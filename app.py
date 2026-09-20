# app.py
"""
Parolario — Wordle in famiglia (2-3 giocatori)
Layout Mobile-First: sidebar per gestione, schermo pulito per il gioco.
"""

import streamlit as st
import random
import json
import os
from datetime import date
from streamlit_autorefresh import st_autorefresh
from parole import PAROLE_SOLUZIONE, PAROLE_VALIDE

# =========================================================
# CONFIGURAZIONE PAGINA
# =========================================================
APP_NAME = "Parolario"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🟩",
    layout="centered",
    initial_sidebar_state="collapsed",  # <-- collassata di default
)

# =========================================================
# CSS PERSONALIZZATO — MOBILE-FIRST DEFINITIVO
# =========================================================
st.markdown("""
<style>
    /* ============================================
       1. PADDING TOP ZERO — NIENTE SPAZIO VUOTO
       ============================================ */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
        max-width: 420px !important;
        margin: auto !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;  /* Nasconde l'header trasparente */
    }
    .stApp { background-color: #121213; }

    /* Azzera gap verticali tra elementi Streamlit */
    div[data-testid="stVerticalBlock"] > div { gap: 0.2rem !important; }
    .element-container { margin-bottom: 0 !important; }
    div[data-testid="column"] { padding: 0 !important; }

    /* ============================================
       2. TITOLO COMPATTO (1 RIGA SOLA)
       ============================================ */
    .top-title {
        text-align: center;
        font-size: 1.4rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 0.5px;
        margin: 0 0 0.4rem 0;
        padding: 0;
    }
    .mode-label {
        text-align: center;
        color: #a0a0a0;
        font-size: 0.8rem;
        margin: 0 0 0.4rem 0;
    }

    /* ============================================
       3. GRIGLIA — GRANDE, CENTRATA, SENZA SCROLL
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
        width: 62px;
        height: 62px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        font-weight: 800;
        border: 2px solid #3a3a3c;
        border-radius: 6px;
        text-transform: uppercase;
        color: #ffffff;
        background: #121213;
        transition: all 0.15s ease;
    }
    .grid-cell.filled  { border-color: #565758; }
    .grid-cell.correct { background: #6aaa64; border-color: #6aaa64; }
    .grid-cell.present { background: #c9b458; border-color: #c9b458; }
    .grid-cell.absent  { background: #3a3a3c; border-color: #3a3a3c; }
    .grid-cell.hint    { border-color: #c9b458; background: #2a2a1b; animation: pulse-hint 1s infinite; }

    @keyframes pulse-hint {
        0%, 100% { box-shadow: 0 0 0 0 rgba(201,180,88,0.4); }
        50%      { box-shadow: 0 0 0 6px rgba(201,180,88,0); }
    }

    /* ============================================
       4. INPUT + PULSANTE INVIO
       ============================================ */
    .stTextInput input {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        padding: 0.7rem 0.8rem !important;
        text-transform: uppercase;
        text-align: center;
        letter-spacing: 4px;
        background: #1a1a1b !important;
        color: #fff !important;
        border: 2px solid #3a3a3c !important;
        border-radius: 10px !important;
        height: 54px !important;
    }
    .stTextInput input::placeholder {
        color: #555 !important;
        text-transform: none;
        letter-spacing: normal;
        font-weight: 400;
        font-size: 0.95rem;
    }
    .stTextInput input:focus {
        border-color: #6aaa64 !important;
        box-shadow: 0 0 0 2px rgba(106,170,100,0.3) !important;
    }

    /* Bottone "Invia" */
    .btn-invia > button {
        background: #6aaa64 !important;
        border-color: #6aaa64 !important;
        color: #ffffff !important;
        min-height: 54px !important;
        font-size: 1.6rem !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
    }
    .btn-invia > button:hover { background: #7abb74 !important; }
    .btn-invia > button:active { transform: scale(0.95); }

    /* Bottone suggerimento */
    .hint-btn > button {
        background: #2a2a1b !important;
        border: 1px solid #c9b458 !important;
        color: #c9b458 !important;
        min-height: 40px !important;
        font-size: 0.85rem !important;
        border-radius: 8px !important;
    }
    .hint-btn > button:hover { background: #3a3a2b !important; }

    /* Bottoni generici */
    .stButton > button {
        width: 100%;
        font-weight: 700 !important;
        background: #1a1a1b !important;
        color: #ffffff !important;
        border: 1px solid #3a3a3c !important;
        border-radius: 8px !important;
        transition: all 0.1s ease;
    }
    .stButton > button:hover {
        background: #2a2a2c !important;
        border-color: #6aaa64 !important;
    }
    .stButton > button:active { transform: scale(0.97); }

    /* Bottoni modalità */
    .mode-btn > button {
        min-height: 56px !important;
        font-size: 1rem !important;
        border-radius: 12px !important;
    }

    /* ============================================
       5. SIDEBAR
       ============================================ */
    section[data-testid="stSidebar"] {
        background: #0e0e10 !important;
        border-right: 1px solid #2a2a2c;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        font-size: 0.9rem !important;
        min-height: 44px !important;
        margin-bottom: 4px;
    }
    .sidebar-title {
        text-align: center;
        font-size: 1.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.6rem;
    }
    .sidebar-player {
        text-align: center;
        background: #1a1a1b;
        border: 1px solid #3a3a3c;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 1rem;
    }
    .sidebar-player .label {
        color: #a0a0a0;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sidebar-player .name {
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 2px;
    }
    .sidebar-section {
        color: #a0a0a0;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 1rem 0 0.4rem 0;
        font-weight: 600;
    }

    /* ============================================
       6. ALTRI COMPONENTI
       ============================================ */
    .stAlert {
        background: #1a1a1b !important;
        border-radius: 10px !important;
        padding: 0.5rem 0.8rem !important;
        font-size: 0.85rem !important;
    }

    .leader-card {
        background: #1a1a1b;
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-left: 4px solid #6aaa64;
    }
    .leader-card.me { border-left-color: #c9b458; background: #232324; }
    .leader-name { font-size: 1rem; font-weight: 700; color: #ffffff; }
    .leader-stats { font-size: 0.8rem; color: #b0b0b0; margin-top: 2px; }

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
        width: 95px; padding: 10px 6px; border-radius: 10px;
        text-align: center; border: 2px solid #3a3a3c; background: #1a1a1b;
    }
    .badge-card.earned {
        border-color: #c9b458;
        background: linear-gradient(135deg, #2a2a1b, #1a1a1b);
        box-shadow: 0 0 10px rgba(201,180,88,0.25);
    }
    .badge-card.locked { opacity: 0.35; filter: grayscale(0.8); }
    .badge-icon { font-size: 1.5rem; margin-bottom: 4px; }
    .badge-name { font-size: 0.75rem; font-weight: 700; color: #fff; }
    .badge-desc { font-size: 0.62rem; color: #a0a0a0; margin-top: 2px; line-height: 1.25; }

    .stat-item { text-align: center; }
    .stat-value { font-size: 1.5rem; font-weight: 800; color: #6aaa64; }
    .stat-label { font-size: 0.62rem; color: #a0a0a0; text-transform: uppercase; letter-spacing: 0.4px; }

    /* ============================================
       7. CORIANDOLI LENTI (4-5 secondi)
       ============================================ */
    .confetti-container {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }
    .confetti-piece {
        position: absolute;
        width: 10px;
        height: 14px;
        opacity: 0;
        top: -20px;
        border-radius: 2px;
        animation-name: confetti-fall;
        animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94);
        animation-iteration-count: 1;
        animation-fill-mode: forwards;
    }
    @keyframes confetti-fall {
        0% {
            transform: translateY(0) rotate(0deg) translateX(0);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        50% {
            transform: translateY(50vh) rotate(360deg) translateX(20px);
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(110vh) rotate(900deg) translateX(-20px);
            opacity: 0;
        }
    }

    /* Nasconde menu Streamlit in fondo */
    footer {visibility: hidden;}

    /* ============================================
       8. RESPONSIVE
       ============================================ */
    @media (max-width: 380px) {
        .grid-cell { width: 54px; height: 54px; font-size: 26px; }
        .grid-row { gap: 4px; margin-bottom: 4px; }
        .top-title { font-size: 1.2rem; }
        .stTextInput input { height: 50px !important; letter-spacing: 3px; }
        .btn-invia > button { min-height: 50px !important; }
    }

    @media (max-height: 700px) {
        .grid-cell { width: 52px; height: 52px; font-size: 24px; }
        .grid-row { margin-bottom: 4px; }
        .top-title { font-size: 1.2rem; }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# COSTANTI
# =========================================================
WORD_LEN = 5
MAX_TRIES = 6
PROFILI_PREDEFINITI = ["Mamma", "Papà"]
DATA_FILE = "dati_gioco.json"
REFRESH_MS = 30_000
PAGINE_CON_REFRESH = {"classifica", "menu", "statistiche"}

# =========================================================
# BADGE
# =========================================================
BADGES = [
    {"id": "prima_vittoria", "icon": "🎯", "name": "Prima", "desc": "Prima vittoria"},
    {"id": "genio", "icon": "🧠", "name": "Genio", "desc": "Al 2° tentativo"},
    {"id": "streak_3", "icon": "🔥", "name": "In Fiamme", "desc": "Streak di 3"},
    {"id": "streak_7", "icon": "⚡", "name": "Imbattibile", "desc": "Streak di 7"},
    {"id": "veterano", "icon": "🎖️", "name": "Veterano", "desc": "20 partite"},
    {"id": "perfezionista", "icon": "👑", "name": "Perfetto", "desc": "Al 1° tentativo"},
    {"id": "cinque", "icon": "⭐", "name": "Cinque", "desc": "In 5 tentativi"},
    {"id": "cento_punti", "icon": "💯", "name": "Cento", "desc": "100 punti"},
]

# =========================================================
# PERSISTENZA
# =========================================================
def carica_dati():
    default = {"utenti": {}, "daily_giocato": {}}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                d.setdefault("utenti", {})
                d.setdefault("daily_giocato", {})
                for u in d["utenti"].values():
                    u.setdefault("tentativi_distribuzione", [0]*6)
                    u.setdefault("suggerimenti_usati", 0)
                    u.setdefault("badges", [])
                return d
        except Exception:
            pass
    return default

def salva_dati(dati):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)

def assicura_utente(nome: str):
    d = st.session_state.dati
    if nome not in d["utenti"]:
        d["utenti"][nome] = {
            "punti": 0, "vittorie": 0, "partite": 0,
            "streak": 0, "max_streak": 0,
            "tentativi_distribuzione": [0]*6,
            "suggerimenti_usati": 0,
            "badges": [],
        }
        salva_dati(d)

def rinomina_utente(vecchio: str, nuovo: str) -> bool:
    nuovo = nuovo.strip()
    if not nuovo:
        return False
    d = st.session_state.dati
    if nuovo in d["utenti"] and nuovo != vecchio:
        return False
    if vecchio not in d["utenti"]:
        return False
    nuovi_utenti = {}
    for k, v in d["utenti"].items():
        nuovi_utenti[nuovo if k == vecchio else k] = v
    d["utenti"] = nuovi_utenti
    for giorno, players in d["daily_giocato"].items():
        if vecchio in players:
            players[nuovo] = players.pop(vecchio)
    salva_dati(d)
    return True

def elimina_utente(nome: str) -> bool:
    d = st.session_state.dati
    if nome not in d["utenti"]:
        return False
    del d["utenti"][nome]
    for giorno in list(d["daily_giocato"].keys()):
        if nome in d["daily_giocato"][giorno]:
            del d["daily_giocato"][giorno][nome]
        if not d["daily_giocato"][giorno]:
            del d["daily_giocato"][giorno]
    salva_dati(d)
    return True

def reset_tutto():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.session_state.dati = {"utenti": {}, "daily_giocato": {}}
    salva_dati(st.session_state.dati)
    for k in list(st.session_state.keys()):
        if k != "dati":
            st.session_state.pop(k, None)
    st.rerun()

if "dati" not in st.session_state:
    st.session_state.dati = carica_dati()

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

# =========================================================
# STATO PARTITA
# =========================================================
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
    st.session_state.nuovi_badges = []

# =========================================================
# BADGE
# =========================================================
def controlla_badges(utente: str, tentativo_num: int, vinto: bool):
    d = st.session_state.dati
    u = d["utenti"][utente]
    nuovi = []

    def sblocca(bid):
        if bid not in u["badges"]:
            u["badges"].append(bid)
            nuovi.append(bid)

    if vinto:
        sblocca("prima_vittoria")
        if tentativo_num == 1:
            sblocca("perfezionista")
        if tentativo_num <= 2:
            sblocca("genio")
        if tentativo_num == 5:
            sblocca("cinque")
    if u["streak"] >= 3:
        sblocca("streak_3")
    if u["streak"] >= 7:
        sblocca("streak_7")
    if u["partite"] >= 20:
        sblocca("veterano")
    if u["punti"] >= 100:
        sblocca("cento_punti")

    if nuovi:
        salva_dati(d)
    return nuovi

def render_nuovi_badges(nuovi):
    if not nuovi:
        return
    for bid in nuovi:
        b = next((x for x in BADGES if x["id"] == bid), None)
        if b:
            st.toast(f"{b['icon']} Nuovo badge: {b['name']}!", icon="🏆")

# =========================================================
# REGISTRAZIONE
# =========================================================
def registra_vittoria(utente: str, punti: int, modalita: str, tentativo_num: int):
    d = st.session_state.dati
    u = d["utenti"].setdefault(utente, {"punti":0,"vittorie":0,"partite":0,"streak":0,"max_streak":0,
                                          "tentativi_distribuzione":[0]*6,"suggerimenti_usati":0,"badges":[]})
    u["punti"] += punti
    u["vittorie"] += 1
    u["partite"] += 1
    u["streak"] += 1
    u["max_streak"] = max(u["max_streak"], u["streak"])
    u["tentativi_distribuzione"][tentativo_num - 1] += 1
    if modalita == "daily":
        d["daily_giocato"].setdefault(date.today().isoformat(), {})[utente] = {"punti": punti, "vinto": True}
    salva_dati(d)
    return controlla_badges(utente, tentativo_num, True)

def registra_sconfitta(utente: str, modalita: str):
    d = st.session_state.dati
    u = d["utenti"].setdefault(utente, {"punti":0,"vittorie":0,"partite":0,"streak":0,"max_streak":0,
                                          "tentativi_distribuzione":[0]*6,"suggerimenti_usati":0,"badges":[]})
    u["partite"] += 1
    u["streak"] = 0
    if modalita == "daily":
        d["daily_giocato"].setdefault(date.today().isoformat(), {})[utente] = {"punti": 0, "vinto": False}
    salva_dati(d)
    return controlla_badges(utente, 0, False)

# =========================================================
# AZIONI
# =========================================================
def invia_tentativo(parola_input: str = None):
    parola = (parola_input or st.session_state.corrente).upper().strip()
    if len(parola) != WORD_LEN:
        st.toast("La parola deve avere 5 lettere!", icon="⚠️")
        return
    if parola not in PAROLE_VALIDE:
        st.toast(f"'{parola}' non è nel dizionario", icon="🚫")
        return
    fb = calcola_feedback(parola, st.session_state.soluzione)
    st.session_state.tentativi.append((parola, fb))
    st.session_state.corrente = ""
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
    d = st.session_state.dati
    utente = st.session_state.utente
    if utente in d["utenti"]:
        d["utenti"][utente]["suggerimenti_usati"] += 1
        salva_dati(d)
    st.toast(f"💡 Posizione {pos+1}: **{lettera}**", icon="💡")

# =========================================================
# SIDEBAR
# =========================================================
def render_sidebar():
    """Sidebar con profilo, cambia giocatore, menu e azioni admin."""
    with st.sidebar:
        utente = st.session_state.utente or "—"
        st.markdown(f'<div class="sidebar-title">🟩 {APP_NAME}</div>', unsafe_allow_html=True)

        # Card giocatore
        nome_vis = utente if len(utente) <= 14 else utente[:13] + "…"
        st.markdown(f"""
            <div class="sidebar-player">
                <div class="label">Giocatore</div>
                <div class="name">👤 {nome_vis}</div>
            </div>
        """, unsafe_allow_html=True)

        # Sezione profilo
        st.markdown('<div class="sidebar-section">Profilo</div>', unsafe_allow_html=True)
        if st.button("✏️ Modifica Nickname", use_container_width=True, key="sb_edit_nick"):
            st.session_state.modifica_nick = True
            st.session_state.pagina = "profilo"
            st.rerun()
        if st.button("🔄 Cambia Giocatore", use_container_width=True, key="sb_change"):
            for k in ["utente","modalita","soluzione","tentativi","corrente",
                      "finita","vinto","punteggio_assegnato",
                      "modifica_nick","suggerimento_usato","suggerimento_pos",
                      "mostra_definizione","nuovi_badges","pagina"]:
                st.session_state.pop(k, None)
            st.rerun()

        # Sezione navigazione
        st.markdown('<div class="sidebar-section">Navigazione</div>', unsafe_allow_html=True)
        if st.button("🏠 Menu principale", use_container_width=True, key="sb_menu"):
            st.session_state.pagina = "menu"
            for k in ["modalita","soluzione","tentativi","corrente",
                      "finita","vinto","punteggio_assegnato",
                      "suggerimento_usato","suggerimento_pos","mostra_definizione",
                      "nuovi_badges"]:
                st.session_state.pop(k, None)
            st.rerun()
        if st.button("🏆 Classifica", use_container_width=True, key="sb_leader"):
            st.session_state.pagina = "classifica"
            st.rerun()
        if st.button("📊 Statistiche", use_container_width=True, key="sb_stats"):
            st.session_state.pagina = "statistiche"
            st.rerun()

        # Zona admin
        st.markdown('<div class="sidebar-section">Admin</div>', unsafe_allow_html=True)
        with st.expander("⚠️ Zona Admin"):
            st.caption("Azione irreversibile.")
            conf = st.text_input("Scrivi RESET", key="sb_reset_confirm")
            if st.button("🗑️ Cancella tutto", use_container_width=True, key="sb_reset"):
                if conf.strip().upper() == "RESET":
                    reset_tutto()
                else:
                    st.error("Scrivi RESET per confermare.")

# =========================================================
# GRIGLIA
# =========================================================
def render_griglia():
    sugg_pos = st.session_state.get("suggerimento_pos")
    righe_html = ['<div class="grid-wrapper">']
    for r in range(MAX_TRIES):
        celle = []
        if r < len(st.session_state.tentativi):
            parola, fb = st.session_state.tentativi[r]
            for lettera, colore in zip(parola, fb):
                celle.append(f'<div class="grid-cell {colore}">{lettera}</div>')
        elif r == len(st.session_state.tentativi) and not st.session_state.finita:
            for i in range(WORD_LEN):
                if i < len(st.session_state.corrente):
                    classe = "filled"
                    if sugg_pos is not None and i == sugg_pos:
                        classe = "hint"
                    celle.append(f'<div class="grid-cell {classe}">{st.session_state.corrente[i]}</div>')
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

# =========================================================
# ALTRI RENDER
# =========================================================
def genera_risultato_condivisione():
    emoji_map = {"correct": "🟩", "present": "🟨", "absent": "⬜"}
    righe = []
    for parola, fb in st.session_state.tentativi:
        righe.append("".join(emoji_map[c] for c in fb))
    n = len(st.session_state.tentativi)
    return f"Parolario {n}/{MAX_TRIES}\n" + "\n".join(righe)

def render_classifica():
    utenti = st.session_state.dati["utenti"]
    if not utenti:
        st.info("Nessun giocatore registrato ancora.")
        return
    ordinati = sorted(utenti.items(), key=lambda x: (-x[1]["punti"], -x[1]["vittorie"]))
    for pos, (nome, s) in enumerate(ordinati, start=1):
        medaglia = {1:"🥇", 2:"🥈", 3:"🥉"}.get(pos, f"{pos}.")
        io = " me" if nome == st.session_state.get("utente") else ""
        st.markdown(f"""
        <div class="leader-card{io}">
            <div class="leader-name">{medaglia} {nome}</div>
            <div class="leader-stats">
                🏆 <b>{s['punti']}</b> pt · ✅ {s['vittorie']}/{s['partite']} · 🔥 {s['streak']}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_coriandoli_lenti():
    """Coriandoli con caduta dolce di 4-5 secondi, senza st.balloons()."""
    colori = ["#6aaa64", "#c9b458", "#ffffff", "#e74c3c", "#3498db", "#f39c12",
              "#9b59b6", "#1abc9c", "#e67e22"]
    pezzi = []
    for _ in range(60):
        colore = random.choice(colori)
        left = random.randint(0, 100)
        delay = round(random.uniform(0, 1.8), 2)
        durata = round(random.uniform(4.0, 5.5), 2)
        width = random.randint(8, 14)
        height = random.randint(10, 18)
        pezzi.append(
            f'<div class="confetti-piece" style="'
            f'left:{left}%; '
            f'background:{colore}; '
            f'animation-delay:{delay}s; '
            f'animation-duration:{durata}s; '
            f'width:{width}px; '
            f'height:{height}px;'
            f'"></div>'
        )
    st.markdown(
        '<div class="confetti-container">' + "".join(pezzi) + '</div>',
        unsafe_allow_html=True
    )

# =========================================================
# SCHERMATA 1: SELEZIONE
# =========================================================
def pagina_selezione():
    st.markdown(f'<div class="top-title">🟩 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="mode-label">Chi sta giocando?</div>', unsafe_allow_html=True)

    d = st.session_state.dati
    profili_esistenti = list(d["utenti"].keys())
    predefiniti = [p for p in PROFILI_PREDEFINITI if p in profili_esistenti]
    altri = [n for n in profili_esistenti if n not in PROFILI_PREDEFINITI]

    if "conferma_elimina" not in st.session_state:
        st.session_state.conferma_elimina = None

    def render_profilo(nome):
        col_login, col_del = st.columns([5, 1], gap="small")
        with col_login:
            if st.button(f"👤 {nome}", use_container_width=True, key=f"login_{nome}"):
                st.session_state.utente = nome
                st.session_state.dati = carica_dati()
                st.rerun()
        with col_del:
            if st.button("🗑️", use_container_width=True, key=f"del_{nome}"):
                st.session_state.conferma_elimina = nome
                st.rerun()
        if st.session_state.conferma_elimina == nome:
            st.warning(f"Eliminare **{nome}**?")
            c1, c2 = st.columns(2, gap="small")
            with c1:
                if st.button("✅ Sì", use_container_width=True, key=f"conf_yes_{nome}"):
                    elimina_utente(nome)
                    st.session_state.conferma_elimina = None
                    st.rerun()
            with c2:
                if st.button("❌ No", use_container_width=True, key=f"conf_no_{nome}"):
                    st.session_state.conferma_elimina = None
                    st.rerun()

    for nome in predefiniti:
        render_profilo(nome)

    if altri:
        st.markdown('<div style="color:#a0a0a0;font-size:0.8rem;margin-top:0.8rem;">Altri profili</div>',
                    unsafe_allow_html=True)
        for nome in altri:
            render_profilo(nome)

    st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
    n_ospiti = len([n for n in profili_esistenti if n.startswith("Ospite")])
    nome_default = f"Ospite {n_ospiti + 1}" if n_ospiti > 0 or not profili_esistenti else "Ospite"

    with st.expander("➕ Crea un nuovo profilo"):
        nuovo_nome = st.text_input("Nome", placeholder="Es. Nonna, Zio…", key="crea_nome")
        if st.button("Crea profilo", use_container_width=True, key="btn_crea"):
            nome_finale = nuovo_nome.strip() or nome_default
            if nome_finale in d["utenti"]:
                st.error(f"'{nome_finale}' è già in uso.")
            else:
                assicura_utente(nome_finale)
                st.session_state.utente = nome_finale
                st.rerun()

# =========================================================
# SCHERMATA 2: MENU
# =========================================================
def pagina_menu():
    st.markdown(f'<div class="top-title">🟩 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="mode-label">Scegli la modalità</div>', unsafe_allow_html=True)

    st.markdown('<div class="mode-btn">', unsafe_allow_html=True)
    if st.button("📅 Parola del Giorno", use_container_width=True, key="m_daily"):
        reset_partita("daily")
        st.session_state.pagina = "gioco"
        st.rerun()
    if st.button("🎲 Gioca Ancora", use_container_width=True, key="m_unlimited"):
        reset_partita("unlimited")
        st.session_state.pagina = "gioco"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("🏆 Classifica", use_container_width=True, key="m_leader"):
            st.session_state.pagina = "classifica"
            st.rerun()
    with c2:
        if st.button("📊 Statistiche", use_container_width=True, key="m_stats"):
            st.session_state.pagina = "statistiche"
            st.rerun()

# =========================================================
# SCHERMATA 3: GIOCO (PULITA, SENZA SIDEBAR CHIUSA DI DEFAULT)
# =========================================================
def pagina_gioco():
    titolo_mod = "📅 Parola del Giorno" if st.session_state.modalita == "daily" else "🎲 Illimitato"

    st.markdown(f'<div class="top-title">🟩 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mode-label">{titolo_mod}</div>', unsafe_allow_html=True)

    render_griglia()

    # ============================================
    # FINE PARTITA
    # ============================================
    if st.session_state.finita:
        if st.session_state.vinto:
            n = len(st.session_state.tentativi)
            punti = calcola_punti(n)
            if not st.session_state.punteggio_assegnato:
                nuovi_badges = registra_vittoria(st.session_state.utente, punti,
                                                  st.session_state.modalita, n)
                st.session_state.punteggio_assegnato = True
                st.session_state.nuovi_badges = nuovi_badges
                render_coriandoli_lenti()
            render_nuovi_badges(st.session_state.get("nuovi_badges", []))
            st.success(f"🎉 Bravissimo! In {n} tentativi — **+{punti} punti!**")

            with st.expander("📋 Condividi risultato"):
                st.code(genera_risultato_condivisione(), language=None)

            c1, c2 = st.columns(2, gap="small")
            with c1:
                if st.button("📋 WhatsApp", use_container_width=True, key="copy_whats"):
                    st.toast("Copiato!", icon="✅")
            with c2:
                if st.button("🔍 Definizione", use_container_width=True, key="def_btn"):
                    st.session_state.mostra_definizione = True
                    st.rerun()

            if st.session_state.get("mostra_definizione"):
                p = st.session_state.soluzione
                st.info(f"**{p}** — [Treccani](https://www.treccani.it/vocabolario/{p.lower()}/) · "
                        f"[Wikizionario](https://it.wiktionary.org/wiki/{p.lower()})")
        else:
            if not st.session_state.punteggio_assegnato:
                nuovi_badges = registra_sconfitta(st.session_state.utente, st.session_state.modalita)
                st.session_state.punteggio_assegnato = True
                st.session_state.nuovi_badges = nuovi_badges
            render_nuovi_badges(st.session_state.get("nuovi_badges", []))
            st.error(f"😢 Peccato! La parola era: **{st.session_state.soluzione}**")

            with st.expander("📋 Condividi risultato"):
                st.code(genera_risultato_condivisione(), language=None)

            c1, c2 = st.columns(2, gap="small")
            with c1:
                if st.button("📋 WhatsApp", use_container_width=True, key="copy_whats_lose"):
                    st.toast("Copiato!", icon="✅")
            with c2:
                if st.button("🔍 Definizione", use_container_width=True, key="def_btn_lose"):
                    st.session_state.mostra_definizione = True
                    st.rerun()

            if st.session_state.get("mostra_definizione"):
                p = st.session_state.soluzione
                st.info(f"**{p}** — [Treccani](https://www.treccani.it/vocabolario/{p.lower()}/) · "
                        f"[Wikizionario](https://it.wiktionary.org/wiki/{p.lower()})")

        st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("🔄 Nuova", use_container_width=True, key="end_new"):
                reset_partita("unlimited")
                st.rerun()
        with c2:
            if st.button("🏠 Menu", use_container_width=True, key="end_menu"):
                st.session_state.pagina = "menu"
                for k in ["modalita","soluzione","tentativi","corrente",
                          "finita","vinto","punteggio_assegnato",
                          "suggerimento_usato","suggerimento_pos","mostra_definizione",
                          "nuovi_badges"]:
                    st.session_state.pop(k, None)
                st.rerun()
        return

    # ============================================
    # INPUT + INVIO
    # ============================================
    col_input, col_invia = st.columns([4, 1], gap="small")
    with col_input:
        testo = st.text_input(
            "Parola",
            value="",
            max_chars=WORD_LEN,
            key="input_fisico",
            label_visibility="collapsed",
            placeholder="Scrivi la parola…",
            autocomplete="off",
        )
    with col_invia:
        st.markdown('<div class="btn-invia">', unsafe_allow_html=True)
        if st.button("✔️", use_container_width=True, key="btn_invia"):
            invia_tentativo(testo)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Suggerimento + contatore
    col_hint, col_count = st.columns([3, 1], gap="small")
    with col_hint:
        if not st.session_state.suggerimento_usato:
            st.markdown('<div class="hint-btn">', unsafe_allow_html=True)
            if st.button("💡 Suggerimento", use_container_width=True, key="hint_btn"):
                usa_suggerimento()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;color:#c9b458;font-size:0.75rem;padding:0.6rem 0;">💡 usato</div>',
                        unsafe_allow_html=True)
    with col_count:
        st.markdown(f'<div style="text-align:center;color:#a0a0a0;font-size:0.75rem;padding:0.6rem 0;">{len(st.session_state.tentativi)}/{MAX_TRIES}</div>',
                    unsafe_allow_html=True)

