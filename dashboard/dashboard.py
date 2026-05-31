import streamlit as st
import sqlite3
import pandas as pd
import time
import os
import math
import plotly.graph_objects as go

TARIF_DT_KWH = 0.180  # Tarif industriel STEG (DT/kWh)

# 1. CONFIGURATION DE LA PAGE WEB
st.set_page_config(
    page_title="Supervision Industrielle IoT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&display=swap');

/* ── GLOBAL DARK ── */
.stApp {
    background: #080c12 !important;
    font-family: 'Rajdhani', 'Segoe UI', sans-serif !important;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { background: transparent !important; border: none !important; }
/* Rendre TOUS les boutons du header visibles et en teal */
header button {
    background-color: #00d4aa !important;
    color: #060a10 !important;
    opacity: 1 !important;
    visibility: visible !important;
    border-radius: 0 8px 8px 0 !important;
    min-width: 24px !important;
    min-height: 40px !important;
}
header button svg {
    fill: #060a10 !important;
    visibility: visible !important;
}
[data-testid="stSidebar"] > button {
    visibility: visible !important;
    color: #00d4aa !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #060a10 !important;
    border-right: 1px solid rgba(0,212,170,0.1) !important;
}
[data-testid="stSidebar"] * { color: #2d4a5a !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #00d4aa !important; font-size:0.7rem !important;
    letter-spacing:0.15em !important; text-transform:uppercase !important; }
[data-testid="stSidebar"] strong { color: #64748b !important; }
[data-testid="stSidebar"] hr { border-color: rgba(0,212,170,0.07) !important; }
[data-testid="stSidebar"] label { color: #2d4a5a !important; font-size:0.7rem !important;
    text-transform:uppercase; letter-spacing:0.1em; }

/* ── KPI CARDS ── */
[data-testid="metric-container"] {
    background: #0b1520 !important;
    border-radius: 3px !important;
    padding: 20px 22px 16px !important;
    border: 1px solid rgba(0,212,170,0.08) !important;
    border-left: 3px solid #00d4aa !important;
    box-shadow: 0 0 40px rgba(0,0,0,0.6) !important;
}
[data-testid="stMetricValue"] > div {
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: #7fa8c0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 0.04em;
}
[data-testid="stMetricLabel"] > div {
    font-size: 0.62rem !important;
    font-weight: 600 !important;
    color: #00d4aa !important;
    text-transform: uppercase !important;
    letter-spacing: 0.16em !important;
}
[data-testid="stMetricDelta"] > div { font-size: 0.68rem !important; font-weight: 700 !important; letter-spacing:0.06em; }

/* ── PLOTLY CHARTS ── */
[data-testid="stPlotlyChart"] {
    background: #0b1520 !important;
    border-radius: 3px !important;
    border: 1px solid rgba(0,212,170,0.08) !important;
    box-shadow: 0 0 40px rgba(0,0,0,0.6) !important;
    overflow: hidden;
    padding: 4px;
}

/* ── LINE CHART ── */
[data-testid="stArrowVegaLiteChart"] {
    background: #0b1520 !important;
    border-radius: 3px !important;
    border: 1px solid rgba(0,212,170,0.08) !important;
    box-shadow: 0 0 40px rgba(0,0,0,0.6) !important;
    padding: 16px;
    overflow: hidden;
}

/* ── BUTTON ── */
.stButton > button {
    background: transparent !important;
    color: #00d4aa !important;
    border: 1px solid rgba(0,212,170,0.35) !important;
    border-radius: 3px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important; font-size:0.78rem !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
}
.stButton > button:hover {
    background: rgba(0,212,170,0.08) !important;
    box-shadow: 0 0 16px rgba(0,212,170,0.2) !important;
}

/* ── DIVIDERS ── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 20px 0 !important; }

/* ── SIDEBAR TOGGLE ARROW (Streamlit 1.54) ── */
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    background-color: #00d4aa !important;
    border-radius: 0 8px 8px 0 !important;
    min-width: 24px !important;
    min-height: 56px !important;
    box-shadow: 4px 0 20px rgba(0,212,170,0.5) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {
    background: transparent !important;
    color: #060a10 !important;
    border: none !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="collapsedControl"] svg {
    fill: #060a10 !important;
    width: 16px !important; height: 16px !important;
}
/* Bouton collapse DANS la sidebar (quand ouverte) */
[data-testid="stSidebar"] button[kind="header"],
[data-testid="stSidebar"] [data-testid="baseButton-header"] {
    color: #00d4aa !important;
    background: rgba(0,212,170,0.08) !important;
    border-radius: 4px !important;
}
</style>
""", unsafe_allow_html=True)

def section_header(icon, titre, couleur="#00d4aa"):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin:28px 0 16px 0;">
        <div style="width:3px;height:20px;background:{couleur};border-radius:2px;flex-shrink:0;"></div>
        <span style="font-size:0.72rem;font-weight:700;color:{couleur};letter-spacing:0.18em;
                     text-transform:uppercase;font-family:'Rajdhani',sans-serif;">
            {icon}&nbsp;&nbsp;{titre}</span>
    </div>""", unsafe_allow_html=True)

def gauge_svg(value, vmin, vmax, label, unit, color="#00d4aa", w=280, h=190):
    """Arc gauge SVG — 270° horseshoe, opening at bottom, clockwise fill."""
    pct = max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    cx  = w / 2
    cy  = h * 0.62        # centre du cercle
    r   = h * 0.43        # rayon
    sw  = r * 0.155       # épaisseur de l'arc

    # Arc de 135° (bas-gauche) → sens horaire 270° → 45° (bas-droite)
    # Dans SVG, sens horaire = sweep=1, angles croissants
    START = 135.0   # angle de départ SVG (bas-gauche)
    SPAN  = 270.0   # ouverture totale de la jauge
    SWEEP = 1       # sens horaire

    def pt(deg):
        rad = math.radians(deg % 360)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    sx, sy = pt(START)
    ex, ey = pt(START + SPAN)          # = 405° = 45° (bas-droite)
    val_span = pct * SPAN
    vx, vy   = pt(START + val_span)

    val_large = 1 if val_span > 180 else 0

    # Format de la valeur
    if abs(value) < 0.0001:  val_str = "0.0000"
    elif abs(value) < 1:     val_str = f"{value:.4f}"
    elif abs(value) < 10:    val_str = f"{value:.1f}"
    else:                    val_str = f"{int(round(value))}"
    fsz = 22 if len(val_str) > 7 else 28

    # Position du texte : centre de la jauge
    tx, ty = cx, cy + r * 0.08

    arc_val = "" if pct < 0.005 else (
        f'<path d="M {sx:.1f},{sy:.1f} A {r:.1f},{r:.1f} 0 {val_large} {SWEEP} {vx:.1f},{vy:.1f}"'
        f' fill="none" stroke="{color}" stroke-width="{sw:.1f}" stroke-linecap="round"/>'
        f'<path d="M {sx:.1f},{sy:.1f} A {r:.1f},{r:.1f} 0 {val_large} {SWEEP} {vx:.1f},{vy:.1f}"'
        f' fill="none" stroke="{color}" stroke-width="{sw*2.8:.1f}"'
        f' stroke-linecap="round" opacity="0.07"/>'
    )

    return f"""
<div style="background:#0b1520;border:1px solid rgba(0,212,170,0.09);border-radius:3px;
            padding:10px 4px 8px;text-align:center;box-shadow:0 0 30px rgba(0,0,0,0.5);">
<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;">
  <text x="{cx}" y="16" text-anchor="middle"
        style="fill:#2d4a5a;font-size:8.5px;letter-spacing:3.5px;
               font-family:Rajdhani,sans-serif;text-transform:uppercase;">{label}</text>
  <path d="M {sx:.1f},{sy:.1f} A {r:.1f},{r:.1f} 0 1 {SWEEP} {ex:.1f},{ey:.1f}"
        fill="none" stroke="#0d1e2e" stroke-width="{sw:.1f}" stroke-linecap="round"/>
  {arc_val}
  <text x="{tx:.0f}" y="{ty:.0f}" text-anchor="middle"
        style="fill:#7fa8c0;font-size:{fsz}px;font-weight:500;
               font-family:'Share Tech Mono',monospace;">{val_str}</text>
  <text x="{tx:.0f}" y="{ty+20:.0f}" text-anchor="middle"
        style="fill:#2d4a5a;font-size:9px;letter-spacing:2.5px;
               font-family:Rajdhani,sans-serif;">{unit}</text>
</svg>
</div>"""

# Récupération sécurisée du chemin de la base de données
try:
    from config import DB_PATH
except ImportError:
    DB_PATH = os.path.join("data", "factory.db")

# 2. FONCTIONS DE LECTURE DE LA BASE DE DONNÉES
def charger_mesures(machine_id, limit=30):
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT timestamp, tension_V, courant_A, puissance_W, cos_phi, temperature_C, etat_machine
            FROM measurements
            WHERE machine_id = ?
            ORDER BY id DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(machine_id, limit))
        conn.close()
        # On inverse le dataframe pour l'afficher de gauche à droite (ordre chronologique)
        return df.iloc[::-1].reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur de lecture des mesures : {e}")
        return pd.DataFrame()

def charger_anomalies(machine_id, limit=8):
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT timestamp, type_alerte, niveau, message
            FROM anomalies
            WHERE machine_id = ?
            ORDER BY id DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(machine_id, limit))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erreur de lecture des anomalies : {e}")
        return pd.DataFrame()

