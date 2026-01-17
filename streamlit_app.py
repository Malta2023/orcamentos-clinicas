import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

# ================= FUNÇÕES BASE =================

def purificar(texto):
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = texto.upper()
    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

# ================= SINÔNIMOS =================

SINONIMOS = {
    "CRANIO": ["CRANIO", "CABECA", "ENCEFALO"],
    "COLUNA": ["COLUNA", "CERVICAL", "LOMBAR", "DORSAL", "COSTAS"],
    "ABDOMEN": ["ABDOMEN", "ABDOME", "BARRIGA"],
    "TORAX": ["TORAX", "PEITO"],
    "PELVE": ["PELVE", "BACIA"],
    "JOELHO": ["JOELHO"],
    "OMBRO": ["OMBRO"],
}

def detectar_regiao(texto):
    for regiao, palavras in SINONIMOS.items():
        for p in palavras:
            if p in texto:
                return regiao
    return None

# ================= BUSCA =================

def buscar_exame(df, tipo, regiao):
    df_temp = df.copy()

    # remove lixo
    df_temp = df_temp[~df_temp['NOME_PURIFICADO'].str.contains(
        "TAXA|URG|URGENCIA|ANGIO|CONTRASTE", na=False
    )]

    if tipo == "RM":
        df_temp = df_temp[df_temp['NOME_PURIFICADO'].str.contains("RESSON", na=False)]
    elif tipo == "TC":
        df_temp = df_temp[df_temp['NOME_PURIFICADO'].str.contains("TOMOGRAFIA", na=False)]
    elif tipo == "US":
        df_temp = df_temp[df_temp['NOME_PURIFICADO'].str.contains("ULTRA", na=False)]

    if regiao:
        df_temp = df_temp[df_temp['NOME_PURIFICADO'].str.contains(regiao, na=False)]

    if df_temp.empty:
        return None

    df_temp['tam'] = df_temp['NOME_PURIFICADO'].str.len()
    return df_temp.sort_values('tam').iloc[0]

# ================= URLs =================

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LAB = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

# ================= APP =================

st.title("🏥 Senhor APP")

clinica = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
texto = st.text_area("Cole os exames:", height=180)

if st.button("✨ GERAR ORÇAMENTO"):
    if not texto:
        st.warning("Cole pelo menos um exame.")
    else:
        url = URL_SABRY if clinica == "Sabry" else URL_LAB
        df = pd.read_csv(url, dtype=str).fillna("")
        df['NOME_PURIFICADO'] = df.iloc[:, 0].apply(purificar)

        linhas = re.split(r'\n|,| E | & | \+ | / ', texto)

        total = 0.0
        saida = f"*Orçamento Saúde Dirceu*\n\n"

        for item in linhas:
            original = item.strip()
            if not original:
                continue

            termo = purificar(original)
            tipo = None

            if "RESSONANCIA" in termo or termo == "RM":
                tipo = "RM"
                preco_fixo = 545.00
            elif "TOMOGRAFIA" in termo or termo == "TC":
                tipo = "TC"
                preco_fixo = 165.00
            elif "ULTRASSOM" in termo or "ULTRASONOGRAFIA" in termo or termo == "US":
                tipo = "US"
                preco_fixo = None
            else:
                saida += f"❌ {original}: não identificado\n"
                continue

            regiao = detectar_regiao(termo)

            if not regiao:
                saida += f"⚠️ {original}: informe a região\n"
                continue

            res = buscar_exame(df, tipo, regiao)

            if res is None:
                saida += f"❌ {original}: região não encontrada\n"
                continue

            nome = res.iloc[0]

            if preco_fixo:
                preco = preco_fixo
            else:
                p_str = str(res.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.')
                nums = re.findall(r"\d+\.\d+|\d+", p_str)
                preco = float(nums[0]) if nums else 0.0

            total += preco
            saida += f"✅ {nome}: R$ {preco:.2f}\n"

        saida += f"\n*Total: R$ {total:.2f}*\n"
        st.code(saida)

        st.markdown(
            f'<a href="https://wa.me/?text={quote(saida)}" target="_blank" '
            f'style="background:#25D366;color:#fff;padding:14px;border-radius:8px;'
            f'display:block;text-align:center;text-decoration:none;font-weight:bold;">'
            f'📲 Enviar para WhatsApp</a>',
            unsafe_allow_html=True
        )
