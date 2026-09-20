# genera_parole.py
"""
Generatore automatico di parole.py per Parola Mia.

Prova prima a scaricare il dizionario da GitHub.
Se fallisce, usa il file locale 'parole_uniche.txt'.

Uso: python genera_parole.py
"""

import urllib.request
import re
import sys
import os

URL = "https://raw.githubusercontent.com/napolux/paroleitaliane/master/paroleitaliane/parole_uniche.txt"
FILE_LOCALE = "parole_uniche.txt"

# Parole comuni usate come "parola del giorno" (le più semplici e familiari)
SOLUZIONI_PREFERITE = [
    "ABITO","ACQUA","AEREO","AGLIO","ALBUM","ALTRO","AMACA","AMICO","AMORE",
    "ANIMA","ARENA","AROMA","ASINO","ASTRO","ATOMO","AVARO","AVVIO","BAGNO",
    "BALLO","BANCO","BARCA","BASSO","BECCO","BIRRA","BOCCA","BORSA","BOSCO",
    "BRAVO","BUONO","CALDO","CALMA","CAMPO","CANTO","CARNE","CARTA","CASCO",
    "CAUSA","CEDRO","CENNO","CIELO","CIFRA","COCCO","COLPO","CORPO","CORSA",
    "CORTO","COSTA","CREDO","CUORE","DANZA","DENTE","DIETA","DISCO","DOLCE",
    "DONNA","DORSO","DRAGO","EDERA","EPOCA","FALCO","FESTA","FIATO","FIORE",
    "FONDO","FORMA","FORNO","FORTE","FRASE","FRENO","FUOCO","GATTO","GENTE",
    "GESSO","GIOCO","GLOBO","GRANO","GRIDO","GUSTO","ISOLA","LAMPO","LATTE",
    "LEGNO","LENTO","LETTO","LIBRO","LINEA","LITRO","LUOGO","LUSSO","MADRE",
    "MAGIA","MAGRO","MANGO","MANTO","MAREA","MASSA","MATTO","MEDIA","MENTE",
    "MERLO","METRO","MEZZO","MIELE","MISTO","MONDO","MONTE","MORSO","MOSCA",
    "MOTTO","MUCCA","MUSEO","NERVO","NOTTE","NUOTO","OMBRA","ONORE","OPERA",
    "PADRE","PAESE","PALCO","PANDA","PARCO","PARTO","PASSO","PASTA","PASTO",
    "PENNA","PERLA","PESCA","PESCE","PEZZO","PIANO","PIGRO","PINNA","PISTA",
    "PIZZA","POETA","PONTE","PORRO","PORTO","POSTA","POZZO","PRATO","PRIMO",
    "PULCE","PUNTO","QUOTA","RADIO","RAGNO","RAZZA","REGNO","RESTO","RICCO",
    "RITMO","ROBOT","ROSSO","RUOTA","SALTO","SASSO","SCALA","SCENA","SCUOLA",
    "SEGNO","SENSO","SERRA","SETTE","SFIDA","SOGNO","SOLCO","SONNO","SORSO",
    "SPADA","SPAGO","SPIGA","SPINA","SPOSA","STELLA","STILE","SUONO","TACCO",
    "TANTO","TARDI","TASSO","TEMPO","TENDA","TENUE","TERRA","TESTO","TETTO",
    "TIGRE","TORRE","TORTA","TOSSE","TRENO","TRONO","TROTA","TURBO","UDITO",
    "UMORE","UNICO","USATO","VACCA","VASCA","VENTO","VERBO","VERDE","VERME",
    "VERSO","VETRO","VILLA","VIOLA","VIRUS","VISTA","VOLPE","VOLTA","VUOTO",
    "ZAINO","ZEBRA","ZUCCA","ZUPPA",
]


