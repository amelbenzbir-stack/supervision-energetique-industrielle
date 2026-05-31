#include <LiquidCrystal.h>
// LCD : RS, EN, D4, D5, D6, D7
LiquidCrystal lcd(8, 9, 10, 11, 12, 13);

// Seuil de surcharge (valeur analogique)
#define SEUIL 600

// ── Broche du Ventilateur de Secours ─────────────────────
const int PIN_VENTILATEUR = 3; // Moteur / Fan de secours
const int PIN_ARRET_URGENCE = 2; // Bouton d'urgence sur la broche 5
const unsigned long TEMPS_CRITIQUE = 4000; // 4 secondes avant coupure auto
// LEDs
#define LED_VERT_M1  4
#define LED_ROUGE_M1 5
#define LED_VERT_M2  6
#define LED_ROUGE_M2 7

// ─── Constantes physiques ────────────────────────────────────
#define COS_PHI       0.91         // Facteur de puissance (moteur industriel)
#define TEMP_BASE     35.0         // Température de base (°C)
#define TEMP_CHARGE   2.5          // Augmentation par ampère de courant

// ─── Énergie cumulée (kWh) ───────────────────────────────────
float energie_M1 = 0.0;
float energie_M2 = 0.0;
unsigned long tDernier = 0;

// ─── Compteur secondes pour timestamp ────────────────────────
unsigned long secondes = 0;
unsigned long tTimestamp = 0;
bool systemeBloque = false;      // Variable pour mémoriser l'état d'urgence
unsigned long chronoM1 = 0;      // Chrono de surcharge pour Machine 1
bool coupureAutoM1 = false;      // État de la coupure automatique Machine 1
unsigned long chronoM2 = 0;      // Chrono de surcharge pour Machine 2
bool coupureAutoM2 = false;      // État de la coupure automatique Machine 2

void setup() {
  Serial.begin(9600);

  pinMode(LED_VERT_M1,  OUTPUT);
  pinMode(LED_ROUGE_M1, OUTPUT);
  pinMode(LED_VERT_M2,  OUTPUT);
  pinMode(LED_ROUGE_M2, OUTPUT);
  pinMode(PIN_VENTILATEUR, OUTPUT);
  pinMode(PIN_ARRET_URGENCE, INPUT_PULLUP);
  
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(" Surveillance  ");
  lcd.setCursor(0, 1);
  lcd.print(" Industrielle  ");
  delay(2000);
  lcd.clear();
  // Initialisation sécurisée : Ventilateur éteint au démarrage
  digitalWrite(PIN_VENTILATEUR, LOW);
  tDernier   = millis();
  tTimestamp = millis();
}

// ════════════════════════════════════════════════════════════
// Génère un timestamp simulé : "2025-05-24T14:32:01"
String getTimestamp() {
  secondes = millis() / 1000;
  unsigned long h  = (secondes / 3600) % 24;
  unsigned long m  = (secondes / 60)   % 60;
  unsigned long s  =  secondes          % 60;

  char buf[22];
  sprintf(buf, "2025-05-26T%02lu:%02lu:%02lu", h, m, s);
  return String(buf);
}

// ────────────────────────────────────────────────────────────
// Détermine l'état machine selon courant et surcharge
String determinerEtat(float courant, bool surcharge, bool coupure_auto) {
  if (coupure_auto)   return "DISJONCTE"; // 🔴 Priorité absolue : affichera Disjoncté en texte
  if (courant < 0.1)  return "OFF";
  if (surcharge)      return "SURCHARGE";
  return "ON";
}

// ────────────────────────────────────────────────────────────
// Calcule la température estimée selon la charge
float calculerTemp(float courant, bool surcharge) {
  float temp = TEMP_BASE + (courant * TEMP_CHARGE);
  if (surcharge) temp += 20.0;  // surchauffe en surcharge
  return temp;
}

// ────────────────────────────────────────────────────────────
// Envoie le JSON complet pour une machine sur Serial
void envoyerJSON(
    String machine_id,
    float  tension,
    float  courant,
    float  puissance,
    float  energie,
    bool   surcharge,
    float  temp,
    bool   coupure_auto,  
    bool   ventilo_actif)
{
  float puissReactive = puissance * tan(acos(COS_PHI));  // Q = P × tan(φ)
  String etat         = determinerEtat(courant, surcharge, coupure_auto);
  String ts           = getTimestamp();

  Serial.print("{");
  Serial.print("\"machine_id\":\"");           Serial.print(machine_id);         Serial.print("\",");
  Serial.print("\"timestamp\":\"");            Serial.print(ts);                 Serial.print("\",");
  Serial.print("\"tension_V\":");              Serial.print(tension, 1);         Serial.print(",");
  Serial.print("\"courant_A\":");              Serial.print(courant, 2);         Serial.print(",");
  Serial.print("\"puissance_W\":");            Serial.print(puissance, 1);       Serial.print(",");
  Serial.print("\"puissance_reactive_VAR\":"); Serial.print(puissReactive, 1);   Serial.print(",");
  Serial.print("\"cos_phi\":");               Serial.print(COS_PHI, 2);         Serial.print(",");
  Serial.print("\"energie_kWh\":");            Serial.print(energie, 4);         Serial.print(",");
  Serial.print("\"temperature_C\":");          Serial.print(temp, 1);            Serial.print(",");
  Serial.print("\"etat_machine\":\"");         Serial.print(etat);               Serial.print("\",");
  Serial.print("\"coupure_automatique\":");    Serial.print(coupure_auto ? "true" : "false"); Serial.print(",");
  Serial.print("\"ventilateur_secours\":");    Serial.print(ventilo_actif ? "true" : "false");
  Serial.println("}"); 
}