def charger_nb_anomalies_depuis(machine_id, depuis_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT COUNT(*) as n FROM anomalies WHERE machine_id=? AND id > ?",
            conn, params=(machine_id, depuis_id)
        )
        conn.close()
        return int(df['n'][0])
    except Exception:
        return 0

def charger_energie_incrementale(machine_id):
    """Calcule l'énergie depuis l'ouverture du dashboard.
    Chargement incrémental : seules les nouvelles lignes (id > last_id) sont lues.
    """
    cle_last_id = f"nrg_last_id_{machine_id}"
    cle_last_ts = f"nrg_last_ts_{machine_id}"
    cle_val     = f"nrg_session_{machine_id}"

    try:
        conn = sqlite3.connect(DB_PATH)

        # Premier appel : mémoriser le curseur de départ, retourner 0
        if cle_last_id not in st.session_state:
            row = pd.read_sql_query(
                "SELECT COALESCE(MAX(id), 0) as max_id, MAX(timestamp) as max_ts "
                "FROM measurements WHERE machine_id=?",
                conn, params=(machine_id,)
            )
            conn.close()
            st.session_state[cle_last_id] = int(row['max_id'][0])
            st.session_state[cle_last_ts] = row['max_ts'][0]
            st.session_state[cle_val]     = 0.0
            return 0.0

        # Appels suivants : uniquement les lignes insérées depuis le dernier refresh
        last_id = st.session_state[cle_last_id]
        last_ts = st.session_state[cle_last_ts]

        df = pd.read_sql_query(
            "SELECT id, timestamp, puissance_W FROM measurements "
            "WHERE machine_id=? AND id > ? ORDER BY id ASC",
            conn, params=(machine_id, last_id)
        )
        conn.close()

        if df.empty:
            return st.session_state[cle_val]

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # dt du premier point = écart avec le dernier timestamp connu
        if last_ts is not None:
            premier_dt = (df['timestamp'].iloc[0] - pd.to_datetime(last_ts)).total_seconds()
            premier_dt = float(max(0.0, min(premier_dt, 10.0)))
        else:
            premier_dt = 0.0

        dt = df['timestamp'].diff().dt.total_seconds().clip(lower=0.0, upper=10.0)
        dt.iloc[0] = premier_dt

        nouvelle_energie = float((df['puissance_W'] * dt / 3_600_000).sum())
        energie_session  = round(st.session_state[cle_val] + max(nouvelle_energie, 0.0), 4)

        st.session_state[cle_last_id] = int(df['id'].iloc[-1])
        st.session_state[cle_last_ts] = str(df['timestamp'].iloc[-1])
        st.session_state[cle_val]     = energie_session

        return energie_session

    except Exception:
        return st.session_state.get(cle_val, 0.0)

