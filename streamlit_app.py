import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

def purificar(txt):
    """Transforma qualquer nome em uma 'chave' única sem espaços ou símbolos."""
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    # Remove termos que variam entre tabelas mas são o mesmo exame
    termos_ignore = ["NOSORO", "SANGUE", "EXAMEDE", "MATERIAU", "SORO", "VALOR", "SÉRICO", "PESQUISA", "DOSAGEM"]
    txt_limpo = re.sub(r"[^A-Z0-9]", "", txt)
    for termo in termos_ignore:
        txt_limpo = txt_limpo.replace(termo, "")
    return txt_limpo

URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"

# TRADUTOR INTELIGENTE: Liga o que você digita ao que as tabelas costumam ter
DICIONARIO_PADRAO = {
    "VITAMINAD": "VITAMINAD",
    "ANTITPO": "TPO",
    "ANTITG": "TIREOGLOBULINA",
    "PCU": "PROTEINACREATIVAULTRASENSIVEL",
    "PROTEINACULTRASSENSIVEL": "PROTEINACREATIVAULTRASENSIVEL",
    "EAS": "SUMARIODEURINA",
    "AST": "TGO",
    "ALT": "TGP",
    "GAMAGT": "GAMA"
}

if "exames_texto" not in st.session_state:
    st.session_state.exames_texto = ""

def acao_limpar():
    st.cache_data.clear()
    st.session_state.exames_texto = ""

st.title("🏥 Orçamento Saúde Dirceu")

if st.button("🔄 NOVO ORÇAMENTO", on_click=acao_limpar):
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
    except: return pd.DataFrame()

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        # Pega a tabela ESPECÍFICA escolhida no rádio
        df = carregar_dados(URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA)
        
        if not df.empty:
            linhas_entrada = [l.strip() for l in exames_raw.split('\n') if l.strip()]
            total = 0.0
            sigla_c = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto_zap = f"*Orçamento Saúde Dirceu ({sigla_c})*\n\n"

            for original in linhas_entrada:
                entrada_limpa = purificar(original)
                if not entrada_limpa: continue
                
                # Tradução via dicionário ou usa o próprio termo limpo
                busca_final = DICIONARIO_PADRAO.get(entrada_limpa, entrada_limpa)
                
                # Busca na tabela selecionada
                match = df[df["NOME_PURIFICADO"].str.contains(busca_final, na=False)]
                
                # Filtro de segurança (VHS só se for pedido)
                if not match.empty and "VHS" not in entrada_limpa:
                    match = match[~match["NOME_PURIFICADO"].str.fullmatch("VHS")]

                nome_exame = None
                preco = 0.0

                if not match.empty:
                    # Entre os achados na clínica, pega o mais curto (mais preciso)
                    res = match.copy()
                    res["tam"] = res["NOME_PURIFICADO"].str.len()
                    final = res.sort_values("tam").iloc[0]
                    
                    nome_exame = final["NOME_ORIGINAL"]
                    p_raw = str(final.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                    v = re.findall(r"\d+\.\d+|\d+", p_raw)
                    if v: preco = float(v[0])

                # Regra de Imagem Exclusiva Sabry
                if nome_exame is None and clinica_selecionada == "Sabry":
                    if any(x in entrada_limpa for x in ["RM", "RESSONANCIA", "TC", "TOMOGRAFIA"]):
                        nome_exame = original.upper()
                        preco = 545.00 if "RM" in entrada_limpa else 165.00

                if nome_exame:
                    total += preco
                    texto_zap += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto_zap += f"❌ {original}: não encontrado\n"

            texto_zap += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_zap)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto_zap)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
