# app.py
"""
Parolario v4 — Wordle in famiglia con autenticazione PIN, Admin panel,
persistenza su Google Sheets e restyling UI/UX completo.
"""

import streamlit as st
import random
import json
import os
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

# =========================================================
# CSS PERSONALIZZATO
# =========================================================
st.markdown("""
<style>
    /* ============================================
       CONTAINER
       ============================================ */
    .main .block-container {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
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
    div[data-testid="stVerticalBlock"] > div { gap: 0.15rem !important; }
    .element-container { margin-bottom: 0 !important; }
    div[data-testid="column"] { padding: 0 !important; }

    /* ============================================
       HEADER CON TESSERE WORDLE
       ============================================ */
    .wordle-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 8px 0 4px 0;
        margin-bottom: 0.3rem;
    }
    .wordle-tiles {
        display: flex;
        gap: 6px;
        margin-bottom: 6px;
    }
    .wordle-tile {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        font-weight: 800;
        border-radius: 6px;
        color: #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        animation: tile-bounce 2s ease-in-out infinite;
    }
    .wordle-tile:nth-child(1) { animation-delay: 0s; }
    .wordle-tile:nth-child(2) { animation-delay: 0.3s; }
    .wordle-tile:nth-child(3) { animation-delay: 0.6s; }
    .wordle-tile:nth-child(4) { animation-delay: 0.9s; }
    .wordle-tile:nth-child(5) { animation-delay: 1.2s; }
    @keyframes tile-bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }
    .tile-green  { background: linear-gradient(135deg, #6aaa64, #4d8a48); }
    .tile-yellow { background: linear-gradient(135deg, #c9b458, #a89540); }
    .tile-gray   { background: linear-gradient(135deg, #565758, #3a3a3c); }

    .wordle-title {
        font-size: 1.6rem;
        font-weight: 900;
        letter-spacing: 4px;
        color: #ffffff;
        text-shadow: 0 0 20px rgba(106,170,100,0.4);
        margin: 0;
        text-align: center;
    }
    .wordle-subtitle {
        font-size: 0.7rem;
        color: #a0a0a0;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 2px;
    }

    /* ============================================
       GRIGLIA DI GIOCO
       ============================================ */
    .grid-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0.3rem auto;
        width: 100%;
    }
    .grid-row {
        display: flex;
        gap: 5px;
        justify-content: center;
        margin-bottom: 5px;
    }
    .grid-cell {
        width: 56px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 800;
        border: 2px solid #3a3a3c;
        border-radius: 8px;
        text-transform: uppercase;
        color: #ffffff;
        background: #1a1a1b;
        transition: all 0.15s ease;
        line-height: 1;
        box-shadow: inset 0 1px 2px rgba(255,255,255,0.03);
    }
    .grid-cell.filled  { border-color: #6a6a6c; background: #232324; }
    .grid-cell.correct {
        background: linear-gradient(135deg, #6aaa64, #4d8a48);
        border-color: #6aaa64;
        box-shadow: 0 2px 8px rgba(106,170,100,0.4);
    }
    .grid-cell.present {
        background: linear-gradient(135deg, #c9b458, #a89540);
        border-color: #c9b458;
        box-shadow: 0 2px 8px rgba(201,180,88,0.4);
    }
    .grid-cell.absent {
        background: #3a3a3c;
        border-color: #3a3a3c;
        color: #b0b0b0;
    }
    .grid-cell.hint {
        border-color: #c9b458;
        background: #2a2a1b;
        animation: pulse-hint 1s infinite;
    }
    @keyframes pulse-hint {
        0%, 100% { box-shadow: 0 0 0 0 rgba(201,180,88,0.4); }
        50%      { box-shadow: 0 0 0 8px rgba(201,180,88,0); }
    }

    /* ============================================
       INDICATORE TENTATIVI
       ============================================ */
    .attempts-bar {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        margin: 0.4rem 0;
        padding: 8px 0;
    }
    .attempt-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #3a3a3c;
        transition: all 0.3s ease;
    }
    .attempt-dot.used {
        background: #6aaa64;
        box-shadow: 0 0 8px rgba(106,170,100,0.6);
    }
    .attempt-dot.current {
        background: #c9b458;
        box-shadow: 0 0 8px rgba(201,180,88,0.6);
        animation: dot-pulse 1.5s infinite;
    }
    .attempt-dot.lost {
        background: #e74c3c;
    }
    @keyframes dot-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.3); }
    }

    /* ============================================
       INPUT + PULSANTE INVIA
       ============================================ */
    .stTextInput input {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 0.6rem 0.8rem !important;
        text-transform: uppercase;
        text-align: center;
        letter-spacing: 4px;
        background: #1a1a1b !important;
        color: #fff !important;
        border: 2px solid #3a3a3c !important;
        border-radius: 12px !important;
        height: 52px !important;
        line-height: 1 !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput input::placeholder {
        color: #666 !important;
        text-transform: none;
        letter-spacing: normal;
        font-weight: 400;
        font-size: 0.9rem;
    }
    .stTextInput input:focus {
        border-color: #6aaa64 !important;
        box-shadow: 0 0 0 3px rgba(106,170,100,0.25), 0 0 20px rgba(106,170,100,0.15) !important;
        background: #222224 !important;
    }

    .btn-invia > button {
        background: linear-gradient(135deg, #6aaa64, #4d8a48) !important;
        border: none !important;
        color: #ffffff !important;
        min-height: 52px !important;
        height: 52px !important;
        font-size: 0.95rem !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        letter-spacing: 1px;
        padding: 0 0.5rem !important;
        box-shadow: 0 4px 12px rgba(106,170,100,0.35) !important;
        transition: all 0.15s ease !important;
    }
    .btn-invia > button:hover {
        background: linear-gradient(135deg, #7abb74, #5a9a54) !important;
        box-shadow: 0 6px 16px rgba(106,170,100,0.5) !important;
        transform: translateY(-1px);
    }
    .btn-invia > button:active {
        transform: translateY(1px) scale(0.98);
    }

    .hint-btn > button {
        background: linear-gradient(135deg, #3a3520, #2a2a1b) !important;
        border: 2px solid #c9b458 !important;
        color: #f0d97a !important;
        min-height: 44px !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 0.4rem 0.6rem !important;
        box-shadow: 0 0 15px rgba(201,180,88,0.15) !important;
        transition: all 0.2s ease !important;
    }
    .hint-btn > button:hover {
        background: linear-gradient(135deg, #4a4525, #3a3a25) !important;
        box-shadow: 0 0 25px rgba(201,180,88,0.35) !important;
        color: #ffe680 !important;
    }

    .stButton > button {
        width: 100%;
        font-weight: 700 !important;
        background: #1a1a1b !important;
        color: #ffffff !important;
        border: 1px solid #3a3a3c !important;
        border-radius: 10px !important;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        background: #2a2a2c !important;
        border-color: #6aaa64 !important;
        transform: translateY(-1px);
    }
    .stButton > button:active { transform: translateY(0); }

    .mode-btn > button {
        min-height: 56px !important;
        font-size: 1rem !important;
        border-radius: 14px !important;
    }

    /* ============================================
       TAB LOGIN / REGISTRATI
       ============================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: transparent !important;
        border-bottom: 2px solid #2a2a2c !important;
        padding: 0 !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px !important;
        background: transparent !important;
        border-radius: 0 !important;
        padding: 0 16px !important;
        color: #888 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-bottom: 3px solid transparent !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #c9b458 !important; }
    .stTabs [aria-selected="true"] {
        color: #6aaa64 !important;
        border-bottom: 3px solid #6aaa64 !important;
        background: rgba(106,170,100,0.08) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background: #6aaa64 !important; }

    /* ============================================
       AVATAR UTENTE
       ============================================ */
    .user-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        background: linear-gradient(135deg, #2a2a2c, #1a1a1b);
        border: 2px solid #3a3a3c;
        flex-shrink: 0;
    }
    .user-avatar.admin {
        background: linear-gradient(135deg, #4a3a1b, #2a2a1b);
        border-color: #c9b458;
        box-shadow: 0 0 15px rgba(201,180,88,0.3);
    }
    .user-info { flex: 1; min-width: 0; }
    .user-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .user-role {
        font-size: 0.75rem;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
    }
    .user-role.admin { color: #c9b458; font-weight: 700; }

    .sidebar-player {
        display: flex;
        align-items: center;
        gap: 12px;
        background: linear-gradient(135deg, #1a1a1b, #232324);
        border: 1px solid #3a3a3c;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 1rem;
    }
    .sidebar-player .user-avatar {
        width: 42px;
        height: 42px;
        font-size: 22px;
    }

    /* ============================================
       ALTRI ELEMENTI
       ============================================ */
    .stAlert {
        background: #1a1a1b !important;
        border-radius: 12px !important;
        padding: 0.6rem 0.9rem !important;
        font-size: 0.85rem !important;
        border-left: 4px solid #6aaa64 !important;
    }

    .leader-card {
        background: linear-gradient(135deg, #1a1a1b, #202022);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 8px;
        border-left: 4px solid #6aaa64;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .leader-card.me {
        border-left-color: #c9b458;
        background: linear-gradient(135deg, #232324, #2a2a25);
        box-shadow: 0 2px 12px rgba(201,180,88,0.15);
    }
    .leader-name { font-size: 1.05rem; font-weight: 700; color: #ffffff; }
    .leader-stats { font-size: 0.8rem; color: #b0b0b0; margin-top: 3px; }

    .live-dot {
        display: inline-block;
        width: 7px; height: 7px;
        background: #6aaa64;
        border-radius: 50%;
        margin-right: 5px;
        animation: pulse 2s infinite;
        vertical-align: middle;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .live-label {
        text-align: center;
        color: #6aaa64;
        font-size: 0.72rem;
        margin-bottom: 0.5rem;
    }

    .badge-grid { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 0.75rem 0; }
    .badge-card {
        width: 95px; padding: 10px 6px; border-radius: 12px;
        text-align: center; border: 2px solid #3a3a3c;
        background: linear-gradient(135deg, #1a1a1b, #232324);
    }
    .badge-card.earned {
        border-color: #c9b458;
        background: linear-gradient(135deg, #2a2a1b, #1a1a1b);
        box-shadow: 0 0 15px rgba(201,180,88,0.3);
    }
    .badge-card.locked { opacity: 0.35; filter: grayscale(0.8); }
    .badge-icon { font-size: 1.5rem; margin-bottom: 4px; }
    .badge-name { font-size: 0.75rem; font-weight: 700; color: #fff; }
    .badge-desc { font-size: 0.62rem; color: #a0a0a0; margin-top: 2px; line-height: 1.25; }

    .stat-item { text-align: center; }
    .stat-value {
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6aaa64, #c9b458);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .stat-label { font-size: 0.62rem; color: #a0a0a0; text-transform: uppercase; letter-spacing: 0.4px; }

    /* ============================================
       PALLONCINI
       ============================================ */
    .balloons-container {
        position: fixed; bottom: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none; z-index: 9999; overflow: hidden;
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

    @media (max-width: 380px) {
        .grid-cell { width: 50px; height: 50px; font-size: 24px; }
        .grid-row { gap: 3px; margin-bottom: 3px; }
        .wordle-title { font-size: 1.3rem; letter-spacing: 3px; }
        .wordle-tile { width: 28px; height: 28px; font-size: 14px; }
        .stTextInput input { height: 48px !important; letter-spacing: 2px; }
        .btn-invia > button { min-height: 48px !important; height: 48px !important; }
    }
    @media (max-height: 720px) {
        .grid-cell { width: 50px; height: 50px; font-size: 24px; }
        .grid-row { margin-bottom: 3px; }
        .wordle-title { font-size: 1.3rem; }
        .wordle-tile { width: 28px; height: 28px; font-size: 14px; }
        .stTextInput input { height: 48px !important; }
        .btn-invia > button { min-height: 48px !important; height: 48px !important; }
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

def leggi_utenti() -> pd.DataFrame:
    ws = get_worksheet("Utenti")
    if ws is None:
        return pd.DataFrame(columns=["Username", "PIN_Hash", "Ruolo", "Data_Creazione"])
    dati = ws.get_all_records()
    if not dati:
        return pd.DataFrame(columns=["Username", "PIN_Hash", "Ruolo", "Data_Creazione"])
    return pd.DataFrame(dati)

def leggi_partite() -> pd.DataFrame:
    ws = get_worksheet("Partite")
    if ws is None:
        return pd.DataFrame(columns=["Data", "Username", "Modalità", "Tentativi_Usati", "Vinta", "Punti_Ottenuti"])
    dati = ws.get_all_records()
    if not dati:
        return pd.DataFrame(columns=["Data", "Username", "Modalità", "Tentativi_Usati", "Vinta", "Punti_Ottenuti"])
    return pd.DataFrame(dati)

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
            "Giorno" if modalita == "daily" else "Illimitato",
            tentativi,
            "Sì" if vinta else "No",
            punti,
        ])
    except Exception as e:
        st.error(f"Errore registrazione partita: {e}")

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
# AVATAR E RUOLI
# =========================================================
def get_avatar(username: str, ruolo: str = "User") -> str:
    """Restituisce un'emoji avatar in base al nome/ruolo."""
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
        return
    res = get_suggerimento()
    if res is None:
        st.toast("Hai già indovinato tutte le lettere!", icon="ℹ️")
        return
    pos, lettera = res
    st.session_state.suggerimento_pos = pos
    st.session_state.suggerimento_usato = True
    st.toast(f"💡 Posizione {pos+1}: **{lettera}**", icon="💡")

# =========================================================
# RENDER COMPONENTI
# =========================================================
def render_header():
    """Header stilizzato con tessere Wordle."""
    st.markdown("""
        <div class="wordle-header">
            <div class="wordle-tiles">
                <div class="wordle-tile tile-green">P</div>
                <div class="wordle-tile tile-yellow">A</div>
                <div class="wordle-tile tile-gray">R</div>
                <div class="wordle-tile tile-green">O</div>
                <div class="wordle-tile tile-yellow">L</div>
                <div class="wordle-tile tile-green">A</div>
                <div class="wordle-tile tile-gray">R</div>
                <div class="wordle-tile tile-yellow">I</div>
                <div class="wordle-tile tile-green">O</div>
            </div>
            <div class="wordle-title">PAROLARIO</div>
            <div class="wordle-subtitle">Indovina la parola di 5 lettere</div>
        </div>
    """, unsafe_allow_html=True)

def render_griglia():
    sugg_pos = st.session_state.get("suggerimento_pos")
    key_dinamica = f"input_parola_{st.session_state.get('input_version', 0)}"
    corrente = st.session_state.get(key_dinamica, "").upper()

    # Barra dei pallini tentativi
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

    # Griglia
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
        st.info("Nessun giocatore registrato ancora.")
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
# SIDEBAR
# =========================================================
def render_sidebar():
    with st.sidebar:
        utente = st.session_state.utente or "—"
        ruolo = st.session_state.get("ruolo", "User")
        avatar = get_avatar(utente, ruolo)
        ruolo_label = get_ruolo_label(ruolo)

        st.markdown("""
            <div style="text-align:center; padding-bottom:0.6rem;">
                <div style="font-size:1.3rem; font-weight:900;
                            background:linear-gradient(135deg,#6aaa64,#c9b458);
                            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                            letter-spacing:3px;">PAROLARIO</div>
            </div>
        """, unsafe_allow_html=True)

        nome_vis = utente if len(utente) <= 14 else utente[:13] + "…"
        avatar_classe = "admin" if ruolo == "Admin" else ""
        ruolo_classe = "admin" if ruolo == "Admin" else ""
        st.markdown(f"""
            <div class="sidebar-player">
                <div class="user-avatar {avatar_classe}">{avatar}</div>
                <div class="user-info">
                    <div class="user-name">{nome_vis}</div>
                    <div class="user-role {ruolo_classe}">{ruolo_label}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">Navigazione</div>', unsafe_allow_html=True)
        if st.button("🏠  Menu principale", use_container_width=True, key="sb_menu"):
            st.session_state.pagina = "menu"
            for k in ["modalita", "soluzione", "tentativi", "corrente",
                      "finita", "vinto", "punteggio_assegnato",
                      "suggerimento_usato", "suggerimento_pos", "mostra_definizione"]:
                st.session_state.pop(k, None)
            st.rerun()
        if st.button("🏆  Classifica", use_container_width=True, key="sb_leader"):
            st.session_state.pagina = "classifica"
            st.rerun()
        if st.button("📊  Statistiche", use_container_width=True, key="sb_stats"):
            st.session_state.pagina = "statistiche"
            st.rerun()

        if ruolo == "Admin":
            st.markdown('<div class="sidebar-section">👑 Admin Panel</div>', unsafe_allow_html=True)
            if st.button("⚙️  Pannello Admin", use_container_width=True, key="sb_admin"):
                st.session_state.pagina = "admin"
                st.rerun()

        st.markdown('<div class="sidebar-section">Sessione</div>', unsafe_allow_html=True)
        if st.button("🚪  Logout", use_container_width=True, key="sb_logout"):
            for k in list(st.session_state.keys()):
                st.session_state.pop(k, None)
            st.rerun()

# =========================================================
# LOGIN / REGISTRAZIONE
# =========================================================
def render_login():
    """Schermata di login/registrazione con header stilizzato."""
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
                        st.session_state.ruolo = riga.iloc[0].get("Ruolo", "User")
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

    st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)
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
    gia_giocato = None
    if st.session_state.get("ruolo") != "Guest":
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
    if st.button("🎲  GIOCA ANCORA", use_container_width=True, key="m_unlimited"):
        reset_partita("unlimited")
        st.session_state.pagina = "gioco"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("🏆  Classifica", use_container_width=True, key="m_leader"):
            st.session_state.pagina = "classifica"
            st.rerun()
    with c2:
        if st.button("📊  Statistiche", use_container_width=True, key="m_stats"):
            st.session_state.pagina = "statistiche"
            st.rerun()

def pagina_gioco():
    render_header()
    titolo_mod = "📅 Parola del Giorno" if st.session_state.modalita == "daily" else "🎲 Illimitato"
    st.markdown(f'<div class="mode-label" style="text-align:center;color:#a0a0a0;font-size:0.72rem;margin-bottom:0.3rem;">{titolo_mod}</div>',
                unsafe_allow_html=True)

    render_griglia()

    # ============================================
    # FINE PARTITA
    # ============================================
    if st.session_state.finita:
        if st.session_state.vinto:
            n = len(st.session_state.tentativi)
            punti = calcola_punti(n)
            if not st.session_state.punteggio_assegnato:
                if st.session_state.get("ruolo") != "Guest":
                    registra_partita(st.session_state.utente, st.session_state.modalita, n, True, punti)
                st.session_state.punteggio_assegnato = True
                render_palloncini()
            st.success(f"🎉 Bravissimo! In {n} tentativi — **+{punti} punti!**")

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
                if st.session_state.get("ruolo") != "Guest":
                    registra_partita(st.session_state.utente, st.session_state.modalita, MAX_TRIES, False, 0)
                st.session_state.punteggio_assegnato = True
            st.error(f"😢 Peccato! La parola era: **{st.session_state.soluzione}**")

        st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("🔄  Nuova", use_container_width=True, key="end_new"):
                reset_partita("unlimited")
                st.rerun()
        with c2:
            if st.button("🏠  Menu", use_container_width=True, key="end_menu"):
                st.session_state.pagina = "menu"
                st.rerun()
        return

    # ============================================
    # INPUT + INVIO
    # ============================================
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

    # Suggerimento
    if not st.session_state.suggerimento_usato:
        st.markdown('<div class="hint-btn">', unsafe_allow_html=True)
        if st.button("💡  SUGGERIMENTO  (una sola volta per partita)",
                     use_container_width=True, key="hint_btn"):
            usa_suggerimento()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;color:#c9b458;font-size:0.75rem;'
            'padding:0.5rem 0;letter-spacing:0.5px;">💡 Suggerimento già usato</div>',
            unsafe_allow_html=True
        )

def pagina_classifica():
    render_header()
    st.markdown('<div class="live-label"><span class="live-dot"></span>'
                'Dati in tempo reale da Google Sheets</div>', unsafe_allow_html=True)
    render_classifica()
    if st.button("⬅️  Torna al Menu", use_container_width=True, key="back_menu"):
        st.session_state.pagina = "menu"
        st.rerun()

def pagina_statistiche():
    render_header()
    utente = st.session_state.utente
    st.markdown(f'<div style="text-align:center;color:#fff;font-size:1rem;font-weight:700;margin:0.5rem 0;">📊 {utente}</div>',
                unsafe_allow_html=True)

    df = leggi_partite()
    if df.empty:
        st.info("Nessuna partita registrata.")
    else:
        df_u = df[df["Username"] == utente]
        if df_u.empty:
            st.info("Nessuna partita per questo utente.")
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
                df_chart = pd.DataFrame({"Tentativi": [f"{i}°" for i in dist.index], "Volte": dist.values})
                st.bar_chart(df_chart, x="Tentativi", y="Volte", color="#6aaa64", height=180)

    if st.button("⬅️  Torna al Menu", use_container_width=True, key="back_stats"):
        st.session_state.pagina = "menu"
        st.rerun()

def pagina_admin():
    render_header()
    st.markdown('<div style="text-align:center;color:#c9b458;font-size:1rem;font-weight:700;margin:0.5rem 0;">👑 PANNELLO ADMIN</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👥 Utenti", "📊 Partite", "📖 Parole"])

    with tab1:
        df = leggi_utenti()
        if not df.empty:
            st.dataframe(df[["Username", "Ruolo", "Data_Creazione"]], use_container_width=True, hide_index=True)
            utente_sel = st.selectbox("Seleziona utente", df["Username"].tolist(), key="admin_user_reset")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Reset Punti", use_container_width=True, key="admin_reset_punti"):
                    ws = get_worksheet("Partite")
                    if ws:
                        celle = ws.findall(utente_sel)
                        righe_da_cancellare = sorted({c.row for c in celle if c.col == 2}, reverse=True)
                        for riga in righe_da_cancellare:
                            ws.delete_rows(riga)
                        st.success(f"Punti di {utente_sel} resettati.")
                        st.rerun()
            with col2:
                if st.button("🗑️ Elimina Utente", use_container_width=True, key="admin_del_user"):
                    ws = get_worksheet("Utenti")
                    if ws:
                        celle = ws.findall(utente_sel)
                        righe = sorted({c.row for c in celle if c.col == 1}, reverse=True)
                        for riga in righe:
                            ws.delete_rows(riga)
                        st.success(f"Utente {utente_sel} eliminato.")
                        st.rerun()

    with tab2:
        df = leggi_partite()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab3:
        st.caption(f"Parole soluzione attuali: {len(PAROLE_SOLUZIONE)}")
        st.caption(f"Parole valide totali: {len(PAROLE_VALIDE)}")
        st.info("Per aggiungere/rimuovere parole, modifica il file `parole.py` su GitHub.")

    if st.button("⬅️  Torna al Menu", use_container_width=True, key="back_admin"):
        st.session_state.pagina = "menu"
        st.rerun()

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

if st.session_state.utente:
    render_sidebar()

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
elif st.session_state.pagina == "admin" and st.session_state.get("ruolo") == "Admin":
    pagina_admin()
else:
    pagina_menu()
