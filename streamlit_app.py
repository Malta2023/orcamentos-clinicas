import streamlit as st
import pandas as pd
import unicodedata

# ---------- FUNÇÕES ----------
def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.strip()

def padronizar_exame(exame):
    e = normalizar(exame)

    if "glicose" in e or "glicemia" in e:
        return "GLICOSE"

    if "ressonancia" in e:
        return "RESSONANCIA"

    if e.startswith("tc") or "tomografia" in e:
        return "TOMOGRAFIA"

    if e.startswith("us") or "ultrassom" in e or "ultrasonografia" in e:
        return "ULTRASSONOGRAFIA"

    return exame.upper()

def buscar_preco(df, exame_padrao):
    df["exame_norm"] = df["EXAME"].apply(normalizar)

    if exame_padrao == "RESSONANCIA":
        filtro = df[df["exame_norm"].str.contains("ressonancia")]
    elif exame_padrao == "TOMOGRAFIA":
        filtro = df[df["exame_norm"].str.contains("tomografia")]
    elif exame_padrao == "ULTRASSONOGRAFIA":
        filtro = df[df["exame_norm"].str.contains("ultrassom")]
    elif exame_padrao == "GLICOSE":
        filtro = df[df["exame_norm"].str.contains("glicose")]
    else:
        filtro = df[df["exame_norm"].str.contains(normalizar(exame_padrao))]

    if filtro.empty:
        return None

    linha = filtro.iloc[0]
    return float(linha["VALOR"])

# ---------- APP ----------
st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")
st.title("Orçamento Saúde Dirceu")

tabela = st.selectbox("Escolha a tabela", ["Sabry", "Labclinica"])

if tabela == "Sabry":
    df = pd.read_csv("TABELA_SABRY_ATUALIZADA 160126.csv")
else:
    df = pd.read_csv("TABELA_LABCLINICA_ATUALIZADA160126.csv")

entrada = st.text_area(
    "Digite os exames (um por linha)",
    placeholder="Ex: \nressonancia\ntc\nus\nglicemia"
)

if st.button("Gerar orçamento"):
    exames = [e for e in entrada.split("\n") if e.strip()]
    total = 0.0

    st.markdown("### Orçamento")

    for exame in exames:
        exame_padrao = padronizar_exame(exame)
        preco = buscar_preco(df, exame_padrao)

        if preco is None:
            st.write(f"❌ {exame}: não encontrado")
        else:
            st.write(f"✅ {exame_padrao}: R$ {preco:.2f}")
            total += preco

    st.markdown(f"### 💰 Total: R$ {total:.2f}")
