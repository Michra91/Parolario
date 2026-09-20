# app.py
"""
Parolario — Wordle in famiglia (2-3 giocatori)
Con effetti visivi, suggerimenti, statistiche e badge.
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
    initial_sidebar_state="collapsed",
)

# =========================================================
# CSS PERSONALIZZATO
# =========================================================
st.markdown("""
<style>
    .stApp { background-color: #121213; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 620px; }

    .app-title { text-align:center; font-size:2.2rem; font-weight:800; color:#ffffff; letter-spacing:0.5px; margin-bottom:0.2rem; }
    .app-subtitle { text-align:center; color:#a0a0a0; font-size:0.95rem; margin-bottom:2rem; }

    .player-badge { display:flex; align-items:center; justify-content:space-between; background:#1a1a1b; border:1px solid #3a3a3c; border-radius:12px; padding:12px 18px; margin-bottom:1rem; }
    .player-badge .label { color:#a0a0a0; font-size:0.9rem; }
    .player-badge .name { color:#ffffff; font-size:1.25rem; font-weight:700; }

    .grid-row { display:flex; gap:6px; justify-content:center; margin-bottom:6px; }
    .grid-cell { width:58px; height:58px; display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:bold; border:2px solid #3a3a3c; border-radius:6px; text-transform:uppercase; color:#ffffff; background:#121213; }
    .grid-cell.filled { border-color:#565758; }
    .grid-cell.correct { background:#6aaa64; color:#fff; border-color:#6aaa64; }
    .grid-cell.present { background:#c9b458; color:#fff; border-color:#c9b458; }
    .grid-cell.absent { background:#3a3a3c; color:#fff; border-color:#3a3a3c; }
    .grid-cell.hint { border-color:#c9b458; background:#2a2a1b; }

    .stButton > button { width:100%; font-size:1rem !important; font-weight:600 !important; padding:0.75rem 1rem !important; min-height:52px; border-radius:10px !important; background:#1a1a1b !important; color:#ffffff !important; border:1px solid #3a3a3c !important; transition:all 0.15s ease; }
    .stButton > button:hover { background:#2a2a2c !important; border-color:#6aaa64 !important; }
    .stButton > button:focus { box-shadow:0 0 0 2px #6aaa64 !important; }

    .stTextInput input { font-size:1.15rem !important; padding:0.75rem !important; text-transform:uppercase; background:#1a1a1b !important; color:#fff !important; border:1px solid #3a3a3c !important; border-radius:8px !important; }
    .stTextInput input::placeholder { color:#666 !important; text-transform:none; }

    .leader-card { background:#1a1a1b; border-radius:12px; padding:14px 18px; margin-bottom:10px; border-left:5px solid #6aaa64; }
    .leader-card.me { border-left-color:#c9b458; background:#232324; }
    .leader-name { font-size:1.15rem; font-weight:700; color:#ffffff; }
    .leader-stats { font-size:0.95rem; color:#b0b0b0; margin-top:4px; }

    .stAlert { background:#1a1a1b !important; border-radius:10px !important; }

    .live-dot { display:inline-block; width:8px; height:8px; background:#6aaa64; border-radius:50%; margin-right:6px; animation:pulse 2s infinite; vertical-align:middle; }
    @keyframes pulse { 0%, 100% { opacity:1; } 50% { opacity:0.3; } }
    .live-label { text-align:center; color:#6aaa64; font-size:0.8rem; margin-bottom:0.75rem; }

    /* Badge/trofei */
    .badge-grid { display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin:1rem 0; }
    .badge-card { width:120px; padding:14px 10px; border-radius:12px; text-align:center; border:2px solid #3a3a3c; background:#1a1a1b; transition:all 0.2s; }
    .badge-card.earned { border-color:#c9b458; background:linear-gradient(135deg, #2a2a1b, #1a1a1b); box-shadow:0 0 12px rgba(201,180,88,0.3); }
    .badge-card.locked { opacity:0.35; filter:grayscale(0.8); }
    .badge-icon { font-size:2rem; margin-bottom:6px; }
    .badge-name { font-size:0.85rem; font-weight:700; color:#fff; }
    .badge-desc { font-size:0.7rem; color:#a0a0a0; margin-top:3px; line-height:1.3; }

    /* Coriandoli */
    .confetti-container { position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9999; overflow:hidden; }
    .confetti-piece { position:absolute; width:10px; height:10px; opacity:0; animation:confetti-fall linear forwards; }
    @keyframes confetti-fall {
        0% { transform:translateY(-100px) rotate(0deg); opacity:1; }
        100% { transform:translateY(100vh) rotate(720deg); opacity:0; }
    }

    /* Statistiche */
    .stat-row { display:flex; justify-content:space-around; text-align:center; margin:1rem 0; }
    .stat-item { flex:1; }
    .stat-value { font-size:2rem; font-weight:800; color:#6aaa64; }
    .stat-label { font-size:0.8rem; color:#a0a0a0; text-transform:uppercase; letter-spacing:0.5px; }

    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
    header {visibility:hidden;}
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
# DEFINIZIONI BADGE
# =========================================================
BADGES = [
    {"id": "prima_vittoria", "icon": "🎯", "name": "Prima Vittoria", "desc": "Indovina la prima parola"},
    {"id": "genio", "icon": "🧠", "name": "Genio", "desc": "Indovina al 2° tentativo"},
    {"id": "streak_3", "icon": "🔥", "name": "In Fiamme", "desc": "Streak di 3 vittorie"},
    {"id": "streak_7", "icon": "⚡", "name": "Imbattibile", "desc": "Streak di 7 vittorie"},
    {"id": "veterano", "icon": "🎖️", "name": "Veterano", "desc": "Gioca 20 partite"},
    {"id": "perfezionista", "icon": "👑", "name": "Perfezionista", "desc": "Vinci al 1° tentativo"},
    {"id": "cinque", "icon": "⭐", "name": "Cinque", "desc": "Indovina in 5 tentativi"},
    {"id": "cento_punti", "icon": "💯", "name": "Cento", "desc": "Raggiungi 100 punti"},
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

def aggiorna_colori_tastiera(colori_attuali: dict, tentativo: str, feedback: list):
    priorità = {"absent": 0, "present": 1, "correct": 2}
    for lettera, colore in zip(tentativo.upper(), feedback):
        if lettera not in colori_attuali or priorità[colore] > priorità[colori_attuali[lettera]]:
            colori_attuali[lettera] = colore
    return colori_attuali

def calcola_punti(numero_tentativo: int) -> int:
    return max(0, MAX_TRIES + 1 - numero_tentativo)

def get_suggerimento():
    """Trova una lettera corretta non ancora indovinata e la rivela."""
    soluzione = st.session_state.soluzione.upper()
    # Trova posizioni già indovinate (verdi)
    posizioni_indovinate = set()
    for parola, fb in st.session_state.tentativi:
        for i, colore in enumerate(fb):
            if colore == "correct":
                posizioni_indovinate.add(i)
    # Trova posizioni non ancora rivelate
    posizioni_nascoste = [i for i in range(WORD_LEN) if i not in posizioni_indovinate]
    if not posizioni_nascoste:
        return None
    # Prendi una posizione a caso tra quelle nascoste
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
    st.session_state.colori_tastiera = {}
    st.session_state.finita = False
    st.session_state.vinto = False
    st.session_state.punteggio_assegnato = False
    st.session_state.suggerimento_usato = False
    st.session_state.suggerimento_pos = None
    st.session_state.mostra_definizione = False

# =========================================================
# BADGE
# =========================================================
def controlla_badges(utente: str, tentativo_num: int, vinto: bool):
    """Controlla e sblocca nuovi badge dopo una partita."""
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
# REGISTRAZIONE PUNTEGGI
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
# AZIONI TASTIERA
# =========================================================
def aggiungi_lettera(l):
    if len(st.session_state.corrente) < WORD_LEN and not st.session_state.finita:
        st.session_state.corrente += l

def rimuovi_lettera():
    st.session_state.corrente = st.session_state.corrente[:-1]

def invia_tentativo():
    parola = st.session_state.corrente.upper().strip()
    if len(parola) != WORD_LEN:
        st.toast("La parola deve avere 5 lettere!", icon="⚠️")
        return
    if parola not in PAROLE_VALIDE:
        st.toast(f"'{parola}' non è nel dizionario", icon="🚫")
        return
    fb = calcola_feedback(parola, st.session_state.soluzione)
    st.session_state.tentativi.append((parola, fb))
    st.session_state.colori_tastiera = aggiorna_colori_tastiera(
        st.session_state.colori_tastiera, parola, fb
    )
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
    st.toast(f"💡 La lettera in posizione {pos+1} è **{lettera}**", icon="💡")

# =========================================================
# RENDER COMPONENTI
# =========================================================
def render_header():
    st.markdown(f'<div class="app-title">🟩 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Indovina la parola di 5 lettere in 6 tentativi</div>',
                unsafe_allow_html=True)

def render_player_badge():
    utente = st.session_state.utente
    st.markdown(f"""
        <div class="player-badge">
            <div>
                <div class="label">Giocatore</div>
                <div class="name">👤 {utente}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✏️ Modifica Nickname", use_container_width=True, key="btn_edit_nick"):
            st.session_state.modifica_nick = True
            st.rerun()
    with c2:
        if st.button("🔄 Cambia Giocatore", use_container_width=True, key="btn_change_player"):
            for k in ["utente","modalita","soluzione","tentativi","corrente",
                      "colori_tastiera","finita","vinto","punteggio_assegnato",
                      "modifica_nick","suggerimento_usato","suggerimento_pos",
                      "mostra_definizione"]:
                st.session_state.pop(k, None)
            st.rerun()

def render_griglia():
    righe_html = []
    sugg_pos = st.session_state.get("suggerimento_pos")
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
    st.markdown("".join(righe_html), unsafe_allow_html=True)

def render_tastiera():
    righe = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    for riga in righe:
        cols = st.columns(len(riga) + (2 if riga == "ZXCVBNM" else 0))
        idx = 0
        for lettera in riga:
            with cols[idx]:
                if st.button(lettera, key=f"key_{lettera}", use_container_width=True):
                    aggiungi_lettera(lettera)
            idx += 1
        if riga == "ZXCVBNM":
            with cols[idx]:
                if st.button("⌫", key="key_back", use_container_width=True):
                    rimuovi_lettera()
            idx += 1
            with cols[idx]:
                if st.button("✔️", key="key_enter", use_container_width=True):
                    invia_tentativo()
                    st.rerun()

def genera_risultato_condivisione():
    """Genera il testo da condividere con quadratini emoji."""
    emoji_map = {"correct": "🟩", "present": "🟨", "absent": "⬜"}
    righe = []
    for parola, fb in st.session_state.tentativi:
        righe.append("".join(emoji_map[c] for c in fb))
    n = len(st.session_state.tentativi)
    header = f"Parolario {n}/{MAX_TRIES}"
    return header + "\n" + "\n".join(righe)

def render_classifica():
    utenti = st.session_state.dati["utenti"]
    if not utenti:
        st.info("Nessun giocatore registrato ancora. Gioca la prima partita! 🎮")
        return
    ordinati = sorted(utenti.items(), key=lambda x: (-x[1]["punti"], -x[1]["vittorie"]))
    for pos, (nome, s) in enumerate(ordinati, start=1):
        medaglia = {1:"🥇", 2:"🥈", 3:"🥉"}.get(pos, f"{pos}.")
        io = " me" if nome == st.session_state.get("utente") else ""
        st.markdown(f"""
        <div class="leader-card{io}">
            <div class="leader-name">{medaglia} {nome}</div>
            <div class="leader-stats">
                🏆 <b>{s['punti']}</b> punti &nbsp;·&nbsp;
                ✅ {s['vittorie']}/{s['partite']} parole &nbsp;·&nbsp;
                🔥 Streak <b>{s['streak']}</b> (max {s['max_streak']})
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_coriandoli():
    """Inietta coriandoli animati con CSS."""
    colori = ["#6aaa64", "#c9b458", "#ffffff", "#e74c3c", "#3498db", "#f39c12"]
    pezzi = []
    for i in range(40):
        colore = random.choice(colori)
        left = random.randint(0, 100)
        delay = round(random.uniform(0, 1.5), 2)
        durata = round(random.uniform(2.5, 4.5), 2)
        pezzi.append(
            f'<div class="confetti-piece" style="left:{left}%; background:{colore}; '
            f'animation-delay:{delay}s; animation-duration:{durata}s; '
            f'width:{random.randint(8,14)}px; height:{random.randint(8,14)}px;"></div>'
        )
    html = '<div class="confetti-container">' + "".join(pezzi) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

# =========================================================
# SCHERMATA 1: SELEZIONE GIOCATORE
# =========================================================
def pagina_selezione():
    st.markdown(f'<div class="app-title">🟩 {APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Chi sta giocando?</div>', unsafe_allow_html=True)

    d = st.session_state.dati
    profili_esistenti = list(d["utenti"].keys())
    predefiniti = [p for p in PROFILI_PREDEFINITI if p in profili_esistenti]

    if predefiniti:
        for nome in predefiniti:
            if st.button(f"👤 {nome}", use_container_width=True, key=f"login_{nome}"):
                st.session_state.utente = nome
                st.session_state.dati = carica_dati()
                st.rerun()

    altri = [n for n in profili_esistenti if n not in PROFILI_PREDEFINITI]
    if altri:
        st.markdown('<div style="color:#a0a0a0;font-size:0.85rem;margin-top:1rem;">Altri profili</div>',
                    unsafe_allow_html=True)
        for nome in altri:
            if st.button(f"👤 {nome}", use_container_width=True, key=f"login_{nome}"):
                st.session_state.utente = nome
                st.rerun()

    st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
    n_ospiti = len([n for n in profili_esistenti if n.startswith("Ospite")])
    nome_default = f"Ospite {n_ospiti + 1}" if n_ospiti > 0 or not profili_esistenti else "Ospite"

    with st.expander("➕ Crea un nuovo profilo"):
        nuovo_nome = st.text_input("Nome nuovo profilo", placeholder="Es. Nonna, Zio, Ospite 1…",
                                    key="crea_nome")
        if st.button("Crea profilo", use_container_width=True, key="btn_crea"):
            nome_finale = nuovo_nome.strip() or nome_default
            if nome_finale in d["utenti"]:
                st.error(f"Il nome '{nome_finale}' è già in uso.")
            else:
                assicura_utente(nome_finale)
                st.session_state.utente = nome_finale
                st.rerun()

# =========================================================
# SCHERMATA 2: MENU MODALITÀ
# =========================================================
def pagina_menu():
    render_header()
    render_player_badge()
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    st.markdown('<h3 style="text-align:center;color:#fff;margin-bottom:1rem;">Scegli la modalità</h3>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        if st.button("📅 Parola del Giorno", use_container_width=True, key="m_daily"):
            reset_partita("daily")
            st.session_state.pagina = "gioco"
            st.rerun()
    with c2:
        if st.button("🎲 Gioca Ancora", use_container_width=True, key="m_unlimited"):
            reset_partita("unlimited")
            st.session_state.pagina = "gioco"
            st.rerun()

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        if st.button("🏆 Classifica", use_container_width=True, key="m_leader"):
            st.session_state.pagina = "classifica"
            st.rerun()
    with c2:
        if st.button("📊 Le Mie Statistiche", use_container_width=True, key="m_stats"):
            st.session_state.pagina = "statistiche"
            st.rerun()

# =========================================================
# SCHERMATA 3: GIOCO
# =========================================================
def pagina_gioco():
    render_header()
    render_player_badge()
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    titolo_mod = "📅 Parola del Giorno" if st.session_state.modalita == "daily" else "🎲 Gioco Illimitato"
    st.markdown(f'<h3 style="text-align:center;color:#fff;">{titolo_mod}</h3>',
                unsafe_allow_html=True)

    render_griglia()
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    # Fine partita
    if st.session_state.finita:
        if st.session_state.vinto:
            n = len(st.session_state.tentativi)
            punti = calcola_punti(n)
            if not st.session_state.punteggio_assegnato:
                nuovi_badges = registra_vittoria(st.session_state.utente, punti,
                                                  st.session_state.modalita, n)
                st.session_state.punteggio_assegnato = True
                st.session_state.nuovi_badges = nuovi_badges
                st.balloons()
                render_coriandoli()
            render_nuovi_badges(st.session_state.get("nuovi_badges", []))
            st.success(f"🎉 Bravissimo! Indovinato in {n} tentativi — **+{punti} punti!**")

            # Pulsante copia risultato
            risultato = genera_risultato_condivisione()
            st.code(risultato, language=None)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📋 Copia per WhatsApp", use_container_width=True, key="copy_whats"):
                    st.toast("Copiato! Incollalo in WhatsApp 💬", icon="✅")
            with c2:
                if st.button("🔍 Definizione", use_container_width=True, key="def_btn"):
                    st.session_state.mostra_definizione = True
                    st.rerun()

            if st.session_state.get("mostra_definizione"):
                parola = st.session_state.soluzione
                st.info(f"**{parola}** — Cerca la definizione su "
                        f"[Treccani](https://www.treccani.it/vocabolario/{parola.lower()}/) "
                        f"o [Wikizionario](https://it.wiktionary.org/wiki/{parola.lower()})")
        else:
            if not st.session_state.punteggio_assegnato:
                nuovi_badges = registra_sconfitta(st.session_state.utente, st.session_state.modalita)
                st.session_state.punteggio_assegnato = True
                st.session_state.nuovi_badges = nuovi_badges
            render_nuovi_badges(st.session_state.get("nuovi_badges", []))
            st.error(f"😢 Peccato! La parola era: **{st.session_state.soluzione}**")

            risultato = genera_risultato_condivisione()
            st.code(risultato, language=None)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📋 Copia per WhatsApp", use_container_width=True, key="copy_whats_lose"):
                    st.toast("Copiato! Incollalo in WhatsApp 💬", icon="✅")
            with c2:
                if st.button("🔍 Definizione", use_container_width=True, key="def_btn_lose"):
                    st.session_state.mostra_definizione = True
                    st.rerun()

            if st.session_state.get("mostra_definizione"):
                parola = st.session_state.soluzione
                st.info(f"**{parola}** — Cerca la definizione su "
                        f"[Treccani](https://www.treccani.it/vocabolario/{parola.lower()}/) "
                        f"o [Wikizionario](https://it.wiktionary.org/wiki/{parola.lower()})")

        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Nuova parola", use_container_width=True, key="end_new"):
                reset_partita("unlimited")
                st.rerun()
        with c2:
            if st.button("🏠 Menu", use_container_width=True, key="end_menu"):
                st.session_state.pagina = "menu"
                for k in ["modalita","soluzione","tentativi","corrente",
                          "colori_tastiera","finita","vinto","punteggio_assegnato",
                          "suggerimento_usato","suggerimento_pos","mostra_definizione",
                          "nuovi_badges"]:
                    st.session_state.pop(k, None)
                st.rerun()
        return

    # Input fisico
    with st.form("input_form", clear_on_submit=True):
        col_input, col_btn = st.columns([4,1])
        with col_input:
            testo = st.text_input(
                "Parola", value="", max_chars=WORD_LEN, key="input_fisico",
                label_visibility="collapsed",
                placeholder="Scrivi o usa la tastiera…",
            )
        with col_btn:
            inviato = st.form_submit_button("✔️", use_container_width=True)
    if inviato and testo:
        st.session_state.corrente = testo.upper().strip()
        invia_tentativo()
        st.rerun()

    # Suggerimento
    if not st.session_state.suggerimento_usato:
        if st.button("💡 Suggerimento (1 sola volta)", use_container_width=True, key="hint_btn"):
            usa_suggerimento()
            st.rerun()
    else:
        st.caption("💡 Suggerimento già usato in questa partita")

    render_tastiera()
    st.caption(f"Tentativi: {len(st.session_state.tentativi)}/{MAX_TRIES}")

# =========================================================
# SCHERMATA 4: CLASSIFICA
# =========================================================
def pagina_classifica():
    render_header()
    st.markdown('<h3 style="text-align:center;color:#fff;">🏆 Classifica</h3>', unsafe_allow_html=True)
    st.markdown('<div class="live-label"><span class="live-dot"></span>Aggiornamento automatico ogni 30s</div>',
                unsafe_allow_html=True)
    render_classifica()
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    if st.button("⬅️ Torna al Menu", use_container_width=True, key="back_menu"):
        st.session_state.pagina = "menu"
        st.rerun()

# =========================================================
# SCHERMATA 5: STATISTICHE PERSONALI
# =========================================================
def pagina_statistiche():
    render_header()
    utente = st.session_state.utente
    st.markdown(f'<h3 style="text-align:center;color:#fff;">📊 Statistiche di {utente}</h3>',
                unsafe_allow_html=True)

    d = st.session_state.dati
    u = d["utenti"].get(utente)
    if not u:
        st.info("Nessuna partita registrata ancora. Gioca per vedere le statistiche!")
        if st.button("⬅️ Torna al Menu", use_container_width=True, key="back_from_stats"):
            st.session_state.pagina = "menu"
            st.rerun()
        return

    # Riepilogo
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-item"><div class="stat-value">{u["partite"]}</div>'
                    f'<div class="stat-label">Partite</div></div>', unsafe_allow_html=True)
    with c2:
        perc = round(100 * u["vittorie"] / u["partite"]) if u["partite"] > 0 else 0
        st.markdown(f'<div class="stat-item"><div class="stat-value">{perc}%</div>'
                    f'<div class="stat-label">Vittorie</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-item"><div class="stat-value">{u["streak"]}</div>'
                    f'<div class="stat-label">Streak</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-item"><div class="stat-value">{u["max_streak"]}</div>'
                    f'<div class="stat-label">Max Streak</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    # Grafico distribuzione
    st.markdown('<h4 style="color:#fff;">📈 Distribuzione Tentativi</h4>', unsafe_allow_html=True)
    dist = u.get("tentativi_distribuzione", [0]*6)
    if any(dist):
        import pandas as pd
        df = pd.DataFrame({
            "Tentativi": [f"{i+1}°" for i in range(6)],
            "Volte": dist,
        })
        st.bar_chart(df, x="Tentativi", y="Volte", color="#6aaa64")
    else:
        st.caption("Nessuna vittoria ancora. Indovina una parola per vedere il grafico!")

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    # Badge
    st.markdown('<h4 style="color:#fff;">🏅 Trofei</h4>', unsafe_allow_html=True)
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

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    if st.button("⬅️ Torna al Menu", use_container_width=True, key="back_from_stats2"):
        st.session_state.pagina = "menu"
        st.rerun()

# =========================================================
# SCHERMATA 6: MODIFICA NICKNAME
# =========================================================
def pagina_modifica_nick():
    render_header()
    st.markdown('<h3 style="text-align:center;color:#fff;">✏️ Modifica Nickname</h3>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;color:#a0a0a0;">Nome attuale: <b style="color:#fff;">'
                f'{st.session_state.utente}</b></p>', unsafe_allow_html=True)

    nuovo = st.text_input("Nuovo nickname", value="", max_chars=20, key="nick_input",
                          placeholder="Scrivi il nuovo nome…")

    c1, c2 = st.columns(2)
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
                st.success(f"Nickname aggiornato in '{nome_pulito}'!")
                st.rerun()
            else:
                st.error("Nome già in uso da un altro giocatore.")
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
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# Auto-refresh intelligente
if st.session_state.utente and st.session_state.pagina in PAGINE_CON_REFRESH:
    st_autorefresh(interval=REFRESH_MS, key="auto_refresh")
    st.session_state.dati = carica_dati()

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