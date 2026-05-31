import pandas as pd
from datetime import datetime

class DataProcessor:

    def __init__(self):
        # Stocke les dernières mesures par machine sous forme de DataFrame
        self.buffers = {}   # { machine_id : [dict, dict, ...] }

    def traiter(self, mesure):
        """
        Reçoit une mesure brute (dict JSON),
        la valide, la nettoie et la retourne prête pour l'IA.
        Retourne None si la mesure est invalide.
        """
        # ── 1. Validation des champs obligatoires ──────────────────
        champs_obligatoires = ["machine_id", "timestamp",
                               "puissance_W", "courant_A", "tension_V"]
        for champ in champs_obligatoires:
            if champ not in mesure:
                print(f"[PROCESSOR] Champ manquant : {champ} — mesure ignorée")
                return None

        # ── 2. Nettoyage des valeurs aberrantes ────────────────────
        try:
            mesure["puissance_W"]   = max(0, float(mesure["puissance_W"]))
            mesure["courant_A"]     = max(0, float(mesure["courant_A"]))
            mesure["tension_V"]     = max(0, float(mesure["tension_V"]))
            mesure["cos_phi"]       = float(mesure.get("cos_phi", 0.9))
            mesure["temperature_C"] = float(mesure.get("temperature_C", 50))
            mesure["etat_machine"]  = mesure.get("etat_machine", "INCONNU")
        except (ValueError, TypeError) as e:
            print(f"[PROCESSOR] Valeur invalide : {e} — mesure ignorée")
            return None
        # Nouveaux champs version finale Étudiant 2
        mesure["coupure_automatique"]  = bool(mesure.get("coupure_automatique", False))
        mesure["ventilateur_secours"]  = bool(mesure.get("ventilateur_secours", False))
        # ── 3. Ajout de champs calculés ────────────────────────────
        V = mesure["tension_V"]
        I = mesure["courant_A"]
        mesure["puissance_apparente_VA"] = round(V * I, 1)

        # ── 4. Mise en buffer ──────────────────────────────────────
        mid = mesure["machine_id"]
        if mid not in self.buffers:
            self.buffers[mid] = []
        self.buffers[mid].append(mesure)
        self.buffers[mid] = self.buffers[mid][-500:]  # garder 500 max

        return mesure

    def get_dataframe(self, machine_id):
        """Retourne l'historique d'une machine sous forme de DataFrame pandas."""
        data = self.buffers.get(machine_id, [])
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)

    def get_toutes_machines(self):
        """Retourne la liste des machines connues."""
        return list(self.buffers.keys())

    def get_derniere_mesure(self, machine_id):
        """Retourne la dernière mesure d'une machine."""
        data = self.buffers.get(machine_id, [])
        return data[-1] if data else None

    def resume_global(self):
        """
        Retourne un résumé instantané de toutes les machines :
        puissance totale, nombre actives, etc.
        """
        total_P = 0
        actives = 0
        resume = {}

        for mid, mesures in self.buffers.items():
            if not mesures:
                continue
            derniere = mesures[-1]
            P = derniere["puissance_W"]
            total_P += P
            if derniere["etat_machine"] == "ON":
                actives += 1
            resume[mid] = {
                "puissance_W":   P,
                "courant_A":     derniere["courant_A"],
                "temperature_C": derniere["temperature_C"],
                "etat":          derniere["etat_machine"]
            }

        return {
            "puissance_totale_kW": round(total_P / 1000, 2),
            "machines_actives":    actives,
            "par_machine":         resume,
            "timestamp":           datetime.now().isoformat()
        }