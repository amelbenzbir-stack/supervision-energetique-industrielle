# config.py — Paramètres centralisés du système

# ── Compatibilité Arduino / Proteus ───────────────────────────────────────────
# Dans le code Arduino : SEUIL = 600 en valeur RMS analogique.
# Conversion Arduino du courant : courant = rms_I * (5.0 / 1023.0) * 2.5
# Donc I_max compatible Proteus ≈ 600 * 5 / 1023 * 2.5 = 7.33 A.

# ── Seuils énergétiques par machine (W, A, °C) ────────────────────────────────
# Surcharge       : I > I_max
# Surconsommation : P > P_seuil pendant DUREE_SURCONSOMMATION
# Surchauffe      : T > T_max
SEUILS = {
    "M1_CNC": {
        "P_seuil": 1534, "P_max": 1534,
        "I_max": 7.33, "T_max": 80,
        "V_min": 210, "V_max": 250, "cos_phi_min": 0.75
    },
    "M2_MOTOR": {
        "P_seuil": 1534, "P_max": 1534,
        "I_max": 7.33, "T_max": 80,
        "V_min": 210, "V_max": 250, "cos_phi_min": 0.75
    },
    # Alias conservés si d'autres simulateurs ou anciens scripts les utilisent.
    "M2_CNC": {
        "P_seuil": 1534, "P_max": 1534,
        "I_max": 7.33, "T_max": 80,
        "V_min": 210, "V_max": 250, "cos_phi_min": 0.75
    },
    "M3_TOUR": {
        "P_seuil": 3000, "P_max": 3000,
        "I_max": 15, "T_max": 75,
        "V_min": 210, "V_max": 250, "cos_phi_min": 0.75
    },
    "M4_FRAISEUSE": {
        "P_seuil": 3500, "P_max": 3500,
        "I_max": 18, "T_max": 78,
        "V_min": 210, "V_max": 250, "cos_phi_min": 0.75
    },
    "M5_PRESSE": {
        "P_seuil": 5000, "P_max": 5000,
        "I_max": 25, "T_max": 85,
        "V_min": 210, "V_max": 250, "cos_phi_min": 0.75
    },
}

# ── Machines de la flotte ─────────────────────────────────────────────────────
MACHINES = {
    "M1_CNC":   {"P_nom": 1200, "I_nom": 5.5},
    "M2_MOTOR": {"P_nom": 1200, "I_nom": 5.5},
    "M2_CNC":   {"P_nom": 1200, "I_nom": 5.5},
    "M3_TOUR":  {"P_nom": 2200, "I_nom": 10.0},
    "M4_FRAISEUSE": {"P_nom": 2800, "I_nom": 12.5},
    "M5_PRESSE": {"P_nom": 4000, "I_nom": 18.0},
}

# ── Topics MQTT ───────────────────────────────────────────────────────────────
TOPICS_SUBSCRIBE = "usine/machines/+/mesures"
TOPIC_ALERTES    = "usine/centrale/alertes"
TOPIC_RECOS      = "usine/centrale/recommandations"
TOPIC_KPI        = "usine/centrale/kpi"

BROKER = "localhost"
PORT   = 1883

# ── Paramètres IA ─────────────────────────────────────────────────────────────
FENETRE_STATS  = 60      # nombre de mesures utilisées pour les stats dynamiques
CONTAMINATION  = 0.05    # 5% d'anomalies attendues (Isolation Forest)
DUREE_SURCONSOMMATION = 10  # durée minimale en secondes pour confirmer P > P_seuil

# ── Base de données ───────────────────────────────────────────────────────────
DB_PATH = "data/historique.db"

# ── Simulation / série Proteus ────────────────────────────────────────────────
SIMULATION_CONFIG = {
    "interval_seconds": 5,  # delay(5000) dans le code Arduino
    "scenario_actif": "normal",
    "serial_port": "COM13",
    "baud_rate": 9600,
}