def charger_recommandations(machine_id, limit=5):
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT timestamp, alerte, recommandation
            FROM recommandations
            WHERE machine_id = ?
            ORDER BY id DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(machine_id, limit))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erreur de lecture des recommandations : {e}")
        return pd.DataFrame()


# 3. INTERFACE GRAPHIQUE (UI)

# Barre latérale de contrôle
st.sidebar.markdown("### ⚙ Configuration")
machine_selectionnee = st.sidebar.selectbox(
    "Machine active",
    ["M1_CNC", "M2_MOTOR"]
)
refresh_rate = st.sidebar.slider("Intervalle (s)", 1, 5, 2)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🏭 Identité du Site")
st.sidebar.markdown("📊 **LIGNE A-01**")
st.sidebar.markdown("🏗️ **USINE TUNIS**")
st.sidebar.markdown(f"⚙️ **{machine_selectionnee}**")
st.sidebar.markdown("👤 **OPÉRATEUR AUTO**")
st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Statut Système")
st.sidebar.markdown('<span style="color:#00d4aa;font-size:0.75rem;font-weight:700;">● CONNEXION ACTIVE</span>', unsafe_allow_html=True)

# Chargement immédiat des données du cycle actuel
df_mesures = charger_mesures(machine_selectionnee)
df_anomalies = charger_anomalies(machine_selectionnee)
df_recos = charger_recommandations(machine_selectionnee)

