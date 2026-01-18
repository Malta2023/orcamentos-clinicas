import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

def purificar(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    # Remove acentos
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    # REMOVE TUDO QUE NÃO É LETRA OU NÚMERO (limpeza total)
    txt = re.sub(r"[^A-Z0-9]", "", txt) 
    return txt.strip()

URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"

# Sinônimos de entrada (Se o usuário digitar um, o sistema aceita o outro)
MAPA_ENTRADA = {
    "CHLAMYDIA": "CLAMIDEA",
    "GLICEMIA": "GLICOSE",
    "EAS": "SUMARIOURINA",
    "TGO": "TGO",
    "AST": "TGO",
    "TGP": "TGP",
    "ALT": "TGP"
}

if "exames_texto" not in st.session_state:
    st.session_state.exames_texto = ""

def acao_limpar():
    st.cache_data.clear()
    st.session_state.exames_texto = ""

st.title("🏥 Orçamento Saúde Dirceu")

if st.button("🔄 ATUALIZAR / NOVO", on_click=acao_limpar):
    st.rerun()

clinica_selecionada = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames:", height=150, key="exames_texto")

@st.cache_data(ttl=5)
def carregar_dados(url):
    df = pd.read_csv(url, on_bad_lines='skip').fillna("")
    df["NOME_ORIGINAL"] = df.iloc[:, 0].astype(str)
    # A purificação aqui agora é agressiva: remove espaços e símbolos
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
                
                # Purifica o que o usuário digitou (ex: "TGO " vira "TGO")
                busca_limpa = purificar(original)
                busca_final = MAPA_ENTRADA.get(busca_limpa, busca_limpa)

                # Busca na tabela purificada (sem espaços, sem pontos)
                match = df[df["NOME_PURIFICADO"] == busca_final]
                
                # Se não achou exato, tenta "contém" (flexível)
                if match.empty:
                    match = df[df["NOME_PURIFICADO"].str.contains(busca_final, na=False)]

                nome_exame = None
                preco = 0.0

                if not match.empty:
                    res = match.iloc[0] # Pega a primeira ocorrência
                    nome_exame = res["NOME_ORIGINAL"]
                    
                    p_raw = str(res.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                    valores = re.findall(r"\d+\.\d+|\d+", p_raw)
                    if valores: preco = float(valores[0])

                # Regras de Imagem Sabry
                if nome_exame is None and clinica_selecionada == "Sabry":
                    if "RESSONANCIA" in busca_limpa or busca_limpa.startswith("RM"):
                        nome_exame = original.upper(); preco = 545.00
                    elif "TOMOGRAFIA" in busca_limpa or busca_limpa.startswith("TC"):
                        nome_exame = original.upper(); preco = 165.00

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