# =========================================================
# SCHERMATA 4: CLASSIFICA
# =========================================================
def pagina_classifica():
    st.markdown(f'<div class="top-title">🏆 Classifica</div>', unsafe_allow_html=True)
    st.markdown('<div class="live-label"><span class="live-dot"></span>Auto-aggiornamento 30s</div>',
                unsafe_allow_html=True)
    render_classifica()
    if st.button("⬅️ Torna al Menu", use_container_width=True, key="back_menu"):
        st.session_state.pagina = "menu"
        st.rerun()

# =========================================================
# SCHERMATA 5: STATISTICHE
# =========================================================
def pagina_statistiche():
    utente = st.session_state.utente
    st.markdown(f'<div class="top-title">📊 {utente}</div>', unsafe_allow_html=True)

    d = st.session_state.dati
    u = d["utenti"].get(utente)
    if not u:
        st.info("Nessuna partita registrata.")
        if st.button("⬅️ Menu", use_container_width=True, key="back_from_stats"):
            st.session_state.pagina = "menu"
            st.rerun()
        return

    c1, c2, c3, c4 = st.columns(4, gap="small")
    for col, val, label in [
        (c1, u["partite"], "Partite"),
        (c2, f'{round(100*u["vittorie"]/u["partite"]) if u["partite"] else 0}%', "Vittorie"),
        (c3, u["streak"], "Streak"),
        (c4, u["max_streak"], "Max"),
    ]:
        with col:
            st.markdown(f'<div class="stat-item"><div class="stat-value">{val}</div>'
                        f'<div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="color:#fff;font-size:0.9rem;font-weight:700;margin:0.6rem 0 0.3rem 0;">📈 Distribuzione</div>',
                unsafe_allow_html=True)
    dist = u.get("tentativi_distribuzione", [0]*6)
    if any(dist):
        import pandas as pd
        df = pd.DataFrame({"Tentativi": [f"{i+1}°" for i in range(6)], "Volte": dist})
        st.bar_chart(df, x="Tentativi", y="Volte", color="#6aaa64", height=180)
    else:
        st.caption("Nessuna vittoria ancora.")

    st.markdown('<div style="color:#fff;font-size:0.9rem;font-weight:700;margin:0.6rem 0 0.3rem 0;">🏅 Trofei</div>',
                unsafe_allow_html=True)
    earned = u.get("badges", [])
    st.caption(f"🏆 {len(earned)}/{len(BADGES)} sbloccati")

    badge_html = '<div class="badge-grid">'
    for b in BADGES:
        is_earned = b["id"] in earned
        cls = "earned" if is_earned else "locked"
        badge_html += f"""
        <div class="badge-card {cls}">
            <div class="badge-icon">{b['icon']}</div>
            <div class="badge-name">{b['name']}</div>
            <div class="badge-desc">{b['desc']}</div>
        </div>
        """
    badge_html += '</div>'
    st.markdown(badge_html, unsafe_allow_html=True)

    if st.button("⬅️ Torna al Menu", use_container_width=True, key="back_from_stats2"):
        st.session_state.pagina = "menu"
        st.rerun()

