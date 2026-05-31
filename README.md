# \#### 🏭 Système Intelligent de Supervision Énergétique Industrielle

# 

# > Projet Personnel Professionnel (PPP) — Génie Informatique / Systèmes Embarqués

# > Année universitaire 2024–2025

# 

# \#### 📋 Description

# 

# Système de supervision énergétique industrielle en temps réel basé sur :

# \- \*\*Arduino\*\* — Acquisition des grandeurs électriques (courant, tension, puissance)

# \- \*\*Proteus\*\* — Simulation du circuit électrique

# \- \*\*MQTT\*\* — Communication publish/subscribe entre les modules

# \- \*\*Python\*\* — Analyse intelligente et détection d'anomalies (Isolation Forest)

# \- \*\*Streamlit\*\* — Dashboard de supervision en temps réel

# 

# \#### 🎯 Fonctionnalités

# 

# \- ✅ Mesure en temps réel : courant (A), tension (V), puissance (W), énergie (kWh)

# \- ✅ Détection automatique des anomalies (surcharge, surchauffe, panne)

# \- ✅ Intelligence artificielle : Isolation Forest + règles expertes

# \- ✅ Dashboard interactif avec jauges SVG et graphiques Plotly

# \- ✅ Recommandations opérationnelles automatiques

# \- ✅ Stockage local SQLite + publication MQTT

# 

# \#### 🏗️ Architecture

# 

# Capteurs → Arduino → MQTT Broker → Python IA → Streamlit Dashboard

# 

# \#### 📁 Structure du projet

# 

# arduino/          # Code embarqué Arduino (.ino)

# proteus/          # Simulation électrique Proteus

# python/           # Modules d'analyse IA

# &#x20; ├── main.py

# &#x20; ├── ai\_engine.py

# &#x20; ├── data\_processor.py

# &#x20; ├── decision\_engine.py

# &#x20; ├── database.py

# &#x20; ├── mqtt\_receiver.py

# &#x20; ├── serial\_bridge.py

# &#x20; └── config.py

# dashboard/        # Dashboard Streamlit

# &#x20; └── app.py

# 

# \#### ⚙️ Installation

# 

# \#### Prérequis

# \- Python 3.10+

# \- Arduino IDE

# \- Proteus 8

# \- Eclipse Mosquitto (broker MQTT)

# 

# \#### Installation des dépendances Python

# 

# pip install -r python/requirements.txt

# 

# \#### Lancer le broker MQTT

# 

# mosquitto -v

# 

# \#### Lancer l'analyse Python

# 

# cd python

# python main.py

# 

# \#### Lancer le dashboard

# 

# cd dashboard

# streamlit run app.py

# 

# \#### 👥 Équipe

# 

# | Membre | Rôle |

# |--------|------|

# | Aydi Nour Islem | Simulation Proteus |

# | Ben Zbir Amal | Programmation Arduino |

# | Masmoudi Mariem | Analyse IA / Python |

# | Ben Alaya Asma | Dashboard Streamlit |

# 

# \#### 📊 Résultats

# 

# | Scénario | Statut |

# |----------|--------|

# | Démarrage normal | ✅ Conforme |

# | Surcharge | ✅ Conforme |

# | Surchauffe | ✅ Conforme |

# | Multi-machines | ✅ Conforme |

# 

# \- Taux de détection règles expertes : 100%

# \- Taux de détection Isolation Forest : 94%

# \- Délai bout en bout : \~1,2 secondes

