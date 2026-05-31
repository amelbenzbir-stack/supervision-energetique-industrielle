import argparse
import json
import logging
import signal
import sys
import time
import threading

from config          import BROKER, PORT, TOPICS_SUBSCRIBE, TOPIC_ALERTES, TOPIC_RECOS, TOPIC_KPI
from ai_engine       import MoteurIA
from decision_engine import MoteurDecision
from data_processor  import DataProcessor
from database        import init_db, inserer_mesure, inserer_anomalie, inserer_recommandation
from mqtt_receiver   import MQTTReceiver
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

# ── Instances globales ────────────────────────────────────────────────
ia        = MoteurIA()
decision  = MoteurDecision()
processor = DataProcessor()
running   = True

# Client MQTT pour publier les résultats
publisher = mqtt.Client(client_id="centrale_ia")
try:
    publisher.connect(BROKER, PORT)
    publisher.loop_start()
except:
    logger.warning("Broker MQTT non disponible — publication désactivée")

compteur = 0

# ==============================================================================
# PIPELINE PRINCIPAL
# ==============================================================================

def traiter_mesure(mesure_brute):
    global compteur

    # 1. Nettoyage et validation des données
    mesure = processor.traiter(mesure_brute)
    if mesure is None:
        return

    # 📊 Affichage console
    logger.info(
        f"📊 [DONNÉES REÇUES] Machine: {mesure.get('machine_id')} | "
        f"Tension: {mesure.get('tension_V')} V | "
        f"Courant: {mesure.get('courant_A')} A | "
        f"Puissance: {mesure.get('puissance_W')} W | "
        f"Température: {mesure.get('temperature_C')} °C | "
        f"État: {mesure.get('etat_machine')}"
    )

    # 🆕 ✅ AJOUT : Envoyer la mesure brute nettoyée sur MQTT pour le Dashboard
    topic_mesure = f"usine/machines/{mesure.get('machine_id')}/mesures"
    try:
        publisher.publish(topic_mesure, json.dumps(mesure))
    except Exception as e:
        logger.debug(f"Impossible de publier la mesure sur MQTT: {e}")

    # 2. Sauvegarde mesure (le reste du code de la fonction reste inchangé...)
    inserer_mesure(mesure)
    # ... suite du code ...

    # 3. Mise à jour historique IA
    ia.ajouter_mesure(mesure)

    # 4. Détections
    toutes_alertes = []
    toutes_alertes += ia.detecter_surcharge(mesure)

    veille = ia.detecter_veille_anormale(mesure)
    if veille: toutes_alertes.append(veille)

    pic = ia.detecter_pic_dynamique(mesure)
    if pic: toutes_alertes.append(pic)

    anomalie = ia.detecter_anomalie_if(mesure)
    if anomalie: toutes_alertes.append(anomalie)

    # 5. Alertes + recommandations
    for alerte in toutes_alertes:
        inserer_anomalie(alerte)
        reco = decision.generer_recommandation(alerte)
        inserer_recommandation(reco)

        try:
            publisher.publish(TOPIC_ALERTES, json.dumps(alerte))
            publisher.publish(TOPIC_RECOS,   json.dumps(reco))
        except:
            pass

        niveau_emoji = {1:"ℹ️", 2:"⚠️", 3:"⛔"}.get(alerte["niveau"], "?")
        logger.warning(f"{niveau_emoji} [{alerte['type']}] {alerte['message']}")

    # 6. KPI toutes les 5 mesures
    compteur += 1
    if compteur % 5 == 0:
        kpi = decision.calculer_kpi_global(ia.historique)
        try:
            publisher.publish(TOPIC_KPI, json.dumps(kpi))
        except:
            pass
        logger.info(
            f"📈 [KPI GLOBAL] {kpi['puissance_totale_kW']} kW | "
            f"{kpi['machines_actives']}/{kpi['total_machines']} actives"
        )

# ==============================================================================
# MODE SÉRIE CORRIGÉ (Proteus via VSPE)
# ==============================================================================

def start_serial_mode():
    import serial
    PORT_SERIE = "COM13"
    BAUD_RATE  = 9600

    try:
        ser = serial.Serial(PORT_SERIE, BAUD_RATE, timeout=1)
        time.sleep(2)  # ✅ Sécurité : Laisse le temps au port virtuel de se stabiliser
        logger.info(f"[SÉRIE] Port ouvert : {PORT_SERIE} @ {BAUD_RATE} baud")
    except Exception as e:
        logger.error(f"Impossible d'ouvrir {PORT_SERIE} : {e}")
        logger.error("Vérifiez que VSPE est actif et Proteus en simulation.")
        sys.exit(1)

    logger.info("En attente de données Proteus...")
    while running:
        try:
            # ✅ Sécurité : On lit uniquement si le tampon contient des octets
            if ser.in_waiting > 0:
                ligne = ser.readline().decode("utf-8", errors="ignore").strip()
                if ligne.startswith("{"):
                    data = json.loads(ligne)
                    traiter_mesure(data)
            
            time.sleep(0.1)  # ✅ Pause pour éviter de saturer le processeur
            
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"Erreur série : {e}")
            time.sleep(1)

# ==============================================================================
# MODE MQTT RÉEL
# ==============================================================================

def start_mqtt_mode():
    def callback(mesure):
        traiter_mesure(mesure)

    receiver = MQTTReceiver(callback_mesure=callback)
    receiver.demarrer()
    logger.info(f"[MQTT] En écoute sur {TOPICS_SUBSCRIBE}")

    while running:
        time.sleep(1)

# ==============================================================================
# MODE DÉMO (simulateur interne)
# ==============================================================================

def start_demo_mode():
    import subprocess
    logger.info("[DÉMO] Lancement du simulateur interne...")
    subprocess.Popen([sys.executable, "data_simulator.py"])
    start_mqtt_mode()

# ==============================================================================
# POINT D'ENTRÉE
# ==============================================================================

def main():
    global running

    parser = argparse.ArgumentParser()
    parser.add_argument("--demo",   action="store_true",
                        help="Simulation interne")
    parser.add_argument("--serial", action="store_true",
                        help="Réception depuis Proteus via VSPE")
    args = parser.parse_args()

    init_db()

    if args.demo:
        mode_label = "DÉMO (simulation interne)"
    elif args.serial:
        mode_label = "SÉRIE (Proteus → VSPE → Python)"
    else:
        mode_label = "MQTT (Mosquitto)"

    logger.info("=" * 55)
    logger.info("   STATION CENTRALE IA — Optimisation Énergétique")
    logger.info(f"   Mode : {mode_label}")
    logger.info("=" * 55)

    def stop(sig, frame):
        global running
        running = False
        logger.info("Arrêt propre.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  stop)
    signal.signal(signal.SIGTERM, stop)

    if args.demo:
        start_demo_mode()
    elif args.serial:
        start_serial_mode()
    else:
        start_mqtt_mode()

if __name__ == "__main__":
    main()