// ════════════════════════════════════════════════════════════
void loop() {

  /*// ── Debug RAW (à supprimer après calibration) ─────────────
  Serial.print("RAW A0="); Serial.print(analogRead(A0));
  Serial.print(" A1=");    Serial.print(analogRead(A1));
  Serial.print(" A2=");    Serial.print(analogRead(A2));
  Serial.print(" A3=");    Serial.println(analogRead(A3));
  delay(200);*/
  if (digitalRead(PIN_ARRET_URGENCE) == LOW) {
    systemeBloque = true;
  }
  // Si le système est bloqué par l'urgence
  if (systemeBloque) {
    // 1. On coupe TOUTES les sorties physiques (sécurité)
    digitalWrite(LED_VERT_M1, LOW);
    digitalWrite(LED_ROUGE_M1, LOW);
    digitalWrite(LED_VERT_M2, LOW);
    digitalWrite(LED_ROUGE_M2, LOW);
    digitalWrite(PIN_VENTILATEUR, LOW);

    // 2. On affiche le message d'alerte critique sur l'écran LCD
    lcd.setCursor(0, 0);
    lcd.print("    DANGER     ");
    lcd.setCursor(0, 1);
    lcd.print(" ARRET URGENCE! ");

    // 3. 🆕 On envoie l'état ARRET_URGENCE avec des valeurs à 0 pour CHAQUE machine
    // Envoi pour la Machine 1
    Serial.print("{");
    Serial.print("\"machine_id\":\"M1_CNC\",");
    Serial.print("\"timestamp\":\"" + getTimestamp() + "\",");
    Serial.print("\"tension_V\":0.0,");
    Serial.print("\"courant_A\":0.0,");
    Serial.print("\"puissance_W\":0.0,");
    Serial.print("\"puissance_reactive_VAR\":0.0,");
    Serial.print("\"cos_phi\":0.91,");
    Serial.print("\"energie_kWh\":" + String(energie_M1, 4) + ",");
    Serial.print("\"temperature_C\":35.0,");
    Serial.print("\"etat_machine\":\"ARRET_URGENCE\",");
    Serial.print("\"coupure_automatique\":false,");
    Serial.print("\"ventilateur_secours\":false");
    Serial.println("}");

    // Envoi pour la Machine 2
    Serial.print("{");
    Serial.print("\"machine_id\":\"M2_MOTOR\",");
    Serial.print("\"timestamp\":\"" + getTimestamp() + "\",");
    Serial.print("\"tension_V\":0.0,");
    Serial.print("\"courant_A\":0.0,");
    Serial.print("\"puissance_W\":0.0,");
    Serial.print("\"puissance_reactive_VAR\":0.0,");
    Serial.print("\"cos_phi\":0.91,");
    Serial.print("\"energie_kWh\":" + String(energie_M2, 4) + ",");
    Serial.print("\"temperature_C\":35.0,");
    Serial.print("\"etat_machine\":\"ARRET_URGENCE\",");
    Serial.print("\"coupure_automatique\":false,");
    Serial.print("\"ventilateur_secours\":false");
    Serial.println("}");

    delay(1000); // Pause d'une seconde entre chaque envoi de boucle
    return;     // On recommence la boucle loop() sans lire les capteurs
  }
  // ── Échantillonnage RMS ───────────────────────────────────
  unsigned long debut = millis();
  long somme_I1 = 0, somme_V1 = 0;
  long somme_I2 = 0, somme_V2 = 0;
  long nb = 0;

  while (millis() - debut < 20) {
    long raw_I1 = analogRead(A0);
    long raw_V1 = analogRead(A3);
    long raw_I2 = analogRead(A2);
    long raw_V2 = analogRead(A1);

    somme_I1 += (raw_I1 * raw_I1);
    somme_V1 += (raw_V1 * raw_V1);
    somme_I2 += (raw_I2 * raw_I2);
    somme_V2 += (raw_V2 * raw_V2);
    nb++;
  }

  // ── Calcul RMS brut ──────────────────────────────────────
  float rms_I1 = sqrt((float)somme_I1 / nb);
  float rms_V1 = sqrt((float)somme_V1 / nb);
  float rms_I2 = sqrt((float)somme_I2 / nb);
  float rms_V2 = sqrt((float)somme_V2 / nb);

  // ── Conversion en valeurs physiques ─────────────────────
  float courant1  = rms_I1 * (5.0 / 1023.0) * 2.5;
  float tension1  = rms_V1 * (5.0 / 1023.0) * 145.0;
  float courant2  = rms_I2 * (5.0 / 1023.0) * 2.5;
  float tension2  = rms_V2 * (5.0 / 1023.0) * 145.0;

  float puissance1 = courant1 * tension1 * COS_PHI;
  float puissance2 = courant2 * tension2 * COS_PHI;

  // ── Calcul énergie cumulée (kWh) ─────────────────────────
  float dt_h = (millis() - tDernier) / 3600000.0;
  tDernier   = millis();
  energie_M1 += (puissance1 / 1000.0) * dt_h;
  energie_M2 += (puissance2 / 1000.0) * dt_h;

  // ── Détection surcharge ───────────────────────────────────
  bool surcharge1 = (rms_I1 > SEUIL);
  bool surcharge2 = (rms_I2 > SEUIL);

  // ── Température simulée ───────────────────────────────────
  float temp1 = calculerTemp(courant1, surcharge1);
  float temp2 = calculerTemp(courant2, surcharge2);
// LOGIQUE DE COUPURE AUTOMATIQUE TEMPORISÉE ─────────
  // --- Machine 1 ---
  if (surcharge1 && !coupureAutoM1) {
    if (chronoM1 == 0) {
      chronoM1 = millis(); // On lance le chronomètre dès que la surcharge commence
    }
    // Si la surcharge dure depuis plus de 3 secondes
    if (millis() - chronoM1 >= TEMPS_CRITIQUE) {
      coupureAutoM1 = true; // Déclenchement de la coupure automatique
    }
  } else if (!surcharge1) {
    chronoM1 = 0; // On réinitialise le chrono si le courant redescend
  }
  // --- Machine 2 ---
  if (surcharge2 && !coupureAutoM2) {
    if (chronoM2 == 0) {
      chronoM2 = millis(); 
    }
    if (millis() - chronoM2 >= TEMPS_CRITIQUE) {
      coupureAutoM2 = true; 
    }
  } else if (!surcharge2) {
    chronoM2 = 0; 
  }
// 🆕 SÉCURITÉ : FORCE LES VALEURS À ZÉRO SUR COUPURE AUTOMATIQUE
  if (coupureAutoM1) {
    courant1 = 0.0;
    tension1 = 0.0;
    puissance1 = 0.0;
  }
  if (coupureAutoM2) {
    courant2 = 0.0;
    tension2 = 0.0;
    puissance2 = 0.0;
  }
// GESTION DES LEDS ET SORTIES PHYSIQUES ──────────────
  // Machine 1
  if (coupureAutoM1) {
    digitalWrite(LED_VERT_M1, LOW);  // Disjoncté : Plus de jus (éteint)
    digitalWrite(LED_ROUGE_M1, HIGH); // Alerte critique fixe
  } else {
    digitalWrite(LED_VERT_M1, (courant1 >= 0.1) ? HIGH : LOW);
    digitalWrite(LED_ROUGE_M1, surcharge1 ? HIGH : LOW);
  }
  // Machine 2
  if (coupureAutoM2) {
    digitalWrite(LED_VERT_M2, LOW);  
    digitalWrite(LED_ROUGE_M2, HIGH); 
  } else {
    digitalWrite(LED_VERT_M2, (courant2 >= 0.1) ? HIGH : LOW);
    digitalWrite(LED_ROUGE_M2, surcharge2 ? HIGH : LOW);
  }
  // Gestion du Ventilateur de Secours
  bool ventiloM1 = (surcharge1 || coupureAutoM1);
  bool ventiloM2 = (surcharge2 || coupureAutoM2);
  if (ventiloM1 || ventiloM2) {
    digitalWrite(PIN_VENTILATEUR, HIGH); 
  } else {
    digitalWrite(PIN_VENTILATEUR, LOW);
  }
// ── Affichage LCD ─────────────────────────────────────────
  // Ligne 1 : Machine 1
  lcd.setCursor(0, 0);
  if (coupureAutoM1) {
    lcd.print("M1: !DISJONCTE! ");
  } else if (surcharge1) {
    lcd.print("M1 SURCHARGE!!! ");
  } else {
    lcd.print("M1 I:"); lcd.print(courant1, 1); lcd.print("A V:"); lcd.print((int)tension1); lcd.print("V ");
  }

  // Ligne 2 : Machine 2
  lcd.setCursor(0, 1);
  if (coupureAutoM2) {
    lcd.print("M2: !DISJONCTE! ");
  } else if (surcharge2) {
    lcd.print("M2 SURCHARGE!!! ");
  } else {
    lcd.print("M2 I:"); lcd.print(courant2, 1); lcd.print("A V:"); lcd.print((int)tension2); lcd.print("V ");
  }


  // ── Envoi JSON → Python (étudiant 3) via Serial ──────────
  envoyerJSON("M1_CNC",   tension1, courant1, puissance1, energie_M1, surcharge1, temp1, coupureAutoM1, ventiloM1);
  envoyerJSON("M2_MOTOR", tension2, courant2, puissance2, energie_M2, surcharge2, temp2, coupureAutoM2, ventiloM2);

  delay(1000);
}
