import json
import paho.mqtt.client as mqtt
from config import BROKER, PORT, TOPICS_SUBSCRIBE

class MQTTReceiver:

    def __init__(self, callback_mesure):
        """
        callback_mesure : fonction appelée à chaque message reçu
        elle recevra directement le dictionnaire JSON de la mesure
        """
        self.callback_mesure = callback_mesure
        self.client = mqtt.Client()
        self.client.on_connect    = self._on_connect
        self.client.on_message    = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] Connecté au broker — abonnement à : {TOPICS_SUBSCRIBE}")
            client.subscribe(TOPICS_SUBSCRIBE)
        else:
            print(f"[MQTT] Échec connexion — code : {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            mesure = json.loads(msg.payload.decode())
            self.callback_mesure(mesure)
        except json.JSONDecodeError as e:
            print(f"[MQTT] Erreur décodage JSON : {e}")

    def _on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] Déconnecté — code : {rc}")

    def demarrer(self):
        self.client.connect(BROKER, PORT)
        self.client.loop_start()   # tourne en arrière-plan (non bloquant)
        print("[MQTT] Receiver démarré.")

    def arreter(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Receiver arrêté.")