# Initialisation des compteurs de session
if 'session_start' not in st.session_state:
    st.session_state['session_start'] = time.time()

cle_ano_base = f"ano_base_id_{machine_selectionnee}"
if cle_ano_base not in st.session_state:
    try:
        conn = sqlite3.connect(DB_PATH)
        row = pd.read_sql_query(
            "SELECT COALESCE(MAX(id), 0) as max_id FROM anomalies WHERE machine_id=?",
            conn, params=(machine_selectionnee,)
        )
        conn.close()
        st.session_state[cle_ano_base] = int(row['max_id'][0])
    except Exception:
        st.session_state[cle_ano_base] = 0

# HEADER NEXUS-IQ (après sidebar pour avoir machine_selectionnee)
_heure_now = time.strftime("%H:%M:%S")
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:18px 0 18px;margin-bottom:4px;
            border-bottom:1px solid rgba(0,212,170,0.1);">
    <div style="display:flex;align-items:center;gap:16px;">
        <div style="background:#00d4aa;width:44px;height:44px;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;font-size:1.3rem;
                    box-shadow:0 0 24px rgba(0,212,170,0.5);">⚡</div>
        <div>
            <div style="color:white;font-size:1.45rem;font-weight:700;letter-spacing:0.06em;
                        font-family:'Rajdhani',sans-serif;">
                SUPERVISION<span style="color:#00d4aa;"> INDUSTRIELLE</span>
            </div>
            <div style="color:#2d4a5a;font-size:0.62rem;letter-spacing:0.18em;text-transform:uppercase;
                        margin-top:2px;">
                Surveillance Industrielle &nbsp;·&nbsp; Industry 4.0
            </div>
        </div>
    </div>
    <div style="text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
        <div style="background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.25);
                    border-radius:3px;padding:5px 14px;color:#00d4aa;
                    font-size:0.68rem;font-weight:700;letter-spacing:0.14em;">
            ● TEMPS RÉEL
        </div>
        <div style="color:#2d4a5a;font-size:0.6rem;letter-spacing:0.12em;">
            ⏱ {_heure_now} &nbsp;&nbsp; LIGNE A-01 &nbsp;&nbsp; {machine_selectionnee}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 4. AFFICHAGE DES MESURES ÉLECTRIQUES (KPIs)
