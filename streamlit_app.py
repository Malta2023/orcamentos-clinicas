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

# TRADUTOR DE ENTRADA REFORÇADO
MAPA_SINONIMOS = {
    "PCU": "PROTEINA C REATIVA ULTRASENSIVEL",
    "PROTEINA C ULTRASSENSIVEL": "PROTEINA C REATIVA ULTRASENSIVEL",
    "EAS": "SUMARIO DE URINA",
    "AST": "TGO",
    "ALT": "TGP",
    "ANTI TPO": "TPO", # Foca na sigla principal
    "TPO": "ANTI TPO",
    "ANTI TG": "TIREOGLOBULINA",
    "VITAMINA D": "25 HIDROXIVITAMINA D",
    "GAMA GT": "GAMA"
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
exames_raw = st.text_area("Cole os exames:", height=250, key="exames_texto")

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
                termo_original_limpo = purificar(original)
                if not termo_original_limpo: continue
                
                busca = MAPA_SINONIMOS.get(termo_original_limpo, termo_original_limpo)
                match = pd.DataFrame()
                
                # 1. BUSCA EXATA
                match = df[df["NOME_PURIFICADO"] == busca]
                
                # 2. BUSCA POR CONTÉM (Flexível)
                if match.empty:
                    match = df[df["NOME_PURIFICADO"].str.contains(busca, na=False)]
                
                # 3. BUSCA POR PALAVRAS SEPARADAS (Caso o Anti-TPO esteja como "ANTITPO" ou similar)
                if match.empty and " " in busca:
                    partes = busca.split()
                    match = df[df["NOME_PURIFICADO"].apply(lambda x: all(p in str(x) for p in partes))]

                # FILTRO ANTI-INVASOR (VHS)
                if not match.empty:
                    match = match.copy()
                    if "VHS" in match["NOME_PURIFICADO"].values and "VHS" not in termo_original_limpo:
                        match = match[match["NOME_PURIFICADO"] != "VHS"]

                nome_exame = None
                preco = 0.0

                if not match.empty:
                    match["len"] = match["NOME_PURIFICADO"].apply(len)
                    res = match.sort_values("len").iloc[0]
                    
                    if len(res) >= 2:
                        nome_exame = res["NOME_ORIGINAL"]
                        p_raw = str(res.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                        valores = re.findall(r"\d+\.\d+|\d+", p_raw)
                        if valores: preco = float(valores[0])

                if nome_exame:
                    total += preco
                    texto_zap += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto_zap += f"❌ {original}: não encontrado\n"

            texto_zap += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_zap)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto_zap)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