def scarica_online(url: str) -> str | None:
    """Prova a scaricare il dizionario da GitHub."""
    print("📥 Provo a scaricare il dizionario da GitHub...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            testo = r.read().decode("utf-8")
        print(f"✅ Scaricate {len(testo.splitlines())} righe.")
        return testo
    except Exception as e:
        print(f"⚠️  Scaricamento fallito: {e}")
        return None


def leggi_locale(path: str) -> str | None:
    """Legge il dizionario dal file locale."""
    if not os.path.exists(path):
        return None
    print(f"📂 Leggo il dizionario locale '{path}'...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            testo = f.read()
        print(f"✅ Lette {len(testo.splitlines())} righe.")
        return testo
    except Exception as e:
        print(f"❌ Errore lettura file: {e}")
        return None


def filtra_parole(testo: str) -> set:
    """Tiene solo parole di 5 lettere, solo A-Z (no accenti, apostrofi, ecc)."""
    print("🔍 Filtro le parole di 5 lettere...")
    valide = set()
    for riga in testo.splitlines():
        p = riga.strip().upper()
        # Deve essere lunga esattamente 5 e contenere solo lettere A-Z
        if len(p) == 5 and re.match(r"^[A-Z]+$", p):
            valide.add(p)
    print(f"✅ Trovate {len(valide)} parole valide di 5 lettere.")
    return valide


def costruisci_soluzioni(parole_valide: set) -> list:
    """Tiene solo le soluzioni preferite che esistono davvero nel dizionario."""
    print("🎯 Costruisco la lista soluzioni...")
    soluzioni = [p for p in SOLUZIONI_PREFERITE if p in parole_valide]
    # Rimuovi duplicati mantenendo l'ordine
    viste = set()
    soluzioni_pulite = []
    for p in soluzioni:
        if p not in viste:
            viste.add(p)
            soluzioni_pulite.append(p)
    print(f"✅ Soluzioni finali: {len(soluzioni_pulite)}")
    return soluzioni_pulite


def scrivi_parole_py(parole_valide: set, soluzioni: list, filename: str = "parole.py"):
    """Scrive il file parole.py con le due liste."""
    print(f"💾 Scrivo {filename}...")
    valide_ordinate = sorted(parole_valide)
    soluzioni_ordinate = sorted(soluzioni)

    def formatta_lista(lst, per_riga=12):
        righe = []
        for i in range(0, len(lst), per_riga):
            blocco = lst[i:i + per_riga]
            righe.append("    " + ", ".join(f'"{p}"' for p in blocco) + ",")
        return "\n".join(righe)

    contenuto = f'''# parole.py
"""
Dizionario di parole italiane di 5 lettere per Parola Mia.
⚠️ File generato automaticamente da genera_parole.py — non modificare a mano.
Fonte: https://github.com/napolux/paroleitaliane
Totale parole valide: {len(parole_valide)}
Totale soluzioni: {len(soluzioni)}
"""

# =========================================================
# SOLUZIONI — parole comuni usate come "parola del giorno"
# =========================================================
PAROLE_SOLUZIONE = [
{formatta_lista(soluzioni_ordinate)}
]

# =========================================================
# VALIDE — tutte le parole accettate come tentativo
# =========================================================
PAROLE_VALIDE = [
{formatta_lista(valide_ordinate)}
]
'''

    with open(filename, "w", encoding="utf-8") as f:
        f.write(contenuto)
    print(f"✅ File {filename} creato con successo!")
    print(f"   → {len(soluzioni)} soluzioni")
    print(f"   → {len(parole_valide)} parole valide")


def main():
    # 1) Prova online
    testo = scarica_online(URL)

    # 2) Fallback su file locale
    if testo is None:
        testo = leggi_locale(FILE_LOCALE)

    # 3) Se non c'è né online né locale, errore
    if testo is None:
        print()
        print("❌ Impossibile ottenere il dizionario.")
        print(f"   Scarica manualmente questo file:")
        print(f"   {URL}")
        print(f"   e salvalo come '{FILE_LOCALE}' nella stessa cartella di app.py.")
        sys.exit(1)

    # 4) Filtra e scrivi
    valide = filtra_parole(testo)
    soluzioni = costruisci_soluzioni(valide)
    scrivi_parole_py(valide, soluzioni)

    print()
    print("🎉 Fatto! Ora riavvia l'app con: streamlit run app.py")


if __name__ == "__main__":
    main()