if not df_mesures.empty:
    derniere = df_mesures.iloc[-1]
    
    section_header("📊", f"Indicateurs en Direct — {machine_selectionnee}")
    
    # Récupération et nettoyage de l'état
    etat = derniere['etat_machine']
    etat_upper = str(etat).upper().strip()
    est_en_urgence = "URGENCE" in etat_upper or etat_upper == "ARRET_URGENCE"
    
    # Détection de la coupure automatique
    a_disjoncte = "COUPURE" in etat_upper or "DISJONCT" in etat_upper
    if not a_disjoncte and etat_upper == "SURCHARGE" and derniere['puissance_W'] < 5.0:
        a_disjoncte = True
        
    if not a_disjoncte and not df_anomalies.empty:
        derniere_alerte = str(df_anomalies.iloc[0]['type_alerte']).upper()
        if "COUPURE" in list(df_anomalies['type_alerte'].astype(str).str.upper().values)[:2]:
            a_disjoncte = True

    # Création de 4 colonnes pour les tuiles de mesures
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        # Si la machine est coupée ou en urgence, on affiche une chute de tension en rouge
        if est_en_urgence:
            delta_v = "🚨 URGENCE"
            color_v = "inverse" # Rouge (mode alerte)
        elif a_disjoncte:
            delta_v = "⚠️ DISJONCTÉ"
            color_v = "inverse" # Rouge
        else:
            delta_v = "Nominal ✅"
            color_v = "normal"  # Vert (valeur stable)
            
        st.metric(label="⚡ Tension", value=f"{derniere['tension_V']:.1f} V", delta=delta_v, delta_color=color_v)
        
    with kpi2:
        # Si surcharge ou arrêt, on notifie le courant absorbé
        if est_en_urgence or a_disjoncte:
            delta_i = "0.00 A (Coupé)"
            color_i = "off"     # Gris (neutre)
        elif etat_upper == "SURCHARGE":
            delta_i = "🔥 SURCHARGE"
            color_i = "inverse" # Rouge
        else:
            delta_i = "Stable"
            color_i = "normal"  # Vert
            
        st.metric(label="🔌 Courant", value=f"{derniere['courant_A']:.2f} A", delta=delta_i, delta_color=color_i)
        
    with kpi3:
        # Calcul de la puissance
        if est_en_urgence or a_disjoncte:
            delta_p = "Aucune conso"
            color_p = "off"     # Gris
        elif etat_upper == "SURCHARGE":
            delta_p = "⚠️ Surconsommation"
            color_p = "inverse" # Rouge
        else:
            delta_p = "Optimale"
            color_p = "normal"  # Vert
            
        st.metric(label="🔥 Puissance Active", value=f"{derniere['puissance_W']:.1f} W", delta=delta_p, delta_color=color_p)
        
    with kpi4:
        if est_en_urgence:
            st.metric(label="⚙️ Statut", value="🚨 URGENCE STOP")
        elif a_disjoncte:
            st.metric(label="⚙️ Statut", value="🔴 Disjoncté")
        elif etat in ["SURCHARGE", "ERREUR"] or "SURCHARGE" in etat_upper or "ERREUR" in etat_upper:
            st.metric(label="⚙️ Statut", value=f"⚠️ {etat}")
        else:
            st.metric(label="⚙️ Statut", value=f"🟢 {etat}")

    # Deuxième ligne de KPIs — qualité électrique
    cos_phi = float(derniere.get('cos_phi', 1.0) or 1.0)
    cos_phi = max(min(cos_phi, 0.9999), 0.001)
    puissance_W = float(derniere['puissance_W'])
    Q = puissance_W * math.tan(math.acos(cos_phi))
    S = puissance_W / cos_phi

    kpi5, kpi6, kpi7, kpi8 = st.columns(4)

    with kpi5:
        if cos_phi < 0.85:
            delta_fp, color_fp = "⚠️ Faible — pénalité possible", "inverse"
        elif cos_phi >= 0.95:
            delta_fp, color_fp = "Excellent ✅", "normal"
        else:
            delta_fp, color_fp = "Acceptable", "off"
        st.metric(label="📐 Facteur de Puissance", value=f"{cos_phi:.3f}", delta=delta_fp, delta_color=color_fp)

    with kpi6:
        st.metric(label="🔀 Puissance Réactive", value=f"{Q:.0f} VAR")

    with kpi7:
        st.metric(label="🔋 Puissance Apparente", value=f"{S:.0f} VA")

    with kpi8:
        energie_session = st.session_state.get(f"nrg_session_{machine_selectionnee}", 0.0)
        cout_dt = energie_session * TARIF_DT_KWH

        # Projection horaire basée sur la puissance active actuelle
        projection_1h  = (puissance_W / 1000.0) * TARIF_DT_KWH          # DT/h
        projection_8h  = projection_1h * 8                                # DT/shift

        valeur_affichee = f"{cout_dt:.3f} DT"

        st.metric(
            label="💰 Coût Session",
            value=valeur_affichee,
            help=(
                f"Tarif : {TARIF_DT_KWH} DT/kWh (STEG industriel)\n\n"
                f"Projection 1h : {projection_1h:.3f} DT\n\n"
                f"Projection shift (8h) : {projection_8h:.2f} DT"
            )
        )

