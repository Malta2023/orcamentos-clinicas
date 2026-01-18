import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

def purificar(txt):
    if not isinstance(txt, str): txt = str(txt)
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.strip()

# LINKS
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"

# MEMÓRIA DE SINÔNIMOS (TGO, TGP, CLAMIDEA, EAS)
SINONIMOS = {
    "EAS": "SUMARIO DE URINA",
    "URINA I": "SUMARIO DE URINA",
    "GLICEMIA": "GLICOSE",
    "CHLAMYDIA": "CLAMIDEA",
    "TGO": "TRANSAMINASE OXALACETICA",
    "TGP": "TRANSAMINASE PIRUVICA",
    "AST": "TRANSAMINASE OXALACETICA",
    "ALT": "TRANSAMINASE PIRUVICA"
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

@st.cache_data(ttl=30) # Reduzi para 30 segundos para ser quase tempo real
def carregar_dados(url):
    return pd.read_csv(url, on_bad_lines='skip').fillna("")

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        try:
            url = URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA
            df = carregar_dados(url)
            df["NOME_ORIGINAL"] = df.iloc[:, 0].astype(str)
            df["NOME_PURIFICADO"] = df["NOME_ORIGINAL"].apply(purificar)
            
            linhas = re.split(r"\n|,|;| E | & ", exames_raw)
            total = 0.0
            sigla_c = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto_zap = f"*Orçamento Saúde Dirceu ({sigla_c})*\n\n"

            for linha in linhas:
                original = linha.strip()
                if not original: continue
                termo_base = purificar(original)
                
                # Aplica Tradução de Sinônimo
                for sigla, nome in SINONIMOS.items():
                    if sigla == termo_base:
                        termo_base = nome
                        break

                nome_exame = None
                preco = 0.0
                
                # --- NOVA LÓGICA DE BUSCA POR PALAVRAS ---
                palavras_busca = termo_base.split()
                # Filtra a tabela onde TODAS as palavras buscadas aparecem no nome
                def contem_todas(nome_tab):
                    return all(p in nome_tab for p in palavras_busca if len(p) > 1)

                match = df[df["NOME_PURIFICADO"].apply(contem_todas)]

                if not match.empty:
                    # Se houver vários, pega o que tem o nome mais curto
                    match = match.copy()
                    match["len_name"] = match["NOME_PURIFICADO"].apply(lambda x: len(str(x)))
                    melhor_linha = match.sort_values("len_name").iloc[0]
                    
                    nome_exame = melhor_linha["NOME_ORIGINAL"]
                    p_raw = str(melhor_linha.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                    valores = re.findall(r"\d+\.\d+|\d+", p_raw)
                    if valores: preco = float(valores[0])

                # Regra de Segurança para Imagem
                if nome_exame is None and clinica_selecionada == "Sabry":
                    if termo_base.startswith("RM") or "RESSONANCIA" in termo_base:
                        nome_exame = original.upper(); preco = 545.00
                    elif termo_base.startswith("TC") or "TOMOGRAFIA" in termo_base:
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
