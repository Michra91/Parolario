# app.py
"""
Parolario v8 — Wordle in famiglia con bottom navigation bar
e layout mobile moderno.
"""

import streamlit as st
import random
import hmac
import hashlib
from datetime import date, datetime
from streamlit_autorefresh import st_autorefresh
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

from parole import PAROLE_SOLUZIONE, PAROLE_VALIDE

# =========================================================
# CONFIGURAZIONE PAGINA
# =========================================================
APP_NAME = "Parolario"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🟩",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================
# COSTANTI
# =========================================================
WORD_LEN = 5
MAX_TRIES = 6
REFRESH_MS = 30_000
PAGINE_CON_REFRESH = {"classifica", "menu", "statistiche"}
CACHE_TTL = 60

# =========================================================
# CSS PERSONALIZZATO
# =========================================================
st.markdown("""
<style>
    /* ============================================
       CONTAINER PRINCIPALE
       ============================================ */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 5.5rem !important;  /* spazio per bottom nav */
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 420px !important;
        margin: auto !important;
    }
    header[data-testid="stHeader"] { display: none !important; }
    .stApp {
        background: linear-gradient(180deg, #121213 0%, #1a1a1c 100%);
        min-height: 100vh;
    }
    div[data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    .element-container { margin-bottom: 0 !important; }
    div[data-testid="column"] { padding: 0 !important; }

    /* ============================================
       LOGO PAROLARIO CENTRATO
       ============================================ */
    .wordle-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 12px 0 8px 0;
        margin-bottom: 0.4rem;
    }
    .wordle-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 2px;
        text-align: center;
        margin: 0;
        background: linear-gradient(135deg, #c9b458 0%, #6aaa64 50%, #c9b458 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 2px 8px rgba(201,180,88,0.3));
        animation: title-glow 4s ease-in-out infinite;
    }
    @keyframes title-glow {
        0%, 100% { filter: drop-shadow(0 2px 8px rgba(201,180,88,0.3)); }
        50%      { filter: drop-shadow(0 2px 16px rgba(106,170,100,0.5)); }
    }
    .wordle-subtitle {
        font-size: 0.7rem;
        color: #a0a0a0;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 4px;
        text-align: center;
    }

    /* ============================================
       GRIGLIA
       ============================================ */
    .grid-wrapper {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        margin: 0.3rem auto; width: 100%;
    }
    .grid-row {
        display: flex; gap: 4px;
        justify-content: center; margin-bottom: 4px;
    }
    .grid-cell {
        width: 48px; height: 48px;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px; font-weight: 800;
        border: 2px solid #3a3a3c; border-radius: 6px;
        text-transform: uppercase; color: #ffffff;
        background: #1a1a1b; transition: all 0.15s ease;
        line-height: 1;
    }
    .grid-cell.filled  { border-color: #6a6a6c; background: #232324; }
    .grid-cell.correct {
        background: linear-gradient(135deg, #6aaa64, #4d8a48);
        border-color: #6aaa64;
        box-shadow: 0 2px 6px rgba(106,170,100,0.4);
    }
    .grid-cell.present {
        background: linear-gradient(135deg, #c9b458, #a89540);
        border-color: #c9b458;
        box-shadow: 0 2px 6px rgba(201,180,88,0.4);
    }
    .grid-cell.absent {
        background: #3a3a3c; border-color: #3a3a3c; color: #b0b0b0;
    }
    .grid-cell.hint {
        border-color: #c9b458; background: #2a2a1b;
        animation: pulse-hint 1s infinite;
    }
    @keyframes pulse-hint {
        0%, 100% { box-shadow: 0 0 0 0 rgba(201,180,88,0.4); }
        50%      { box-shadow: 0 0 0 6px rgba(201,180,88,0); }
    }

    /* Pallini tentativi */
    .attempts-bar {
        display: flex; justify-content: center;
        align-items: center; gap: 6px;
        margin: 0.15rem 0; padding: 3px 0;
    }
    .attempt-dot {
        width: 8px; height: 8px;
        border-radius: 50%; background: #3a3a3c;
        transition: all 0.3s ease;
    }
    .attempt-dot.used { background: #6aaa64; box-shadow: 0 0 6px rgba(106,170,100,0.6); }
    .attempt-dot.current {
        background: #c9b458; box-shadow: 0 0 6px rgba(201,180,88,0.6);
        animation: dot-pulse 1.5s infinite;
    }
    .attempt-dot.lost { background: #e74c3c; }
    @keyframes dot-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.25); }
    }

    /* ============================================
       INPUT + INVIA
       ============================================ */
    .stTextInput input {
        font-size: 1.15rem !important; font-weight: 700 !important;
        padding: 0.45rem 0.6rem !important; text-transform: uppercase;
        text-align: center; letter-spacing: 3px;
        background: #1a1a1b !important; color: #fff !important;
        border: 2px solid #3a3a3c !important;
        border-radius: 10px !important; height: 46px !important;
        line-height: 1 !important; transition: all 0.2s ease !important;
    }
    .stTextInput input::placeholder {
        color: #666 !important; text-transform: none;
        letter-spacing: normal; font-weight: 400; font-size: 0.85rem;
    }
    .stTextInput input:focus {
        border-color: #6aaa64 !important;
        box-shadow: 0 0 0 3px rgba(106,170,100,0.25) !important;
        background: #222224 !important;
    }
    .btn-invia > button {
        background: #6aaa64 !important;
        border: none !important; color: #ffffff !important;
        min-height: 46px !important; height: 46px !important;
        font-size: 0.82rem !important; border-radius: 10px !important;
        font-weight: 800 !important; letter-spacing: 0.5px;
        padding: 0 0.4rem !important;
        box-shadow: 0 3px 10px rgba(106,170,100,0.35) !important;
        transition: all 0.15s ease !important;
    }
    .btn-invia > button:hover {
        background: #7abb74 !important;
        box-shadow: 0 5px 14px rgba(106,170,100,0.5) !important;
    }
    .btn-invia > button:active { transform: translateY(1px) scale(0.98); }

    /* Pulsanti generici */
    .stButton > button {
        width: 100%; font-weight: 700 !important;
        background: #1a1a1b !important; color: #ffffff !important;
        border: 1px solid #3a3a3c !important;
        border-radius: 10px !important; transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background: #2a2a2c !important;
        border-color: #6aaa64 !important;
    }
    .stButton > button:active { transform: translateY(0); }

    .mode-btn > button {
        min-height: 52px !important; font-size: 0.98rem !important;
        border-radius: 12px !important;
    }

    /* ============================================
       BOTTOM NAVIGATION BAR
       ============================================ */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        z-index: 9999;
        background: rgba(18, 18, 19, 0.85);
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border-top: 1px solid rgba(58, 58, 60, 0.6);
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
        padding: 6px 0 8px 0;
    }
    /* Layout interno della nav */
    .bottom-nav .nav-grid {
        display: flex;
        justify-content: space-around;
        align-items: center;
        max-width: 480px;
        margin: 0 auto;
        padding: 0 8px;
    }
    .bottom-nav .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 2px;
        padding: 4px 8px;
        color: #a0a0a0;
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        transition: all 0.2s ease;
        text-decoration: none;
    }
    .bottom-nav .nav-item.active {
        color: #6aaa64;
    }
    .bottom-nav .nav-icon {
        font-size: 1.35rem;
        line-height: 1;
    }
    .bottom-nav .nav-label {
        font-size: 0.6rem;
        opacity: 0.9;
    }

    /* Streamlit button nella bottom nav - stile trasparente */
    .bottom-nav-buttons .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #a0a0a0 !important;
        min-height: 48px !important;
        height: 48px !important;
        padding: 0.2rem 0.3rem !important;
        font-size: 0.68rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.3px;
    }
    .bottom-nav-buttons .stButton > button:hover {
        background: rgba(106, 170, 100, 0.12) !important;
        color: #6aaa64 !important;
        border: none !important;
    }
    .bottom-nav-buttons .stButton > button:active {
        background: rgba(106, 170, 100, 0.2) !important;
    }

    /* ============================================
       ALTRI
       ============================================ */
    .stAlert {
        background: #1a1a1b !important; border-radius: 10px !important;
        padding: 0.5rem 0.8rem !important; font-size: 0.82rem !important;
        border-left: 4px solid #6aaa64 !important;
    }
    .leader-card {
        background: linear-gradient(135deg, #1a1a1b, #202022);
        border-radius: 10px; padding: 10px 14px; margin-bottom: 6px;
        border-left: 4px solid #6aaa64;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    }
    .leader-card.me {
        border-left-color: #c9b458;
        background: linear-gradient(135deg, #232324, #2a2a25);
    }
    .leader-name { font-size: 1rem; font-weight: 700; color: #ffffff; }
    .leader-stats { font-size: 0.78rem; color: #b0b0b0; margin-top: 2px; }

    .stat-item { text-align: center; }
    .stat-value {
        font-size: 1.5rem; font-weight: 800;
        background: linear-gradient(135deg, #6aaa64, #c9b458);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stat-label {
        font-size: 0.6rem; color: #a0a0a0;
        text-transform: uppercase; letter-spacing: 0.4px;
    }

    /* Avatar */
    .user-avatar {
        width: 44px; height: 44px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px;
        background: linear-gradient(135deg, #2a2a2c, #1a1a1b);
        border: 2px solid #3a3a3c; flex-shrink: 0;
    }
    .user-avatar.admin {
        background: linear-gradient(135deg, #4a3a1b, #2a2a1b);
        border-color: #c9b458;
        box-shadow: 0 0 12px rgba(201,180,88,0.3);
    }
    .user-info { flex: 1; min-width: 0; }
    .user-name {
        font-size: 1rem; font-weight: 700; color: #ffffff;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .user-role {
        font-size: 0.72rem; color: #a0a0a0;
        text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px;
    }
    .user-role.admin { color: #c9b458; font-weight: 700; }
    .sidebar-player {
        display: flex; align-items: center; gap: 12px;
        background: linear-gradient(135deg, #1a1a1b, #232324);
        border: 1px solid #3a3a3c; border-radius: 12px;
        padding: 12px; margin-bottom: 1rem;
    }
    .sidebar-player .user-avatar {
        width: 42px; height: 42px; font-size: 22px;
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important; background: transparent !important;
        border-bottom: 2px solid #2a2a2c !important; padding: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px !important; background: transparent !important;
        border-radius: 0 !important; padding: 0 14px !important;
        color: #888 !important; font-weight: 700 !important;
        font-size: 0.9rem !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #c9b458 !important; }
    .stTabs [aria-selected="true"] {
        color: #6aaa64 !important;
        border-bottom: 3px solid #6aaa64 !important;
        background: rgba(106,170,100,0.08) !important;
    }

    /* Palloncini */
    .balloons-container {
        position: fixed; bottom: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none; z-index: 9998; overflow: hidden;
    }
    .balloon {
        position: absolute; bottom: -150px;
        width: 50px; height: 65px;
        border-radius: 50% 50% 50% 50% / 55% 55% 45% 45%;
        opacity: 0;
        animation-name: balloon-rise;
        animation-timing-function: cubic-bezier(0.4, 0, 0.6, 1);
        animation-iteration-count: 1; animation-fill-mode: forwards;
    }
    .balloon::after {
        content: ""; position: absolute; bottom: -6px; left: 50%;
        transform: translateX(-50%); width: 0; height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 8px solid currentColor; opacity: 0.85;
    }
    .balloon::before {
        content: ""; position: absolute; bottom: -30px; left: 50%;
        width: 1px; height: 30px;
        background: rgba(255,255,255,0.35);
        transform: translateX(-50%);
    }
    .balloon .shine {
        position: absolute; top: 12%; left: 22%;
        width: 30%; height: 22%;
        background: rgba(255,255,255,0.5);
        border-radius: 50%; filter: blur(3px);
    }
    @keyframes balloon-rise {
        0% { transform: translateY(0) translateX(0) rotate(0deg); opacity: 0; }
        8% { opacity: 1; }
        25% { transform: translateY(-25vh) translateX(15px) rotate(-4deg); }
        50% { transform: translateY(-50vh) translateX(-15px) rotate(4deg); }
        75% { transform: translateY(-75vh) translateX(15px) rotate(-3deg); opacity: 1; }
        100% { transform: translateY(-110vh) translateX(-10px) rotate(3deg); opacity: 0; }
    }

    footer {visibility: hidden;}

    /* ============================================
       MOBILE COMPATTO
       ============================================ */
    @media (max-width: 380px) {
        .grid-cell { width: 44px; height: 44px; font-size: 22px; }
        .grid-row { gap: 3px; margin-bottom: 3px; }
        .wordle-title { font-size: 1.7rem; }
        .stTextInput input { height: 44px !important; letter-spacing: 2px; }
        .btn-invia > button { min-height: 44px !important; height: 44px !important; }
        .bottom-nav .nav-icon { font-size: 1.2rem; }
        .bottom-nav .nav-label { font-size: 0.55rem; }
    }
    @media (max-height: 720px) {
        .grid-cell { width: 44px; height: 44px; font-size: 22px; }
        .grid-row { margin-bottom: 3px; }
        .wordle-title { font-size: 1.7rem; }
        .stTextInput input { height: 44px !important; }
        .btn-invia > button { min-height: 44px !important; height: 44px !important; }
    }
    @media (max-height: 600px) {
        .grid-cell { width: 40px; height: 40px; font-size: 20px; }
        .grid-row { gap: 3px; margin-bottom: 2px; }
        .wordle-header { padding: 6px 0 4px 0; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONNESSIONE GOOGLE SHEETS
# =========================================================
@st.cache_resource(ttl=600)
def get_gsheet_connection():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(creds)
        sheet_id = st.secrets["spreadsheet_id"]
        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"❌ Errore connessione Google Sheets: {e}")
        return None

def get_worksheet(nome: str):
    sh = get_gsheet_connection()
    if sh is None:
        return None
    try:
        return sh.worksheet(nome)
    except gspread.exceptions.WorksheetNotFound:
        return None

# =========================================================
# LETTURA CON CACHE
# =========================================================
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def leggi_utenti() -> pd.DataFrame:
    ws = get_worksheet("Utenti")
    if ws is None:
        return pd.DataFrame(columns=["Username", "PIN_Hash", "Ruolo", "Data_Creazione"])
    try:
        dati = ws.get_all_records()
    except Exception:
        return pd.DataFrame(columns=["Username", "PIN_Hash", "Ruolo", "Data_Creazione"])
    if not dati:
        return pd.DataFrame(columns=["Username", "PIN_Hash", "Ruolo", "Data_Creazione"])
    return pd.DataFrame(dati)

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def leggi_partite() -> pd.DataFrame:
    ws = get_worksheet("Partite")
    if ws is None:
        return pd.DataFrame(columns=["Data", "Username", "Modalità", "Tentativi_Usati", "Vinta", "Punti_Ottenuti"])
    try:
        dati = ws.get_all_records()
    except Exception:
        return pd.DataFrame(columns=["Data", "Username", "Modalità", "Tentativi_Usati", "Vinta", "Punti_Ottenuti"])
    if not dati:
        return pd.DataFrame(columns=["Data", "Username", "Modalità", "Tentativi_Usati", "Vinta", "Punti_Ottenuti"])
    return pd.DataFrame(dati)

def invalida_cache():
    leggi_utenti.clear()
    leggi_partite.clear()

# =========================================================
# SCRITTURA
# =========================================================
def hash_pin(pin: str) -> str:
    return hashlib.sha256(str(pin).strip().encode("utf-8")).hexdigest()

def verifica_pin(pin: str, pin_hash: str) -> bool:
    hash_calcolato = hash_pin(pin)
    pin_hash = str(pin_hash).strip()
    return hmac.compare_digest(
        hash_calcolato.encode("utf-8"),
        pin_hash.encode("utf-8")
    )

def registra_utente(username: str, pin: str, ruolo: str = "User") -> bool:
    ws = get_worksheet("Utenti")
    if ws is None:
        return False
    try:
        ws.append_row([
            username,
            hash_pin(pin),
            ruolo,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])
        invalida_cache()
        return True
    except Exception as e:
        st.error(f"Errore registrazione: {e}")
        return False

def registra_partita(username: str, modalita: str, tentativi: int, vinta: bool, punti: int):
    ws = get_worksheet("Partite")
    if ws is None:
        return
    try:
        ws.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username,
            "Giorno",
            tentativi,
            "Sì" if vinta else "No",
            punti,
        ])
        invalida_cache()
    except Exception as e:
        st.error(f"Errore registrazione partita: {e}")

# =========================================================
# QUERY DERIVATE
# =========================================================
def ha_giocato_oggi(username: str):
    df = leggi_partite()
    if df.empty:
        return None
    oggi = date.today().strftime("%Y-%m-%d")
    df_oggi = df[
        (df["Username"] == username) &
        (df["Modalità"] == "Giorno") &
        (df["Data"].astype(str).str.startswith(oggi, na=False))
    ]
    if df_oggi.empty:
        return None
    riga = df_oggi.iloc[0]
    return {
        "tentativi": int(riga["Tentativi_Usati"]),
        "vinta": riga["Vinta"] == "Sì",
        "punti": int(riga["Punti_Ottenuti"]),
    }

def calcola_classifica() -> pd.DataFrame:
    df = leggi_partite()
    if df.empty:
        return pd.DataFrame(columns=["Username", "Punti", "Vittorie", "Partite", "Streak"])
    df = df[df["Modalità"] == "Giorno"]
    if df.empty:
        return pd.DataFrame(columns=["Username", "Punti", "Vittorie", "Partite", "Streak"])
    agg = df.groupby("Username").agg(
        Punti=("Punti_Ottenuti", "sum"),
        Partite=("Vinta", "count"),
    ).reset_index()
    vittorie = df[df["Vinta"] == "Sì"].groupby("Username").size().reset_index(name="Vittorie")
    agg = agg.merge(vittorie, on="Username", how="left").fillna({"Vittorie": 0})
    agg["Vittorie"] = agg["Vittorie"].astype(int)
    streak_map = {}
    for utente in agg["Username"]:
        partite_u = df[df["Username"] == utente].sort_values("Data", ascending=False)
        streak = 0
        for _, riga in partite_u.iterrows():
            if riga["Vinta"] == "Sì":
                streak += 1
            else:
                break
        streak_map[utente] = streak
    agg["Streak"] = agg["Username"].map(streak_map)
    return agg.sort_values("Punti", ascending=False).reset_index(drop=True)

# =========================================================
# ADMIN - BATCH UPDATE
# =========================================================
def admin_reset_punti(username: str) -> bool:
    try:
        sh = get_gsheet_connection()
        if sh is None:
            return False
        ws = sh.worksheet("Partite")
        tutti = ws.get_all_values()
        if len(tutti) < 2:
            return True
        header = tutti[0]
        righe_rimaste = [header] + [r for r in tutti[1:] if len(r) > 1 and r[1] != username]
        ws.clear()
        if len(righe_rimaste) == 1:
            ws.update(values=righe_rimaste, range_name="A1")
        else:
            ws.update(values=righe_rimaste, range_name=f"A1:F{len(righe_rimaste)}")
        invalida_cache()
        return True
    except Exception as e:
        st.error(f"Errore reset: {e}")
        return False

def admin_elimina_utente(username: str) -> bool:
    try:
        sh = get_gsheet_connection()
        if sh is None:
            return False
        ws = sh.worksheet("Utenti")
        tutti = ws.get_all_values()
        if len(tutti) < 2:
            return True
        header = tutti[0]
        righe_rimaste = [header] + [r for r in tutti[1:] if len(r) > 0 and r[0] != username]
        ws.clear()
        if len(righe_rimaste) == 1:
            ws.update(values=righe_rimaste, range_name="A1")
        else:
            ws.update(values=righe_rimaste, range_name=f"A1:D{len(righe_rimaste)}")
        invalida_cache()
        return True
    except Exception as e:
        st.error(f"Errore eliminazione: {e}")
        return False

# =========================================================
# AVATAR E RUOLI
# =========================================================
def get_avatar(username: str, ruolo: str = "User") -> str:
    if ruolo == "Admin":
        return "👑"
    nome_lower = str(username).lower()
    if "mamma" in nome_lower or "mam" in nome_lower:
        return "👩"
    if "pap" in nome_lower or "papa" in nome_lower or "babbo" in nome_lower:
        return "👨"
    if "nonna" in nome_lower:
        return "👵"
    if "nonno" in nome_lower:
        return "👴"
    if "zio" in nome_lower:
        return "🧔"
    if "zia" in nome_lower:
        return "👩‍🦰"
    if "sorella" in nome_lower or "fra" in nome_lower:
        return "👧"
    if "fratello" in nome_lower:
        return "👦"
    if "ospite" in nome_lower or "guest" in nome_lower:
        return "🎭"
    return "👤"

def get_ruolo_label(ruolo: str) -> str:
    return {"Admin": "Amministratore", "User": "Giocatore", "Guest": "Ospite"}.get(ruolo, "Giocatore")

# =========================================================
# LOGICA DI GIOCO
# =========================================================
def parola_del_giorno():
    random.seed(date.today().isoformat())
    return random.choice(PAROLE_SOLUZIONE)

def parola_casuale():
    return random.choice(PAROLE_SOLUZIONE)

def calcola_feedback(tentativo: str, soluzione: str):
    tentativo, soluzione = tentativo.upper(), soluzione.upper()
    risultato = ["absent"] * WORD_LEN
    sol_lettere = list(soluzione)
    for i in range(WORD_LEN):
        if tentativo[i] == soluzione[i]:
            risultato[i] = "correct"
            sol_lettere[i] = None
    for i in range(WORD_LEN):
        if risultato[i] == "correct":
            continue
        if tentativo[i] in sol_lettere:
            risultato[i] = "present"
            sol_lettere[sol_lettere.index(tentativo[i])] = None
    return risultato

def calcola_punti(numero_tentativo: int) -> int:
    return max(0, MAX_TRIES + 1 - numero_tentativo)

def get_suggerimento():
    soluzione = st.session_state.soluzione.upper()
    posizioni_indovinate = set()
    for parola, fb in st.session_state.tentativi:
        for i, colore in enumerate(fb):
            if colore == "correct":
                posizioni_indovinate.add(i)
    posizioni_nascoste = [i for i in range(WORD_LEN) if i not in posizioni_indovinate]
    if not posizioni_nascoste:
        return None
    pos = random.choice(posizioni_nascoste)
    return pos, soluzione[pos]

def reset_partita(mod: str):
    st.session_state.modalita = mod
    st.session_state.soluzione = parola_del_giorno() if mod == "daily" else parola_casuale()
    st.session_state.tentativi = []
    st.session_state.corrente = ""
    st.session_state.finita = False
    st.session_state.vinto = False
    st.session_state.punteggio_assegnato = False
    st.session_state.suggerimento_usato = False
    st.session_state.suggerimento_pos = None
    st.session_state.mostra_definizione = False
    st.session_state.input_version += 1

def invia_tentativo(parola_input: str = None):
    parola = (parola_input or "").upper().strip()
    st.session_state.input_version += 1
    if len(parola) != WORD_LEN:
        st.toast("La parola deve avere 5 lettere!", icon="⚠️")
        return
    if parola not in PAROLE_VALIDE:
        st.toast(f"'{parola}' non è nel dizionario", icon="🚫")
        return
    fb = calcola_feedback(parola, st.session_state.soluzione)
    st.session_state.tentativi.append((parola, fb))
    if parola == st.session_state.soluzione:
        st.session_state.finita = True
        st.session_state.vinto = True
    elif len(st.session_state.tentativi) >= MAX_TRIES:
        st.session_state.finita = True
        st.session_state.vinto = False

def usa_suggerimento():
    if st.session_state.suggerimento_usato:
        st.toast("Hai già usato il suggerimento per questa partita!", icon="ℹ️")
        return
    res = get_suggerimento()
    if res is None:
        st.toast("Hai già indovinato tutte le lettere!", icon="ℹ️")
        return
    pos, lettera = res
    st.session_state.suggerimento_pos = pos
    st.session_state.suggerimento_usato = True
    st.toast(f"💡 Posizione {pos+1}: **{lettera}**", icon="💡")

def torna_al_menu():
    st.session_state.pagina = "menu"
    for k in ["modalita", "soluzione", "tentativi", "corrente",
              "finita", "vinto", "punteggio_assegnato",
              "suggerimento_usato", "suggerimento_pos", "mostra_definizione"]:
        st.session_state.pop(k, None)
    st.rerun()

def vai_a(pagina: str):
    """Naviga a una pagina specifica."""
    st.session_state.pagina = pagina
    st.rerun()

# =========================================================
# RENDER COMPONENTI
# =========================================================
def render_header():
    """Header con logo PAROLARIO centrato e gradient."""
    st.markdown("""
        <div class="wordle-header">
            <div class="wordle-title">PAROLARIO</div>
            <div class="wordle-subtitle">Indovina la parola di 5 lettere</div>
        </div>
    """, unsafe_allow_html=True)

def render_bottom_nav():
    """Bottom navigation bar fissa con 4 icone."""
    # Determina la pagina attiva
    pagina = st.session_state.get("pagina", "menu")
    if pagina == "gioco":
        # Durante il gioco, consideriamo "Home" come attiva
        pagina_attiva = "menu"
    else:
        pagina_attiva = pagina

    # Contenitore fisso
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    st.markdown('<div class="bottom-nav-buttons">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4, gap="small")

    with col1:
        if st.button("🏠\nHome", use_container_width=True, key="nav_home"):
            if pagina == "gioco":
                torna_al_menu()
            else:
                vai_a("menu")
    with col2:
        if st.button("🏆\nClassifica", use_container_width=True, key="nav_classifica"):
            vai_a("classifica")
    with col3:
        # Suggerimento: attivo solo se in gioco e non usato
        if pagina == "gioco" and not st.session_state.get("finita", False):
            if st.button("💡\nSuggerisci", use_container_width=True, key="nav_hint"):
                usa_suggerimento()
                st.rerun()
        else:
            if st.button("💡\nExtra", use_container_width=True, key="nav_extra"):
                vai_a("statistiche")
    with col4:
        if st.button("⚙️\nImpost.", use_container_width=True, key="nav_impost"):
            vai_a("impostazioni")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_griglia():
    sugg_pos = st.session_state.get("suggerimento_pos")
    key_dinamica = f"input_parola_{st.session_state.get('input_version', 0)}"
    corrente = st.session_state.get(key_dinamica, "").upper()

    n_tentativi = len(st.session_state.tentativi)
    finita = st.session_state.get("finita", False)
    vinto = st.session_state.get("vinto", False)

    pallini_html = '<div class="attempts-bar">'
    for i in range(MAX_TRIES):
        if i < n_tentativi:
            classe = "used" if vinto else ("lost" if finita else "used")
        elif i == n_tentativi and not finita:
            classe = "current"
        else:
            classe = ""
        pallini_html += f'<div class="attempt-dot {classe}"></div>'
    pallini_html += '</div>'
    st.markdown(pallini_html, unsafe_allow_html=True)

    righe_html = ['<div class="grid-wrapper">']
    for r in range(MAX_TRIES):
        celle = []
        if r < len(st.session_state.tentativi):
            parola, fb = st.session_state.tentativi[r]
            for lettera, colore in zip(parola, fb):
                celle.append(f'<div class="grid-cell {colore}">{lettera}</div>')
        elif r == len(st.session_state.tentativi) and not finita:
            for i in range(WORD_LEN):
                if i < len(corrente):
                    classe = "filled"
                    if sugg_pos is not None and i == sugg_pos:
                        classe = "hint"
                    celle.append(f'<div class="grid-cell {classe}">{corrente[i]}</div>')
                elif sugg_pos is not None and i == sugg_pos:
                    lettera_hint = st.session_state.soluzione[i].upper()
                    celle.append(f'<div class="grid-cell hint">{lettera_hint}</div>')
                else:
                    celle.append('<div class="grid-cell"></div>')
        else:
            for _ in range(WORD_LEN):
                celle.append('<div class="grid-cell"></div>')
        righe_html.append(f'<div class="grid-row">{"".join(celle)}</div>')
    righe_html.append('</div>')
    st.markdown("".join(righe_html), unsafe_allow_html=True)

def genera_risultato_condivisione():
    emoji_map = {"correct": "🟩", "present": "🟨", "absent": "⬜"}
    righe = []
    for parola, fb in st.session_state.tentativi:
        righe.append("".join(emoji_map[c] for c in fb))
    n = len(st.session_state.tentativi)
    return f"Parolario {n}/{MAX_TRIES}\n" + "\n".join(righe)

def render_classifica():
    df = calcola_classifica()
    if df.empty:
        st.info("Nessuna partita registrata ancora. Gioca la **Parola del Giorno** per entrare in classifica!")
        return
    for pos, (_, riga) in enumerate(df.iterrows(), start=1):
        medaglia = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"{pos}.")
        io = " me" if riga["Username"] == st.session_state.get("utente") else ""
        st.markdown(f"""
        <div class="leader-card{io}">
            <div class="leader-name">{medaglia} {riga['Username']}</div>
            <div class="leader-stats">
                🏆 <b>{riga['Punti']}</b> pt · ✅ {riga['Vittorie']}/{riga['Partite']} · 🔥 {riga['Streak']}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_palloncini():
    colori = ["#6aaa64", "#c9b458", "#e74c3c", "#3498db", "#f39c12",
              "#9b59b6", "#1abc9c", "#e91e63", "#ff5722"]
    palloncini = []
    for _ in range(18):
        colore = random.choice(colori)
        left = random.randint(5, 90)
        delay = round(random.uniform(0, 2.0), 2)
        durata = round(random.uniform(5.0, 6.5), 2)
        width = random.randint(38, 58)
        height = int(width * 1.3)
        palloncini.append(
            f'<div class="balloon" style="left:{left}%; width:{width}px; height:{height}px; '
            f'color:{colore}; background:radial-gradient(circle at 35% 30%, {colore}, {colore}dd 60%, {colore}aa); '
            f'animation-delay:{delay}s; animation-duration:{durata}s;">'
            f'<div class="shine"></div></div>'
        )
    st.markdown('<div class="balloons-container">' + "".join(palloncini) + '</div>',
                unsafe_allow_html=True)

# =========================================================
# LOGIN / REGISTRAZIONE
# =========================================================
def render_login():
    render_header()

    tab_login, tab_register = st.tabs(["🔐  Accedi", "📝  Registrati"])

    with tab_login:
        df_utenti = leggi_utenti()
        if df_utenti.empty:
            st.info("Nessun utente registrato. Vai alla scheda **Registrati** per creare il tuo profilo.")
        else:
            lista_utenti = df_utenti["Username"].tolist()

            utente_scelto = st.selectbox(
                "Chi sta giocando?",
                lista_utenti,
                key="login_user",
                format_func=lambda x: f"{get_avatar(x, df_utenti[df_utenti['Username']==x].iloc[0].get('Ruolo', 'User'))}  {x}"
            )

            pin_inserito = st.text_input(
                "PIN (4 cifre)",
                type="password",
                max_chars=4,
                key="login_pin",
                placeholder="••••"
            )

            if st.button("🔓  ACCEDI", use_container_width=True, key="btn_login"):
                df_utenti = leggi_utenti()
                riga = df_utenti[df_utenti["Username"] == utente_scelto]
                if riga.empty:
                    st.error("Utente non trovato.")
                else:
                    pin_hash = str(riga.iloc[0]["PIN_Hash"]).strip()
                    if verifica_pin(pin_inserito, pin_hash):
                        st.session_state.utente = utente_scelto
                        nome_utente = str(riga.iloc[0]["Username"]).strip()
                        ruolo_foglio = str(riga.iloc[0].get("Ruolo", "User")).strip()
                        if nome_utente.lower() == "admin":
                            st.session_state.ruolo = "Admin"
                        else:
                            st.session_state.ruolo = ruolo_foglio if ruolo_foglio else "User"
                        st.session_state.pagina = "menu"
                        st.rerun()
                    else:
                        st.error("❌ PIN errato")

    with tab_register:
        nuovo_nome = st.text_input("Scegli un nome", max_chars=20, key="reg_name",
                                     placeholder="Es. Mamma, Papà, Nonna…")
        nuovo_pin = st.text_input("Scegli un PIN (4 cifre)", type="password",
                                    max_chars=4, key="reg_pin", placeholder="••••")

        if st.button("✅  CREA PROFILO", use_container_width=True, key="btn_register"):
            if not nuovo_nome.strip() or len(nuovo_pin) != 4 or not nuovo_pin.isdigit():
                st.error("Nome obbligatorio e PIN di 4 cifre numeriche.")
            else:
                df_utenti = leggi_utenti()
                if nuovo_nome.strip() in df_utenti["Username"].values:
                    st.error("Questo nome è già in uso. Scegline un altro.")
                else:
                    if registra_utente(nuovo_nome.strip(), nuovo_pin):
                        st.session_state.utente = nuovo_nome.strip()
                        st.session_state.ruolo = "User"
                        st.session_state.pagina = "menu"
                        st.success(f"Benvenuto {nuovo_nome}!")
                        st.rerun()

    st.markdown('<div style="height:0.6rem;"></div>', unsafe_allow_html=True)
    if st.button("🎭  GIOCA COME OSPITE", use_container_width=True, key="btn_guest"):
        st.session_state.utente = f"Ospite_{random.randint(1000, 9999)}"
        st.session_state.ruolo = "Guest"
        st.session_state.pagina = "menu"
        st.rerun()

# =========================================================
# PAGINE
# =========================================================
def pagina_menu():
    render_header()

    utente = st.session_state.utente
    ruolo = st.session_state.get("ruolo", "User")

    # Barra utente compatta
    avatar = get_avatar(utente, ruolo)
    ruolo_label = get_ruolo_label(ruolo)
    avatar_classe = "admin" if ruolo == "Admin" else ""
    ruolo_classe = "admin" if ruolo == "Admin" else ""
    st.markdown(f"""
        <div class="sidebar-player" style="margin-bottom:0.6rem;">
            <div class="user-avatar {avatar_classe}">{avatar}</div>
            <div class="user-info">
                <div class="user-name">{utente}</div>
                <div class="user-role {ruolo_classe}">{ruolo_label}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Stato parola di oggi
    gia_giocato = None
    if ruolo != "Guest":
        gia_giocato = ha_giocato_oggi(utente)

    if gia_giocato:
        st.info(f"✅ Hai già completato la Parola del Giorno! "
                f"{'Vinto' if gia_giocato['vinta'] else 'Non indovinata'} "
                f"in {gia_giocato['tentativi']} tentativi — {gia_giocato['punti']} punti.")

    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="mode-btn">', unsafe_allow_html=True)
    if st.button("📅  PAROLA DEL GIORNO", use_container_width=True, key="m_daily",
                 disabled=bool(gia_giocato)):
        reset_partita("daily")
        st.session_state.pagina = "gioco"
        st.rerun()
    if st.button("🎲  GIOCA ANCORA  (allenamento)", use_container_width=True, key="m_unlimited"):
        reset_partita("unlimited")
        st.session_state.pagina = "gioco"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.caption("📅 Parola del Giorno → conta in classifica · 🎲 Gioca Ancora → allenamento")

def pagina_gioco():
    render_header()

    mod = st.session_state.modalita
    if mod == "daily":
        info_extra = '<div style="text-align:center;color:#6aaa64;font-size:0.68rem;margin:0.2rem 0;">✦ Conta in classifica ✦</div>'
    else:
        info_extra = '<div style="text-align:center;color:#a0a0a0;font-size:0.68rem;margin:0.2rem 0;">Modalità allenamento</div>'
    st.markdown(info_extra, unsafe_allow_html=True)

    render_griglia()

    # FINE PARTITA
    if st.session_state.finita:
        if st.session_state.vinto:
            n = len(st.session_state.tentativi)
            punti = calcola_punti(n)
            if not st.session_state.punteggio_assegnato:
                if mod == "daily" and st.session_state.get("ruolo") != "Guest":
                    registra_partita(st.session_state.utente, "daily", n, True, punti)
                st.session_state.punteggio_assegnato = True
                render_palloncini()

            if mod == "daily":
                st.success(f"🎉 Bravissimo! In {n} tentativi — **+{punti} punti!**")
            else:
                st.success(f"🎉 Bravo! In {n} tentativi — *allenamento*")

            with st.expander("📋 Condividi risultato"):
                st.code(genera_risultato_condivisione(), language=None)

            c1, c2 = st.columns(2, gap="small")
            with c1:
                if st.button("📋 WhatsApp", use_container_width=True, key="copy_whats"):
                    st.toast("Copiato!", icon="✅")
            with c2:
                if st.button("🔍 Definizione", use_container_width=True, key="def_btn"):
                    p = st.session_state.soluzione
                    st.info(f"**{p}** — [Treccani](https://www.treccani.it/vocabolario/{p.lower()}/) · "
                            f"[Wikizionario](https://it.wiktionary.org/wiki/{p.lower()})")
        else:
            if not st.session_state.punteggio_assegnato:
                if mod == "daily" and st.session_state.get("ruolo") != "Guest":
                    registra_partita(st.session_state.utente, "daily", MAX_TRIES, False, 0)
                st.session_state.punteggio_assegnato = True

            if mod == "daily":
                st.error(f"😢 Peccato! La parola era: **{st.session_state.soluzione}**")
            else:
                st.error(f"😢 Peccato! Era: **{st.session_state.soluzione}** (allenamento)")

        st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("🔄  Nuova", use_container_width=True, key="end_new"):
                reset_partita("unlimited")
                st.rerun()
        with c2:
            if st.button("🏠  Menù", use_container_width=True, key="end_menu"):
                torna_al_menu()
        return

    # INPUT + INVIO
    key_input = f"input_parola_{st.session_state.input_version}"

    col_input, col_invia = st.columns([3, 1], gap="small")
    with col_input:
        testo = st.text_input(
            "Parola",
            value="",
            max_chars=WORD_LEN,
            key=key_input,
            label_visibility="collapsed",
            placeholder="Scrivi la parola…",
            autocomplete="off",
        )
    with col_invia:
        st.markdown('<div class="btn-invia">', unsafe_allow_html=True)
        if st.button("INVIA ↵", use_container_width=True, key="btn_invia"):
            invia_tentativo(testo)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Suggerimento (visibile solo se non usato)
    if not st.session_state.suggerimento_usato:
        st.markdown(
            '<div style="text-align:center;color:#c9b458;font-size:0.7rem;'
            'padding:0.3rem 0;letter-spacing:0.5px;">💡 Usa il tasto "Suggerisci" nel menu in basso</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="text-align:center;color:#c9b458;font-size:0.7rem;'
            'padding:0.3rem 0;letter-spacing:0.5px;">💡 Suggerimento usato</div>',
            unsafe_allow_html=True
        )

def pagina_classifica():
    render_header()
    st.markdown('<div style="text-align:center;color:#fff;font-size:0.95rem;font-weight:700;margin:0.4rem 0;">🏆 Classifica</div>',
                unsafe_allow_html=True)
    render_classifica()
    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)

def pagina_statistiche():
    render_header()
    utente = st.session_state.utente
    st.markdown(f'<div style="text-align:center;color:#fff;font-size:0.95rem;font-weight:700;margin:0.4rem 0;">📊 {utente}</div>',
                unsafe_allow_html=True)

    df = leggi_partite()
    if df.empty:
        st.info("Nessuna partita registrata ancora.")
    else:
        df_u = df[df["Username"] == utente]
        if df_u.empty:
            st.info("Nessuna partita. Gioca la Parola del Giorno!")
        else:
            partite = len(df_u)
            vittorie = len(df_u[df_u["Vinta"] == "Sì"])
            punti = df_u["Punti_Ottenuti"].sum()
            c1, c2, c3 = st.columns(3, gap="small")
            for col, val, label in [
                (c1, partite, "Partite"),
                (c2, f"{round(100*vittorie/partite) if partite else 0}%", "Vittorie"),
                (c3, punti, "Punti"),
            ]:
                with col:
                    st.markdown(f'<div class="stat-item"><div class="stat-value">{val}</div>'
                                f'<div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

            dist = df_u[df_u["Vinta"] == "Sì"]["Tentativi_Usati"].value_counts().sort_index()
            if not dist.empty:
                st.markdown('<div style="color:#fff;font-size:0.85rem;font-weight:700;margin:0.5rem 0 0.2rem 0;">📈 Distribuzione</div>',
                            unsafe_allow_html=True)
                df_chart = pd.DataFrame({"Tentativi": [f"{i}°" for i in dist.index], "Volte": dist.values})
                st.bar_chart(df_chart, x="Tentativi", y="Volte", color="#6aaa64", height=170)

def pagina_impostazioni():
    """Pagina impostazioni con profilo, admin e logout."""
    render_header()

    utente = st.session_state.utente or "—"
    ruolo = st.session_state.get("ruolo", "User")
    avatar = get_avatar(utente, ruolo)
    ruolo_label = get_ruolo_label(ruolo)
    avatar_classe = "admin" if ruolo == "Admin" else ""
    ruolo_classe = "admin" if ruolo == "Admin" else ""

    st.markdown(f'<div style="text-align:center;color:#fff;font-size:0.95rem;font-weight:700;margin:0.4rem 0;">⚙️ Impostazioni</div>',
                unsafe_allow_html=True)

    # Card profilo
    st.markdown(f"""
        <div class="sidebar-player">
            <div class="user-avatar {avatar_classe}">{avatar}</div>
            <div class="user-info">
                <div class="user-name">{utente}</div>
                <div class="user-role {ruolo_classe}">{ruolo_label}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)

    # Pulsante Admin (solo per Admin)
    if ruolo == "Admin":
        if st.button("👑  PANNELLO ADMIN", use_container_width=True, key="set_admin"):
            vai_a("admin")

    # Logout
    if st.button("🚪  LOGOUT", use_container_width=True, key="set_logout"):
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        st.rerun()

def pagina_admin():
    render_header()
    st.markdown('<div style="text-align:center;color:#c9b458;font-size:0.95rem;font-weight:700;margin:0.4rem 0;">👑 PANNELLO ADMIN</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👥 Utenti", "📊 Partite", "📖 Parole"])

    with tab1:
        df = leggi_utenti()
        if not df.empty:
            st.dataframe(df[["Username", "Ruolo", "Data_Creazione"]], use_container_width=True, hide_index=True)
            utente_sel = st.selectbox("Seleziona utente", df["Username"].tolist(), key="admin_user_reset")
            col1, col2 = st.columns(2, gap="small")
            with col1:
                if st.button("🔄 Reset Punti", use_container_width=True, key="admin_reset_punti"):
                    if admin_reset_punti(utente_sel):
                        st.success(f"Punti di {utente_sel} resettati.")
                        st.rerun()
            with col2:
                if st.button("🗑️ Elimina Utente", use_container_width=True, key="admin_del_user"):
                    if admin_elimina_utente(utente_sel):
                        st.success(f"Utente {utente_sel} eliminato.")
                        st.rerun()

    with tab2:
        st.caption("⚠️ Solo partite della Parola del Giorno.")
        df = leggi_partite()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        st.caption(f"Parole soluzione: {len(PAROLE_SOLUZIONE)}")
        st.caption(f"Parole valide: {len(PAROLE_VALIDE)}")
        st.info("Per modificare le parole, aggiorna `parole.py` su GitHub.")

# =========================================================
# ROUTING
# =========================================================
defaults = {
    "utente": None,
    "ruolo": None,
    "pagina": "menu",
    "suggerimento_usato": False,
    "suggerimento_pos": None,
    "input_version": 0,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

if st.session_state.utente and st.session_state.pagina in PAGINE_CON_REFRESH:
    st_autorefresh(interval=REFRESH_MS, key="auto_refresh")

# =========================================================
# RENDERING PAGINE
# =========================================================
if not st.session_state.utente:
    render_login()
elif st.session_state.pagina == "menu":
    pagina_menu()
elif st.session_state.pagina == "gioco":
    pagina_gioco()
elif st.session_state.pagina == "classifica":
    pagina_classifica()
elif st.session_state.pagina == "statistiche":
    pagina_statistiche()
elif st.session_state.pagina == "impostazioni":
    pagina_impostazioni()
elif st.session_state.pagina == "admin" and st.session_state.get("ruolo") == "Admin":
    pagina_admin()
else:
    pagina_menu()

# =========================================================
# BOTTOM NAVIGATION (sempre visibile quando loggato)
# =========================================================
if st.session_state.utente:
    render_bottom_nav()