# =========================================================
# SCHERMATA 6: MODIFICA NICKNAME
# =========================================================
def pagina_modifica_nick():
    st.markdown('<div class="top-title">✏️ Modifica Nickname</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;color:#a0a0a0;font-size:0.85rem;">Attuale: <b style="color:#fff;">'
                f'{st.session_state.utente}</b></p>', unsafe_allow_html=True)

    nuovo = st.text_input("Nuovo nickname", value="", max_chars=20, key="nick_input",
                          placeholder="Scrivi il nuovo nome…")

    c1, c2 = st.columns(2, gap="small")
    with c1:
        if st.button("✅ Salva", use_container_width=True, key="nick_save"):
            nome_pulito = nuovo.strip()
            if not nome_pulito:
                st.error("Il nickname non può essere vuoto.")
            elif nome_pulito == st.session_state.utente:
                st.session_state.modifica_nick = False
                st.session_state.pagina = "menu"
                st.rerun()
            elif rinomina_utente(st.session_state.utente, nome_pulito):
                st.session_state.utente = nome_pulito
                st.session_state.modifica_nick = False
                st.session_state.pagina = "menu"
                st.success(f"Aggiornato in '{nome_pulito}'!")
                st.rerun()
            else:
                st.error("Nome già in uso.")
    with c2:
        if st.button("❌ Annulla", use_container_width=True, key="nick_cancel"):
            st.session_state.modifica_nick = False
            st.session_state.pagina = "menu"
            st.rerun()

# =========================================================
# ROUTING
# =========================================================
defaults = {
    "utente": None,
    "pagina": "menu",
    "modifica_nick": False,
    "suggerimento_usato": False,
    "suggerimento_pos": None,
    "mostra_definizione": False,
    "nuovi_badges": [],
    "conferma_elimina": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

if st.session_state.utente and st.session_state.pagina in PAGINE_CON_REFRESH:
    st_autorefresh(interval=REFRESH_MS, key="auto_refresh")
    st.session_state.dati = carica_dati()

# Sidebar visibile solo quando l'utente è loggato
if st.session_state.utente:
    render_sidebar()

# Rendering
if not st.session_state.utente:
    pagina_selezione()
elif st.session_state.modifica_nick:
    pagina_modifica_nick()
elif st.session_state.pagina == "menu":
    pagina_menu()
elif st.session_state.pagina == "gioco":
    pagina_gioco()
elif st.session_state.pagina == "classifica":
    pagina_classifica()
elif st.session_state.pagina == "statistiche":
    pagina_statistiche()
else:
    pagina_menu()
