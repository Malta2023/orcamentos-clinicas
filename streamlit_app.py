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

# TRADUTOR DE ENTRADA
MAPA_SINONIMOS = {
    "BILIRRUBINA": "BILIRRUBINA",
    "BILIRRUBINAS": "BILIRRUBINA",
    "GAMA GT": "GAMA",
    "EAS": "SUMARIO DE URINA",
    "SUMARIO URINA": "SUMARIO DE URINA",
    "CHLAMYDIA": "CLAMIDEA",
    "AST": "TGO",
    "ALT": "TGP",
    "GLICEMIA": "GLICOSE"
}

if "exames_texto" not in st.session_state:
    st.session_state.exames_texto = ""

def acao_limpar():
    st.cache_data.clear()
    st.session_state.exames_texto = ""

st.title("🏥 Orçamento Saúde Dirceu")

if st.button("🔄 ATUALIZAR TABELAS", on_click=acao_limpar):
    st.rerun()

clinica_selecionada = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames:", height=150, key="exames_texto")

@st.cache_data(ttl=5)
def carregar_dados(url):
    df = pd.read_csv(url, on_bad_lines='skip').fillna("")
    df["NOME_ORIGINAL"] = df.iloc[:, 0].astype(str)
    df["NOME_PURIFICADO"] = df["NOME_ORIGINAL"].apply(purificar)
    return df

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        try:
            url = URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA
            df = carregar_dados(url)
            
            linhas = re.split(r"\n|,|;", exames_raw)
            total = 0.0
            sigla_c = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto_zap = f"*Orçamento Saúde Dirceu ({sigla_c})*\n\n"

            for linha in linhas:
                original = linha.strip()
                if not original: continue
                
                termo = purificar(original)
                
                # Pega a primeira palavra para uma busca mais "agressiva" se falhar
                primeira_palavra = termo.split()[0] if termo else ""
                busca = MAPA_SINONIMOS.get(termo, termo)

                match = pd.DataFrame()
                
                # 1. Busca Exata
                match = df[df["NOME_PURIFICADO"] == busca]
                
                # 2. Busca por Contém (termo completo)
                if match.empty:
                    match = df[df["NOME_PURIFICADO"].str.contains(busca, na=False)]
                
                # 3. Busca pela Primeira Palavra (Caso de Bilirrubinas/Gama)
                if match.empty and len(primeira_palavra) > 3:
                    match = df[df["NOME_PURIFICADO"].str.contains(primeira_palavra, na=False)]

                nome_exame = None
                preco = 0.0

                if not match.empty:
                    match = match.copy()
                    match["len"] = match["NOME_PURIFICADO"].apply(len)
                    res = match.sort_values("len").iloc[0]
                    nome_exame = res["NOME_ORIGINAL"]
                    
                    p_raw = str(res.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                    valores = re.findall(r"\d+\.\d+|\d+", p_raw)
                    if valores: preco = float(valores[0])

                # Regra de Imagem (Sabry)
                if nome_exame is None and clinica_selecionada == "Sabry":
                    if any(x in termo for x in ["RM", "RESSONANCIA", "TC", "TOMOGRAFIA"]):
                        nome_exame = original.upper()
                        preco = 545.00 if "RM" in termo or "RESSONANCIA" in termo else 165.00

                if nome_exame:
                    total += preco
                    texto_zap += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto_zap += f"❌ {original}: não encontrado\n"

            texto_zap += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_zap)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto_zap)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")
