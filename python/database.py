import sqlite3
import os
from config import DB_PATH

def init_db():
    # Création du dossier 'data' s'il n'existe pas déjà
    dossier = os.path.dirname(DB_PATH)
    if dossier:
        os.makedirs(dossier, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id  TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL,
                tension_V   REAL,
                courant_A   REAL,
                puissance_W REAL,
                cos_phi     REAL,
                temperature_C REAL,
                etat_machine  TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS anomalies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id  TEXT,
                timestamp   TEXT,
                type_alerte TEXT,
                niveau      INTEGER,
                message     TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recommandations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id  TEXT,
                timestamp   TEXT,
                alerte      TEXT,
                recommandation TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_machine_time ON measurements (machine_id, timestamp)')
        print("[DB] Base initialisée avec succès.")

def inserer_mesure(mesure):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO measurements
            (machine_id, timestamp, tension_V, courant_A, puissance_W, cos_phi, temperature_C, etat_machine)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            mesure.get("machine_id"),
            mesure.get("timestamp"),
            mesure.get("tension_V"),
            mesure.get("courant_A"),
            mesure.get("puissance_W"),
            mesure.get("cos_phi"),
            mesure.get("temperature_C"),
            mesure.get("etat_machine")
        ))

def inserer_anomalie(alerte):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO anomalies (machine_id, timestamp, type_alerte, niveau, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            alerte.get("machine"),
            alerte.get("timestamp", ""),
            alerte.get("type"),
            alerte.get("niveau"),
            alerte.get("message")
        ))

def inserer_recommandation(reco):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO recommandations (machine_id, timestamp, alerte, recommandation)
            VALUES (?, ?, ?, ?)
        ''', (
            reco.get("machine"),
            reco.get("timestamp", ""),
            reco.get("alerte"),
            reco.get("recommandation")
        ))

def lire_dernieres_mesures(machine_id, n=50):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('''
            SELECT * FROM measurements
            WHERE machine_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (machine_id, n))
        return cursor.fetchall()

if __name__ == "__main__":
    init_db()