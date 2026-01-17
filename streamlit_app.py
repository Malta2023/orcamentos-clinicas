import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

def purificar(txt):
    if not isinstance(txt, str):
        return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.strip()

def score_busca(termo, nome):
    pontos = 0
    termo_words = termo.split()
    nome_words = nome.split()

    for w in termo_words:
        if w in nome_words:
            pontos += 2
        elif w in nome:
            pontos += 1

    return pontos

st.title("🏥 Orçamento Saúde Dirceu")

clinica = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames:")

if st.button("✨ GERAR ORÇAMENTO"):
    url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
    df = pd.read_csv(url, dtype=str).fillna("")
    df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)

    linhas = re.split(r"\n|,|;", exames_raw)
    total = 0
    texto = f"*Orçamento Saúde Dirceu ({'S' if clinica=='Sabry' else 'L'})*\n\n"

    for linha in linhas:
        original = linha.strip()
        if not original:
            continue

        termo = purificar(original)

        # sinônimos
        if termo in ["GLICEMIA", "GLICOSE"]:
            termo = "GLICOSE"

        melhor_pontuacao = 0
        melhor = None

        for _, row in df.iterrows():
            nome_tab = row["NOME_PURIFICADO"]

            # 🚫 BLOQUEIO TOTAL DE ANGIO
            if "ANGIO" in nome_tab and "ANGIO" not in termo:
                continue

            pontos = score_busca(termo, nome_tab)
            if pontos > melhor_pontuacao:
                melhor_pontuacao = pontos
                melhor = row

        if melhor is not None and melhor_pontuacao > 0:
            nome = melhor.iloc[0]
            p = melhor.iloc[1].replace("R$", "").replace(".", "").replace(",", ".")
            preco = float(re.findall(r"\d+\.\d+|\d+", p)[0])
            total += preco
            texto += f"✅ {nome}: R$ {preco:.2f}\n"
        else:
            texto += f"❌ {original}: não encontrado\n"

    texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"

    st.code(texto)

    st.markdown(
        f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" '
        f'style="background:#25D366;color:white;padding:15px;border-radius:10px;'
        f'display:block;text-align:center;font-weight:bold;text-decoration:none;">'
        f'📲 ENVIAR PARA WHATSAPP</a>',
        unsafe_allow_html=True
    )
