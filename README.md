🏭 Système Intelligent de Supervision Énergétique Industrielle



Projet Personnel Professionnel (PPP) 

Année universitaire 2025–2026



📋 Description

Système de supervision énergétique industrielle en temps réel basé sur :



Arduino — Acquisition des grandeurs électriques (courant, tension, puissance)

Proteus — Simulation du circuit électrique

MQTT — Communication publish/subscribe entre les modules

Python — Analyse intelligente et détection d'anomalies (Isolation Forest)

Streamlit — Dashboard de supervision en temps réel



🎯 Fonctionnalités



✅ Mesure en temps réel : courant (A), tension (V), puissance (W), énergie (kWh)

✅ Détection automatique des anomalies (surcharge, surchauffe, panne)

✅ Intelligence artificielle : Isolation Forest + règles expertes

✅ Dashboard interactif avec jauges SVG et graphiques Plotly

✅ Recommandations opérationnelles automatiques

✅ Stockage local SQLite + publication MQTT



🏗️ Architecture

Capteurs → Arduino → MQTT Broker → Python IA → Streamlit Dashboard

📁 Structure du projet

arduino/          # Code embarqué Arduino (.ino)

proteus/          # Simulation électrique Proteus

python/           # Modules d'analyse IA

├── main.py

├── ai\_engine.py

├── data\_processor.py

├── decision\_engine.py

├── database.py

├── mqtt\_receiver.py

├── serial\_bridge.py

└── config.py

dashboard/        # Dashboard Streamlit

└── app.py

⚙️ Installation

Prérequis:

Python 3.10+

Arduino IDE

Proteus 8

Eclipse Mosquitto (broker MQTT)



Installation des dépendances Python:

bash pip install -r python/requirements.txt

Lancer le broker MQTT:

bash mosquitto -v

Lancer l'analyse Python:

bash cd python

python main.py

Lancer le dashboard:

bash cd dashboard

streamlit run app.py



👥 Équipe

Aydi Nour Islem: Simulation Proteus

Ben Zbir Amal: Programmation Arduino 

Masmoudi Mariem: Analyse IA / Python

Ben Alaya Asma: Dashboard Streamlit

📊 Résultats

Scénario:

Démarrage normal✅

Surcharge✅ 

Surchauffe✅ 

Multi-machines✅ 



Taux de détection règles expertes : 100%

Taux de détection Isolation Forest : 94%

Délai bout en bout : \~1,2 secondes

