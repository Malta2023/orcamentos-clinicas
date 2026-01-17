import streamlit as st
import pandas as pd
import unicodedata
from urllib.parse import quote

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

# ---------------- FUNÇÃO ----------------
def purificar(texto):
    if not texto:
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.strip()

# ---------------- APP ----------------
st.title("🏥 Orçamento Saúde Dirceu")

clinica = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_texto = st.text_area("Cole os exames:")

if st.button("✨ GERAR ORÇAMENTO"):
    url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
    df = pd.read_csv(url, dtype=str).fillna("")
    df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)

    linhas = exames_texto.splitlines()
    total = 0
    texto_final = f"*Orçamento Saúde Dirceu ({'S' if clinica == 'Sabry' else 'L'})*\n\n"

    for linha in linhas:
        termo = purificar(linha)

        # -------- RESSONÂNCIA (FIXO) --------
        if "RESSONANCIA" in termo:
            preco = 545.00
            total += preco
            texto_final += f"✅ RESSONÂNCIA: R$ {preco:.2f}\n"
            continue

        # -------- TOMOGRAFIA / TC (FIXO) --------
        if "TOMOGRAFIA" in termo or termo.startswith("TC"):
            preco = 165.00
            total += preco
            texto_final += f"✅ TOMOGRAFIA: R$ {preco:.2f}\n"
            continue

        # -------- ULTRASSOM (TABELA) --------
        if "US" in termo or "ULTRA" in termo:
            achado = df[df["NOME_PURIFICADO"].str.contains("ULTRA", na=False)]
            if not achado.empty:
                row = achado.iloc[0]
                preco = float(row.iloc[1].replace(",", "."))
                total += preco
                texto_final += f"✅ ULTRASSOM: R$ {preco:.2f}\n"
            else:
                texto_final += f"❌ {linha}: não encontrado\n"
            continue

        texto_final += f"❌ {linha}: não reconhecido\n"

    texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"

    st.code(texto_final)

    st.markdown(
        f'<a href="https://wa.me/?text={quote(texto_final)}" target="_blank" '
        f'style="background:#25D366;color:white;padding:15px;border-radius:10px;'
        f'display:block;text-align:center;font-weight:bold;text-decoration:none;">'
        f'📲 ENVIAR PARA WHATSAPP</a>',
        unsafe_allow_html=True
    )
