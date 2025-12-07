import csv
import unicodedata

import streamlit as st
from cltk.nlp import NLP

# ----------------- CONFIGURAZIONE PAGINA ----------------- #

st.set_page_config(
    page_title="Lemmatizzatore per il Vocabolario Greco-Italiano Olivetti",
    layout="centered",
)

# ----------------- STILE: TUTTO TIMES NEW ROMAN + ROSSO SCURO ----------------- #

st.markdown(
    """
    <style>

    /* FONT UNICO PER TUTTO */
    html, body, [class^="css"], div, p, span, h1, h2, h3, h4, input, label, textarea {
        font-family: "Times New Roman", serif !important;
        color: #2b0000 !important;
    }

    input {
        border: 1px solid #7a0000 !important;
        border-radius: 2px !important;
        padding: 6px 8px;
    }

    input::placeholder {
        font-family: "Times New Roman", serif !important;
        color: #7a0000 !important;
    }

    a {
        color: #7a0000 !important;
        text-decoration: underline;
        font-size: 1.05rem !important;
    }

    .main .block-container {
        max-width: 720px !important;
        padding-top: 2.5rem !important;
    }

    hr {
        border: none;
        border-top: 1px solid #bfbfbf;
        margin: 2rem 0;
    }

    .panel {
        border: 1px solid #bfbfbf;
        padding: 1.8rem 2rem;
        background-color: #ffffff;
    }

    /* BOX RISULTATI */
    .result-gold, .result-acceptable, .result-external {
        padding-left: 0.9rem;
        margin: 1.6rem 0;
        border-left-width: 3px;
        border-left-style: solid;
    }

    .result-gold { border-left-color: #7a0000; }
    .result-acceptable { border-left-color: #a46b00; }
    .result-external { border-left-color: #4b4b4b; }

    .lemma {
        font-size: 1.6rem;
        font-weight: bold;
        color: #7a0000;
        margin-bottom: 0.4rem;
    }

    .msg {
        padding-left: 0.7rem;
        margin: 1rem 0;
        border-left: 3px solid #7a0000;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------- HEADER ----------------- #

st.markdown("<div class='panel'>", unsafe_allow_html=True)

st.markdown(
    """
    <h1 style="
        font-size: 2.6rem;
        font-weight: bold;
        margin-top: 0.2rem;
        margin-bottom: 1.2rem;
        color:#7a0000;
    ">
        Lemmatizzatore per il Vocabolario Greco-Italiano Olivetti
    </h1>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <p>
    Prototipo di lemmatizzatore per il greco antico, costruito a partire dalle forme politematiche di alcuni verbi greci e dai loro rispettivi lemmi, ricavati dal Vocabolario Greco-Italiano Olivetti.
    </p>

    <p>Il sistema restituisce tre tipi di risultati:</p>

    <p>
    GOLD: forma riconosciuta con certezza, perché presente nel dataset curato.<br>
    ACCEPTABLE: lemma suggerito automaticamente e compatibile con il vocabolario.<br>
    EXTERNAL: lemma suggerito automaticamente, non necessariamente presente nel vocabolario e quindi non validato dal dataset curato.
    </p>
    """,
    unsafe_allow_html=True,
)

# ----------------- FUNZIONI DI BASE ----------------- #

def normalizza_greco(parola: str) -> str:
    if not parola:
        return ""
    parola = parola.strip().lower()
    dec = unicodedata.normalize("NFD", parola)
    senza = "".join(c for c in dec if unicodedata.category(c) != "Mn")
    return unicodedata.normalize("NFC", senza)


def contiene_solo_latino(parola: str) -> bool:
    return parola.isascii() and parola.isalpha()


def carica_csv(percorso: str):
    """
    Legge forme_lemmi.csv con colonne:
      forma;lemma;analisi;url
    Restituisce:
      - diz_forme: {forma_norm: [ {lemma, analisi, url}, ... ]}
      - lemmi: set di tutti i lemmi presenti
    """
    diz = {}
    lemmi = set()

    with open(percorso, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        # eventuale intestazione
        next(reader, None)

        for riga in reader:
            if len(riga) < 2:
                continue

            forma = riga[0]
            lemma = riga[1]
            analisi = riga[2] if len(riga) >= 3 else ""
            url = riga[3] if len(riga) >= 4 else ""

            forma_norm = normalizza_greco(forma)
            voce = {"lemma": lemma, "analisi": analisi, "url": url}

            lemmi.add(lemma)

            if forma_norm not in diz:
                diz[forma_norm] = []
            if voce not in diz[forma_norm]:
                diz[forma_norm].append(voce)

    return diz, lemmi


@st.cache_resource
def get_cltk():
    return NLP(language="ancient_greek", backend="stanza")


def cltk_lemmas(forma: str):
    nlp = get_cltk()
    doc = nlp.analyze(text=forma)
    if not hasattr(doc, "words") or doc.words is None:
        return []
    return sorted({w.lemma for w in doc.words if getattr(w, "lemma", None)})


@st.cache_data
def load_data():
    try:
        return carica_csv("forme_lemmi.csv")
    except FileNotFoundError:
        return {}, set()


diz_forme, lemmi_olivetti = load_data()

# ----------------- SEZIONE RICERCA ----------------- #

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    """
    <h2 style="font-size:2rem; margin-bottom:1rem; color:#7a0000;">
        Ricerca per forma flessa
    </h2>
    """,
    unsafe_allow_html=True,
)

forma_input = st.text_input(
    "Inserisci una forma verbale greca:",
    placeholder="es. εἶπον, ἤνεγκα, ᾕρηκα…",
    key="forma_input",
)

# ----------------- LOGICA DI RICERCA ----------------- #

if forma_input:

    if contiene_solo_latino(forma_input):
        st.markdown(
            "<div class='msg'>La forma inserita sembra digitata con caratteri latini. Inserisci la forma in greco.</div>",
            unsafe_allow_html=True,
        )

    else:
        forma_norm = normalizza_greco(forma_input)
        risultati = diz_forme.get(forma_norm)

        # --------- CASO GOLD --------- #
        if risultati:

            if len(risultati) == 1:
                v = risultati[0]

                st.markdown(
                    f"""
                    <div class="result-gold">
                        <p><strong>Risultato GOLD</strong></p>

                        <div class="lemma">{v['lemma']}</div>

                        {f"<p><i>{v['analisi']}</i></p>" if v['analisi'] else ""}

                        {(
                            "<p style='margin-top:0.6rem;'>"
                            f"<a href='{v['url']}' target='_blank'>Vai alla voce del vocabolario Olivetti</a>"
                            "</p>"
                         ) if v.get('url') else ""
                        }
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:
                # Più voci GOLD per la stessa forma
                html = """
                <div class="result-gold">
                    <p><strong>Risultati GOLD</strong></p>
                """
                for v in risultati:
                    html += "<div style='margin-bottom:0.8rem;'>"
                    html += f"<div class='lemma'>{v['lemma']}</div>"
                    if v["analisi"]:
                        html += f"<p><i>{v['analisi']}</i></p>"
                    if v.get("url"):
                        html += (
                            "<p style='margin-top:0.2rem;'>"
                            f"<a href='{v['url']}' target='_blank'>Vai alla voce del vocabolario Olivetti</a>"
                            "</p>"
                        )
                    html += "</div>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)

        # --------- NESSUN GOLD → CLTK --------- #
        else:
            st.markdown(
                "<div class='msg'>Nessun risultato GOLD nel dataset curato. Analisi automatica avviata.</div>",
                unsafe_allow_html=True,
            )

            lemmi_auto = cltk_lemmas(forma_input)

            if not lemmi_auto:
                st.markdown(
                    "<div class='msg'>Il motore automatico non ha proposto alcun lemma.</div>",
                    unsafe_allow_html=True,
                )
            else:
                acc = [l for l in lemmi_auto if l in lemmi_olivetti]
                ext = [l for l in lemmi_auto if l not in lemmi_olivetti]

                if acc:
                    html = "<div class='result-acceptable'><p><strong>Suggerimenti ACCEPTABLE</strong></p><ul>"
                    html += "".join(f"<li>{l}</li>" for l in acc)
                    html += "</ul></div>"
                    st.markdown(html, unsafe_allow_html=True)

                if ext:
                    html = "<div class='result-external'><p><strong>Suggerimenti EXTERNAL</strong></p><ul>"
                    html += "".join(f"<li>{l}</li>" for l in ext)
                    html += "</ul></div>"
                    st.markdown(html, unsafe_allow_html=True)

                    st.markdown(
                        "<div class='msg'>I lemmi EXTERNAL non risultano nel vocabolario e sono suggerimenti automatici.</div>",
                        unsafe_allow_html=True,
                    )

# ----------------- NOTE FINALI ----------------- #

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    """
    <h2 style="color:#7a0000;">Note sul prototipo</h2>

    <p>Il livello GOLD è basato su un dataset curato, costruito attraverso un generatore morfologico Python e controllo manuale dei lemmi.</p>

    <p>Il Vocabolario Greco-Italiano Olivetti fornisce il lemmario di riferimento e il collegamento lessicografico (URL), ma non contiene forme flesse.</p>

    <p>Il motore automatico (CLTK) è usato come supporto: i suoi suggerimenti sono classificati come ACCEPTABLE se compatibili con il lemario del dataset, altrimenti come EXTERNAL.</p>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)
