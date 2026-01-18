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
    return txt.strip()

# LINKS DOS ARQUIVOS
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"

# --- DICIONÁRIO DE SIGLAS MEMORIZADO ---
SINONIMOS = {
    "TGO": "TRANSAMINASE OXALACETICA",
    "AST": "TRANSAMINASE OXALACETICA",
    "TGP": "TRANSAMINASE PIRUVICA",
    "ALT": "TRANSAMINASE PIRUVICA",
    "EAS": "SUMARIO DE URINA",
    "SUMARIO DE URINA": "SUMARIO DE URINA",
    "GLICEMIA": "GLICOSE"
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
exames_raw = st.text_area("Cole os exames:", height=150, key="exames_texto")

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        try:
            url = URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA
            df = pd.read_csv(url, on_bad_lines='skip').fillna("")
            df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)

            linhas = re.split(r"\n|,|;| E | & ", exames_raw)
            total = 0.0
            sigla_clinica = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto = f"*Orçamento Saúde Dirceu ({sigla_clinica})*\n\n"

            for linha in linhas:
                original = linha.strip()
                if not original: continue
                termo_base = purificar(original)
                
                # Tradução de Sigla para Nome da Tabela
                busca = termo_base
                for sigla, nome in SINONIMOS.items():
                    if sigla in termo_base:
                        busca = nome
                        break

                nome_exame = None
                preco = 0.0

                # Busca na tabela (Contém o nome ou é exato)
                match = df[df["NOME_PURIFICADO"].str.contains(busca, na=False)]
                
                if not match.empty:
                    # Pega o resultado mais curto (mais preciso)
                    melhor_linha = match.sort_values(by=df.columns[0], key=lambda x: x.str.len()).iloc[0]
                    nome_exame = melhor_linha.iloc[0]
                    # Extração de preço na coluna correta (ex: Ganho com 40%)
                    col_preco = melhor_linha.filter(like='40%').iloc[0] if clinica_selecionada == "Sabry" else melhor_linha.iloc[1]
                    
                    p_str = str(col_preco).replace("R$", "").replace(".", "").replace(",", ".")
                    valores = re.findall(r"\d+\.\d+|\d+", p_str)
                    if valores: preco = float(valores[0])

                if nome_exame:
                    total += preco
                    texto += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto += f"❌ {original}: não encontrado\n"

            texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