# 5. JAUGES SVG EN TEMPS RÉEL
    st.markdown("---")
    col_jauge1, col_jauge2, col_jauge3 = st.columns(3)

    with col_jauge1:
        temp_val  = float(derniere['temperature_C'])
        col_temp  = "#ef4444" if temp_val >= 80 else "#f59e0b" if temp_val >= 50 else "#00d4aa"
        st.markdown(gauge_svg(temp_val, 0, 100, "TEMPÉRATURE", "°C", col_temp),
                    unsafe_allow_html=True)

    with col_jauge2:
        max_puissance   = 4000.0 if machine_selectionnee == "M1_CNC" else 2000.0
        seuil_surcharge = (float(derniere['puissance_W']) - 10.0) if "SURCHARGE" in etat_upper \
                          else (1534.0 if machine_selectionnee == "M1_CNC" else 1000.0)
        p_val = float(derniere['puissance_W'])
        pct_p = p_val / max_puissance
        col_p = "#ef4444" if pct_p > 0.75 else "#f59e0b" if pct_p > 0.50 else "#00d4aa"
        st.markdown(gauge_svg(p_val, 0, max_puissance, "PUISSANCE", "W", col_p),
                    unsafe_allow_html=True)

    with col_jauge3:
        valeur_energie = charger_energie_incrementale(machine_selectionnee)
        if valeur_energie < 0.1:   limite_energie = 0.1
        elif valeur_energie < 0.5: limite_energie = 0.5
        elif valeur_energie < 2.0: limite_energie = 2.0
        elif valeur_energie < 5.0: limite_energie = 5.0
        else:                      limite_energie = 10.0
        st.markdown(gauge_svg(valeur_energie, 0, limite_energie, "ÉNERGIE SESSION", "kWh", "#f59e0b"),
                    unsafe_allow_html=True)

    section_header("📈", "Historique de Charge")
    chart_data = df_mesures.copy()
    chart_data['Heure'] = chart_data['timestamp'].apply(
        lambda x: str(x).split('T')[-1] if 'T' in str(x) else (str(x).split(' ')[-1] if ' ' in str(x) else str(x))
    )

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=chart_data['Heure'], y=chart_data['puissance_W'],
        name="PUISSANCE (W)",
        line=dict(color="#00d4aa", width=2),
        fill='tozeroy',
        fillcolor='rgba(0,212,170,0.04)',
        hovertemplate="<b>%{y:.0f} W</b><br>%{x}<extra></extra>"
    ))
    fig_hist.add_trace(go.Scatter(
        x=chart_data['Heure'], y=chart_data['tension_V'],
        name="TENSION (V)",
        line=dict(color="#f59e0b", width=2),
        hovertemplate="<b>%{y:.1f} V</b><br>%{x}<extra></extra>"
    ))
    fig_hist.update_layout(
        height=260,
        paper_bgcolor="#0b1520",
        plot_bgcolor="#0b1520",
        font=dict(family="Rajdhani, sans-serif", color="#2d4a5a", size=10),
        margin=dict(l=45, r=20, t=20, b=45),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0d1e30",
            bordercolor="#00d4aa",
            font=dict(color="#e2e8f0", size=12)
        ),
        legend=dict(
            orientation="h", x=0, y=1.08,
            font=dict(color="#2d4a5a", size=9),
            bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            showgrid=True, gridcolor="rgba(0,212,170,0.05)",
            tickcolor="#1a2e40", linecolor="#0d1e2e",
            tickfont=dict(size=8, color="#1a3040"),
            tickangle=0
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(0,212,170,0.05)",
            tickcolor="#1a2e40", linecolor="#0d1e2e",
            tickfont=dict(size=9, color="#1a3040"),
            zeroline=True, zerolinecolor="rgba(0,212,170,0.1)"
        ),
    )
    st.plotly_chart(fig_hist, use_container_width=True, key=f"hist_{time.time()}")

