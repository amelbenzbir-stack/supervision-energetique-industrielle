import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
from config import SEUILS, CONTAMINATION, DUREE_SURCONSOMMATION, SIMULATION_CONFIG

class MoteurIA:

    def __init__(self):
        self.historique = {}
        self.modeles_if = {}
        self.scalers = {}

    # ── 1. RÈGLES MÉTIER ────────────────────────────────────────────────────
    def _duree_depassement_puissance(self, machine_id, p_seuil):
        """
        Calcule la durée pendant laquelle la puissance reste au-dessus du seuil.
        La durée est calculée sur les mesures consécutives les plus récentes.
        """
        historique = self.historique.get(machine_id, [])
        mesures_depassement = []

        for mesure in reversed(historique):
            if mesure.get("puissance_W", 0) > p_seuil:
                mesures_depassement.append(mesure)
            else:
                break

        if len(mesures_depassement) < 2:
            return 0

        try:
            t_fin = datetime.fromisoformat(mesures_depassement[0]["timestamp"])
            t_debut = datetime.fromisoformat(mesures_depassement[-1]["timestamp"])
            return (t_fin - t_debut).total_seconds()
        except Exception:
            # Si le timestamp n'est pas exploitable, on estime avec 2 s par mesure.
            return len(mesures_depassement) * SIMULATION_CONFIG.get("interval_seconds", 2)

    def detecter_surcharge(self, mesure):
        mid = mesure["machine_id"]
        seuil = SEUILS.get(mid, {})
        alertes = []

        # Surcharge : courant excessif mettant en danger l'installation.
        if mesure["courant_A"] > seuil.get("I_max", 9999):
            alertes.append({
                "type": "SURCHARGE",
                "niveau": 3,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"SURCHARGE {mid} : I={mesure['courant_A']}A > {seuil['I_max']}A"
            })

        # Surconsommation : puissance supérieure au seuil pendant une durée Δt.
        p_seuil = seuil.get("P_seuil", seuil.get("P_max", 9999))
        duree_depassement = self._duree_depassement_puissance(mid, p_seuil)
        if mesure["puissance_W"] > p_seuil and duree_depassement >= DUREE_SURCONSOMMATION:
            alertes.append({
                "type": "SURCONSOMMATION",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"SURCONSOMMATION {mid} : P={mesure['puissance_W']}W > {p_seuil}W pendant {duree_depassement:.0f}s"
            })

        if mesure.get("temperature_C", 0) > seuil.get("T_max", 9999):
            alertes.append({
                "type": "SURCHAUFFE",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"SURCHAUFFE {mid} : T={mesure['temperature_C']}°C > {seuil['T_max']}°C"
            })

        tension = mesure.get("tension_V", 0)
        if tension < seuil.get("V_min", 0):
            alertes.append({
                "type": "SOUS_TENSION",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"SOUS-TENSION {mid} : V={tension}V < {seuil['V_min']}V"
            })
        elif tension > seuil.get("V_max", 9999):
            alertes.append({
                "type": "SURTENSION",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"SURTENSION {mid} : V={tension}V > {seuil['V_max']}V"
            })

        cos_phi = mesure.get("cos_phi", 1)
        if cos_phi < seuil.get("cos_phi_min", 0):
            alertes.append({
                "type": "FACTEUR_PUISSANCE_FAIBLE",
                "niveau": 1,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"FACTEUR DE PUISSANCE FAIBLE {mid} : cos_phi={cos_phi} < {seuil['cos_phi_min']}"
            })

        if mesure.get("etat_machine") == "ARRET_URGENCE":
            alertes.append({
                "type": "ARRET_URGENCE",
                "niveau": 3,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"ARRÊT D'URGENCE {mid} — intervention requise immédiatement"
            })

        if mesure.get("coupure_automatique") == True:
            alertes.append({
                "type": "COUPURE_AUTO",
                "niveau": 3,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"COUPURE AUTOMATIQUE déclenchée sur {mid}"
            })

        if mesure.get("ventilateur_secours") == True:
            alertes.append({
                "type": "VENTILATEUR_SECOURS",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"Ventilateur de secours activé sur {mid}"
            })
        return alertes

    # ── 2. VEILLE ANORMALE ───────────────────────────────────────────
    def detecter_veille_anormale(self, mesure):
        mid = mesure["machine_id"]
        if mesure["etat_machine"] == "ARRET" and mesure["puissance_W"] > 150:
            return {
                "type": "VEILLE_ANORMALE",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"VEILLE ANORMALE {mid} : arrêtée mais consomme {mesure['puissance_W']}W"
            }
        return None

    # ── 3. SEUILS DYNAMIQUES ─────────────────────────────────────────
    def detecter_pic_dynamique(self, mesure):
        mid = mesure["machine_id"]
        historique = self.historique.get(mid, [])
        if len(historique) < 30:
            return None

        valeurs = [m["puissance_W"] for m in historique[-60:]]
        mu = np.mean(valeurs)
        sigma = np.std(valeurs)
        seuil_haut = mu + 2 * sigma

        if mesure["puissance_W"] > seuil_haut:
            return {
                "type": "PIC_DYNAMIQUE",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "message": f"PIC DYNAMIQUE {mid} : P={mesure['puissance_W']:.0f}W > seuil={seuil_haut:.0f}W"
            }
        return None

    # ── 4. ISOLATION FOREST ──────────────────────────────────────────
    def entrainer_isolation_forest(self, machine_id):
        historique = self.historique.get(machine_id, [])
        if len(historique) < 50:
            return

        df = pd.DataFrame(historique)
        features = ["puissance_W", "courant_A", "tension_V", "temperature_C"]
        X = df[features].dropna()

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = IsolationForest(
            n_estimators=50,
            contamination=CONTAMINATION,
            random_state=42
        )
        model.fit(X_scaled)

        self.modeles_if[machine_id] = model
        self.scalers[machine_id] = scaler

        os.makedirs("data/modeles", exist_ok=True)
        joblib.dump(model, f"data/modeles/if_{machine_id}.pkl")
        print(f"[IA] Isolation Forest entraîné pour {machine_id}")

    def detecter_anomalie_if(self, mesure):
        mid = mesure["machine_id"]
        if mid not in self.modeles_if:
            return None

        features = ["puissance_W", "courant_A", "tension_V", "temperature_C"]
        X = pd.DataFrame([[mesure.get(f, 0) for f in features]], columns=features)
        X_scaled = self.scalers[mid].transform(X)
        pred = self.modeles_if[mid].predict(X_scaled)

        if pred[0] == -1:
            score = self.modeles_if[mid].score_samples(X_scaled)[0]
            return {
                "type": "ANOMALIE_IF",
                "niveau": 2,
                "machine": mid,
                "timestamp": mesure["timestamp"],
                "score": round(float(score), 3),
                "message": f"ANOMALIE IF {mid} : score={score:.3f}"
            }
        return None

    # ── 5. K-MEANS ───────────────────────────────────────────────────
    def identifier_profil(self, machine_id):
        historique = self.historique.get(machine_id, [])
        if len(historique) < 100:
            return "indéterminé"

        df = pd.DataFrame(historique)
        X = df[["puissance_W"]].values

        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(X)
        centres = sorted(kmeans.cluster_centers_.flatten())

        P_actuelle = historique[-1]["puissance_W"]
        if P_actuelle < centres[0] * 1.1:
            return "faible charge"
        elif P_actuelle < centres[1] * 1.1:
            return "charge normale"
        else:
            return "forte charge"

    # ── MISE À JOUR HISTORIQUE ────────────────────────────────────────
    def ajouter_mesure(self, mesure):
        mid = mesure["machine_id"]
        if mid not in self.historique:
            self.historique[mid] = []
        self.historique[mid].append(mesure)
        self.historique[mid] = self.historique[mid][-500:]

        if len(self.historique[mid]) % 50 == 0:
            self.entrainer_isolation_forest(mid)