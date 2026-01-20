import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

def purificar(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[^A-Z0-9]", " ", txt)
    return " ".join(txt.split()).strip()

URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"

MAPA_SINONIMOS = {
    "PCU": "PROTEINA C REATIVA ULTRASENSIVEL",
    "PROTEINA C ULTRASSENSIVEL": "PROTEINA C REATIVA ULTRASENSIVEL",
    "EAS": "SUMARIO DE URINA",
    "AST": "TGO",
    "ALT": "TGP",
    "ANTI TPO": "MICROSSOMAL",
    "ANTI TG": "TIREOGLOBULINA"
}

if "exames_texto" not in st.session_state:
    st.session_state.exames_texto = ""

def acao_limpar():
    st.cache_data.clear()
    st.session_state.exames_texto = ""

st.title("🏥 Orçamento Saúde Dirceu")

if st.button("🔄 NOVO ORÇAMENTO / ATUALIZAR", on_click=acao_limpar):
    st.rerun()

clinica_selecionada = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames:", height=200, key="exames_texto")

@st.cache_data(ttl=5)
def carregar_dados(url):
    try:
        df = pd.read_csv(url, on_bad_lines='skip').fillna("")
        df["NOME_ORIGINAL"] = df.iloc[:, 0].astype(str)
        df["NOME_PURIFICADO"] = df["NOME_ORIGINAL"].apply(purificar)
        return df
    except:
        return pd.DataFrame()

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        df = carregar_dados(URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA)
        
        if not df.empty:
            linhas_entrada = [l.strip() for l in exames_raw.split('\n') if l.strip()]
            total = 0.0
            sigla_c = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto_zap = f"*Orçamento Saúde Dirceu ({sigla_c})*\n\n"

            for original in linhas_entrada:
                termo = purificar(original)
                if not termo: continue
                
                busca = MAPA_SINONIMOS.get(termo, termo)
                match = pd.DataFrame()
                
                # 1. TENTA MATCH EXATO (Prioridade Máxima)
                match = df[df["NOME_PURIFICADO"] == busca]
                
                # 2. TENTA BUSCA POR PALAVRA INTEIRA (Evita VHS dentro de Testosterona)
                if match.empty:
                    # Cria um padrão que exige que a palavra esteja isolada
                    padrao = r'\b' + re.escape(busca) + r'\b'
                    match = df[df["NOME_PURIFICADO"].str.contains(padrao, case=False, na=False, regex=True)]

                nome_exame = None
                preco = 0.0

                if not match.empty:
                    match = match.copy()
                    match["len"] = match["NOME_PURIFICADO"].apply(len)
                    res = match.sort_values("len").iloc[0]
                    
                    if len(res) >= 2:
                        nome_exame = res["NOME_ORIGINAL"]
                        p_raw = str(res.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                        valores = re.findall(r"\d+\.\d+|\d+", p_raw)
                        if valores: preco = float(valores[0])

                # Regra de Imagem Sabry
                if nome_exame is None and clinica_selecionada == "Sabry":
                    if any(x in termo for x in ["RM", "RESSONANCIA", "TC", "TOMOGRAFIA"]):
                        nome_exame = original.upper()
                        preco = 545.00 if ("RM" in termo or "RESSONANCIA" in termo) else 165.00

                if nome_exame:
                    total += preco
                    texto_zap += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto_zap += f"❌ {original}: não encontrado\n"

            texto_zap += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_zap)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto_zap)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
