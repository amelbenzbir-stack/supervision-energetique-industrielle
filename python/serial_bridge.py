"""
serial_bridge.py
----------------
Pont entre le port série virtuel (Proteus/Arduino via VSPE)
et le pipeline IA de la station centrale.

Flux :
  Proteus → COM1 ══ VSPE ══ COM2 → serial_bridge.py → traiter_mesure()
"""

import serial
import json
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Configuration port série ──────────────────────────────────────────────────
SERIAL_PORT = "COM13"      # ← port où Python écoute (l'autre bout du câble VSPE)
BAUD_RATE   = 9600        # doit correspondre au COMPIM dans Proteus
TIMEOUT     = 1           # Aligné sur le script fonctionnel

# L'Arduino peut envoyer juste les mesures sans machine_id.
DEFAULT_MACHINE_ID = "M1_CNC"


class SerialBridge:
    """
    Lit les JSON depuis le port série virtuel et les transmet
    au callback de traitement (pipeline IA).
    """

    def __init__(self, callback, port=SERIAL_PORT, baud=BAUD_RATE):
        self.callback   = callback
        self.port       = port
        self.baud       = baud
        self.running    = False
        self.ser        = None
        self._stats     = {"reçus": 0, "valides": 0, "erreurs": 0}

    # ──────────────────────────────────────────────────────────────────────────
    # CONNEXION
    # ──────────────────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Ouvre le port série. Retourne True si succès."""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=TIMEOUT,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            time.sleep(2) # ✅ Pause de sécurité essentielle pour laisser le port s'initialiser
            logger.info(f"✅ Port série ouvert : {self.port} @ {self.baud} baud")
            return True

        except serial.SerialException as e:
            logger.error(f"❌ Impossible d'ouvrir {self.port} : {e}")
            logger.error("   Vérifiez que VSPE est lancé et Proteus en simulation.")
            return False

    def disconnect(self):
        """Ferme proprement le port série."""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info(f"Port {self.port} fermé.")

    # ──────────────────────────────────────────────────────────────────────────
    # BOUCLE DE LECTURE
    # ──────────────────────────────────────────────────────────────────────────

    def start(self):
        """Lance la lecture dans un thread daemon."""
        self.running = True
        t = threading.Thread(target=self._read_loop, daemon=True)
        t.start()
        logger.info(f"Bridge série démarré — lecture sur {self.port}")

    def _read_loop(self):
        """
        Lit ligne par ligne depuis le port série de manière sécurisée.
        """
        while self.running:
            try:
                if not self.ser or not self.ser.is_open:
                    time.sleep(1)
                    continue

                # ✅ On ne lit que si des données sont réellement en attente (comme dans reception_serie.py)
                if self.ser.in_waiting > 0:
                    raw_line = self.ser.readline()

                    if not raw_line:
                        continue

                    self._stats["reçus"] += 1
                    # ✅ Décodage sécurisé (ignore les caractères corrompus)
                    line = raw_line.decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    logger.debug(f"[SÉRIE brut] {line}")
                    self._parse_and_dispatch(line)

                # ✅ Légère pause pour éviter la surconsommation CPU
                time.sleep(0.1)

            except serial.SerialException as e:
                logger.error(f"Erreur lecture série : {e}")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Erreur inattendue : {e}", exc_info=True)
                self._stats["erreurs"] += 1

    # ──────────────────────────────────────────────────────────────────────────
    # PARSING JSON
    # ──────────────────────────────────────────────────────────────────────────

    def _parse_and_dispatch(self, line: str):
        """Tente de parser la ligne comme JSON et l'envoie au pipeline."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.debug(f"Ligne non-JSON ignorée : {line[:60]}")
            self._stats["erreurs"] += 1
            return

        # Normalisation vers le format attendu par le pipeline
        data = self._normaliser(data)

        logger.info(
            f"[SÉRIE] {data['machine_id']} | "
            f"P={data.get('puissance_W','?')}W | "
            f"T={data.get('temperature_C','?')}°C | "
            f"état={data.get('etat_machine','?')}"
        )

        self._stats["valides"] += 1
        self.callback(data["machine_id"], data)

    def _normaliser(self, data: dict) -> dict:
        """Normalise les formats de données."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()

        if "machine_id" not in data:
            data["machine_id"] = DEFAULT_MACHINE_ID

        # Conversion des formats courts de l'Arduino
        if "P" in data and "puissance_W" not in data:
            data["puissance_W"]  = float(data.pop("P", 0))
        if "I" in data and "courant_A" not in data:
            data["courant_A"]    = float(data.pop("I", 0))
        if "V" in data and "tension_V" not in data:
            data["tension_V"]    = float(data.pop("V", 230))
        if "T" in data and "temperature_C" not in data:
            data["temperature_C"] = float(data.pop("T", 25))
        if "etat" in data and "etat_machine" not in data:
            data["etat_machine"] = str(data.pop("etat", "ON")).upper()

        data.setdefault("tension_V",    230.0)
        data.setdefault("courant_A",    data.get("puissance_W", 0) / 230.0)
        data.setdefault("temperature_C", 45.0)
        data.setdefault("etat_machine", "ON")

        return data

    def stats(self) -> dict:
        return self._stats


# ==============================================================================
# LANCEMENT AUTONOME (Test direct)
# ==============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 55)
    print("  TEST serial_bridge.py — lecture port série virtuel")
    print(f"  Port : {SERIAL_PORT} | Baud : {BAUD_RATE}")
    print("=" * 55)

    def on_data(machine_id, data):
        print(f"\n✅ Reçu de {machine_id} :")
        print(f"   Puissance  : {data.get('puissance_W', '?')} W")
        print(f"   Température: {data.get('temperature_C', '?')} °C")
        print(f"   État       : {data.get('etat_machine', '?')}")

    bridge = SerialBridge(callback=on_data, port=SERIAL_PORT, baud=BAUD_RATE)

    if bridge.connect():
        bridge.start()
        print("\nEn attente de données Proteus... (Ctrl+C pour quitter)\n")
        try:
            while True:
                time.sleep(5)
                s = bridge.stats()
                print(f"[Stats] Reçus={s['reçus']} | Valides={s['valides']} | Erreurs={s['erreurs']}")
        except KeyboardInterrupt:
            print("\nArrêt.")
            bridge.disconnect()