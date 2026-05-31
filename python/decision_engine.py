from datetime import datetime

class MoteurDecision:

    RECOMMANDATIONS = {
        "SURCHARGE": "Réduire le courant absorbé ou arrêter la machine pour protéger l'installation.",
        "SURCONSOMMATION": "Réduire la puissance appelée ou décaler l'utilisation de la machine.",
        "SURCHAUFFE": "Vérifier le système de refroidissement.",
        "SOUS_TENSION": "Vérifier l'alimentation électrique et la stabilité du réseau.",
        "SURTENSION": "Isoler la charge si nécessaire et contrôler la source de tension.",
        "FACTEUR_PUISSANCE_FAIBLE": "Améliorer la compensation réactive ou vérifier le facteur de puissance.",
        "VEILLE_ANORMALE": "Éteindre la machine — elle consomme inutilement.",
        "PIC_DYNAMIQUE": "Vérifier si la charge a changé ou décaler l'usage.",
        "ANOMALIE_IF": "Inspection recommandée — comportement inhabituel.",
        "ARRET_URGENCE": "Intervention physique requise — vérifier la machine immédiatement.",
        "COUPURE_AUTO": "Machine coupée automatiquement — vérifier avant redémarrage.",
        "VENTILATEUR_SECOURS": "Surchauffe critique — laisser refroidir avant toute action.",
    }

    def generer_recommandation(self, alerte):
        type_alerte = alerte.get("type", "")
        reco = self.RECOMMANDATIONS.get(type_alerte, "Vérifier la machine.")
        return {
            "machine":         alerte.get("machine"),
            "niveau":          alerte.get("niveau"),
            "type":            type_alerte,
            "alerte":          alerte.get("message"),
            "recommandation":  reco,
            "timestamp":       alerte.get("timestamp", datetime.now().isoformat())
        }

    def calculer_kpi_global(self, historiques):
        total_P = 0
        machines_actives = 0
        details = {}

        for mid, mesures in historiques.items():
            if not mesures:
                continue
            derniere = mesures[-1]
            P = derniere["puissance_W"]
            total_P += P
            if derniere["etat_machine"] == "ON":
                machines_actives += 1
            details[mid] = {
                "puissance_W":   P,
                "courant_A":     derniere.get("courant_A", 0),
                "temperature_C": derniere.get("temperature_C", 0),
                "etat":          derniere["etat_machine"],
                "timestamp":     derniere["timestamp"]
            }

        return {
            "puissance_totale_kW": round(total_P / 1000, 2),
            "machines_actives":    machines_actives,
            "total_machines":      len(historiques),
            "details_machines":    details,
            "timestamp":           datetime.now().isoformat()
        }