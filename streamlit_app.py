import streamlit as st
import pandas as pd
import unicodedata

# ---------------- UTIL ----------------
def purificar(texto):
    if not texto:
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.strip()

# ---------------- STREAMLIT ----------------
st.title("Orçamento de Exames")

clinica = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"])

exames_texto = st.text_area("Cole os exames:")

if st.button("GERAR ORÇAMENTO"):
    linhas = exames_texto.splitlines()
    total = 0
    resultado = ""

    # carrega tabela só para US
    if clinica == "Sabry":
        df = pd.read_csv("TABELA_SABRY_ATUALIZADA 160126.csv")
    else:
        df = pd.read_csv("TABELA_LABCLINICA_ATUALIZADA160126.csv")

    df["NOME_PURIFICADO"] = df["NOME"].apply(purificar)

    for linha in linhas:
        termo = purificar(linha)

        # -------- RESSONANCIA (REGRA FIXA) --------
        if "RESSONANCIA" in termo:
            preco = 545.00
            total += preco
            resultado += f"✅ RESSONÂNCIA: R$ {preco:.2f}\n"
            continue

        # -------- TOMOGRAFIA / TC (REGRA FIXA) --------
        if "TOMOGRAFIA" in termo or termo.startswith("TC"):
            preco = 165.00
            total += preco
            resultado += f"✅ TOMOGRAFIA: R$ {preco:.2f}\n"
            continue

        # -------- ULTRASSOM (BUSCA SIMPLES NA TABELA) --------
        if "US" in termo or "ULTRA" in termo:
            achado = df[df["NOME_PURIFICADO"].str.contains("ULTRA", na=False)]
            if not achado.empty:
                row = achado.iloc[0]
                preco = float(row["VALOR"])
                total += preco
                resultado += f"✅ ULTRASSOM: R$ {preco:.2f}\n"
            else:
                resultado += f"❌ {linha}: não encontrado\n"
            continue

        # -------- NADA ENCONTRADO --------
        resultado += f"❌ {linha}: não reconhecido\n"

    st.markdown("### Orçamento Saúde Dirceu")
    st.text(resultado)
    st.markdown(f"### Total: R$ {total:.2f}")

    st.button("Enviar para WhatsApp")