# 6. STATISTIQUES DE SESSION
    st.markdown("---")
    section_header("📊", "Statistiques de Session", couleur="#7c3aed")

    duree_sec = time.time() - st.session_state['session_start']
    h, rem = divmod(int(duree_sec), 3600)
    m, s   = divmod(rem, 60)
    duree_str = f"{h:02d}:{m:02d}:{s:02d}"

    df_actif = df_mesures[df_mesures['etat_machine'].str.upper().str.strip() != 'OFF']
    pct_actif = len(df_actif) / len(df_mesures) if not df_mesures.empty else 0
    duree_eff = duree_sec * pct_actif
    he, rem_e = divmod(int(duree_eff), 3600)
    me, se    = divmod(rem_e, 60)
    duree_eff_str = f"{he:02d}:{me:02d}:{se:02d}"

    df_p = df_actif['puissance_W'] if not df_actif.empty else pd.Series([0.0])
    p_min = df_p.min()
    p_max = df_p.max()
    p_moy = df_p.mean()

    nb_ano = charger_nb_anomalies_depuis(machine_selectionnee, st.session_state[cle_ano_base])

    s1, s2, s3, s4, s5, s6 = st.columns(6)
    with s1:
        st.metric("⏱️ Durée Session", duree_str)
    with s2:
        st.metric("⚙️ Temps Actif", duree_eff_str)
    with s3:
        st.metric("📉 Puissance Min", f"{p_min:.0f} W")
    with s4:
        st.metric("📈 Puissance Max", f"{p_max:.0f} W")
    with s5:
        st.metric("⚡ Puissance Moy.", f"{p_moy:.0f} W")
    with s6:
        st.metric("🚨 Alertes Session", nb_ano)

    if st.button("🔄 Réinitialiser la session"):
        keys_reset = [k for k in st.session_state
                      if k.startswith(('nrg_', 'ano_base_', 'session_start'))]
        for k in keys_reset:
            del st.session_state[k]
        st.rerun()

# 7. ALERTES ET RECOMMENDATIONS
col_gauche, col_droite = st.columns(2)

