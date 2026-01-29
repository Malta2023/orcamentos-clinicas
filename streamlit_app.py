import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered", page_icon="🏥")

# --- LOGO ---
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/2966/2966327.png" 
try:
    st.image(URL_DO_LOGO, width=150)
except:
    st.title("🏥 Orçamento Saúde Dirceu")

# --- LINKS DAS PLANILHAS ---
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"
URL_CARDIOGRAFOS = "https://docs.google.com/spreadsheets/d/1tUqddImagn9QBSO7o5ddmpFwNnwtq01l/export?format=csv" 

def purificar(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    termos_ignore = ["NOSORO", "SANGUE", "EXAMEDE", "MATERIAU", "SORO", "VALOR", "SERICO", "PESQUISA", "DOSAGEM"]
    txt_limpo = re.sub(r"[^A-Z0-9]", "", txt)
    for termo in termos_ignore:
        txt_limpo = txt_limpo.replace(termo, "")
    return txt_limpo

DICIONARIO_PADRAO = {
    "VITAMINAD": "VITAMINAD25HIDROXIDO",
    "ANTITPO": "ANTITPO",
    "ANTITG": "ANTITG",
    "PCU": "PROTEINACREATIVAULTRASENSIVEL",
    "EAS": "SUMARIODEURINA",
    "AST": "TGO",
    "ALT": "TGP",
    "GAMAGT": "GAMAGT"
}

if "exames_texto" not in st.session_state:
    st.session_state.exames_texto = ""

def acao_limpar():
    st.cache_data.clear()
    st.session_state.exames_texto = ""

if st.button("🔄 REINICIAR SISTEMA (LIMPAR TUDO)", on_click=acao_limpar):
    st.rerun()

# Mudei a 'key' abaixo para forçar o Streamlit a redesenhar o menu
clinica_selecionada = st.radio(
    "Selecione a clínica:", 
    ["Sabry", "Labclinica", "Cardiografos"], 
    horizontal=True,
    key="menu_v53" 
)

exames_raw = st.text_area("Cole os exames (um por linha):", height=250, key="exames_texto")

@st.cache_data(ttl=5)
def carregar_dados(url):
    try:
        df = pd.read_csv(url, on_bad_lines='skip').fillna("")
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df["NOME_ORIGINAL"] = df.iloc[:, 0].astype(str)
        df["NOME_PURIFICADO"] = df["NOME_ORIGINAL"].apply(purificar)
        return df
    except: return pd.DataFrame()

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        # Define qual URL usar
        if clinica_selecionada == "Sabry":
            url_alvo = URL_SABRY
            sigla = "S"
        elif clinica_selecionada == "Labclinica":
            url_alvo = URL_LABCLINICA
            sigla = "L"
        else:
            url_alvo = URL_CARDIOGRAFOS
            sigla = "C"
            
        df = carregar_dados(url_alvo)
        
        if not df.empty:
            linhas_entrada = [l.strip() for l in exames_raw.split('\n') if l.strip()]
            total = 0.0
            texto_zap = f"*Orçamento Saúde Dirceu ({sigla})*\n\n"

            for original in linhas_entrada:
                entrada_limpa = purificar(original)
                if not entrada_limpa: continue
                
                busca_final = DICIONARIO_PADRAO.get(entrada_limpa, entrada_limpa)
                match = df[df["NOME_PURIFICADO"].str.contains(busca_final, na=False)]
                
                if not match.empty and "VHS" not in entrada_limpa:
                    match = match[~match["NOME_PURIFICADO"].str.fullmatch("VHS")]

                nome_exame = None
                preco = 0.0

                if not match.empty:
                    final = match.copy()
                    final["tam"] = final["NOME_PURIFICADO"].str.len()
                    res = final.sort_values("tam").iloc[0]
                    nome_exame = res["NOME_ORIGINAL"]
                    
                    for col_val in res.values:
                        val_str = str(col_val).replace("R$", "").strip()
                        if "," in val_str and any(c.isdigit() for c in val_str):
                            limpo = val_str.replace(".", "").replace(",", ".")
                            v = re.findall(r"\d+\.\d+|\d+", limpo)
                            if v: 
                                preco = float(v[0])
                                break

                # Regra de Imagem Sabry
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