with col_gauche:
    section_header("", "FLUX DES ALERTES", couleur="#ef4444")

    if not df_anomalies.empty:
        n_crit = int((df_anomalies['niveau'] >= 2).sum())
        n_warn = int((df_anomalies['niveau'] < 2).sum())
        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-bottom:12px;">
            <span style="background:rgba(239,68,68,0.12);color:#fca5a5;font-size:0.62rem;
                         font-weight:700;padding:3px 12px;border-radius:2px;letter-spacing:0.1em;
                         border:1px solid rgba(239,68,68,0.2);font-family:Rajdhani,sans-serif;">
                ● {n_crit} CRITIQUE{'S' if n_crit>1 else ''}
            </span>
            <span style="background:rgba(245,158,11,0.1);color:#fcd34d;font-size:0.62rem;
                         font-weight:700;padding:3px 12px;border-radius:2px;letter-spacing:0.1em;
                         border:1px solid rgba(245,158,11,0.2);font-family:Rajdhani,sans-serif;">
                ◆ {n_warn} WARNING{'S' if n_warn>1 else ''}
            </span>
        </div>""", unsafe_allow_html=True)

        alertes_html = ""
        for _, row in df_anomalies.iterrows():
            ts    = str(row['timestamp'])
            heure = ts.split('T')[-1][:8] if 'T' in ts else ts.split(' ')[-1][:8]
            crit  = row['niveau'] >= 2
            dot   = "#ef4444" if crit else "#f59e0b"
            lvl   = f"N{int(row['niveau'])}"
            badge_c = "#fca5a5" if crit else "#fcd34d"
            alertes_html += f"""
            <div style="background:#0d1825;border-left:2px solid {dot};border-radius:2px;
                        padding:9px 14px;margin-bottom:5px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:3px;">
                    <span style="color:{dot};font-size:0.58rem;font-weight:800;
                                 letter-spacing:0.12em;font-family:Rajdhani,sans-serif;">● {'CRITIQUE' if crit else 'WARNING'}</span>
                    <span style="color:#1a3040;font-size:0.62rem;font-family:Rajdhani,sans-serif;">{heure}</span>
                    <span style="color:#7fa8c0;font-size:0.78rem;font-weight:700;
                                 font-family:Rajdhani,sans-serif;letter-spacing:0.05em;">{row['type_alerte']}</span>
                    <span style="margin-left:auto;background:rgba(255,255,255,0.04);color:#1a3040;
                                 font-size:0.58rem;padding:1px 6px;border-radius:2px;
                                 font-family:Rajdhani,sans-serif;">{lvl}</span>
                </div>
                <div style="color:#1e3548;font-size:0.72rem;font-family:Rajdhani,sans-serif;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{row['message']}</div>
            </div>"""
        st.markdown(alertes_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#0d1825;border-left:2px solid #00d4aa;border-radius:2px;padding:12px 16px;">
            <span style="color:#00d4aa;font-size:0.72rem;font-weight:700;
                         font-family:Rajdhani,sans-serif;letter-spacing:0.1em;">
                ● NOMINAL — Aucune anomalie détectée</span>
        </div>""", unsafe_allow_html=True)

with col_droite:
    section_header("", "RECOMMANDATIONS IA", couleur="#00d4aa")

    if not df_recos.empty:
        recos_html = ""
        for _, row in df_recos.iterrows():
            ts    = str(row['timestamp'])
            heure = ts.split('T')[-1][:8] if 'T' in ts else ts.split(' ')[-1][:8]
            recos_html += f"""
            <div style="background:#0d1825;border-left:2px solid #00d4aa;border-radius:2px;
                        padding:10px 14px;margin-bottom:6px;">
                <div style="display:flex;align-items:center;justify-content:space-between;
                             margin-bottom:5px;">
                    <span style="color:#00d4aa;font-size:0.58rem;font-weight:700;
                                 letter-spacing:0.15em;font-family:Rajdhani,sans-serif;">
                        ▶ IA ANALYSIS</span>
                    <span style="color:#1a3040;font-size:0.6rem;font-family:Rajdhani,sans-serif;">{heure}</span>
                </div>
                <div style="color:#1e3548;font-size:0.7rem;font-family:Rajdhani,sans-serif;
                            margin-bottom:7px;white-space:nowrap;overflow:hidden;
                            text-overflow:ellipsis;">{row['alerte']}</div>
                <div style="background:#060e18;border:1px solid rgba(0,212,170,0.12);
                            border-radius:2px;padding:8px 12px;
                            color:#7fa8c0;font-size:0.76rem;font-weight:600;
                            font-family:Rajdhani,sans-serif;letter-spacing:0.03em;">
                    🛠 {row['recommandation']}
                </div>
            </div>"""
        st.markdown(recos_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#0d1825;border-left:2px solid #00d4aa;border-radius:2px;padding:12px 16px;">
            <span style="color:#00d4aa;font-size:0.72rem;font-weight:700;
                         font-family:Rajdhani,sans-serif;letter-spacing:0.1em;">
                ● NOMINAL — Aucune contre-mesure requise</span>
        </div>""", unsafe_allow_html=True)

# 7. LOGIQUE DE BOUCLE DU TEMPS RÉEL
time.sleep(refresh_rate)
st.rerun()