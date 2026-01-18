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

# LINKS REVISADOS
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/export?format=csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/export?format=csv"

# DICIONÁRIO COMPLETO DE VARIAÇÕES (MEMORIZADO)
SINONIMOS = {
    "TGO": "TRANSAMINASE OXALACETICA",
    "AST": "TRANSAMINASE OXALACETICA",
    "TGP": "TRANSAMINASE PIRUVICA",
    "ALT": "TRANSAMINASE PIRUVICA",
    "EAS": "SUMARIO DE URINA",
    "SUMARIO URINA": "SUMARIO DE URINA",
    "URINA TIPO 1": "SUMARIO DE URINA",
    "BILIRRUBINA": "BILIRRUBINAS",
    "GLICEMIA": "GLICOSE",
    "HEMOGRAMA": "HEMOGRAMA"
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
            
            # Garante que temos pelo menos duas colunas (Nome e Preço)
            if df.shape[1] < 2:
                st.error("A planilha selecionada parece estar vazia ou mal formatada.")
            else:
                df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)
                linhas = re.split(r"\n|,|;| E | & ", exames_raw)
                total = 0.0
                sigla_c = 'S' if clinica_selecionada == "Sabry" else 'L'
                texto = f"*Orçamento Saúde Dirceu ({sigla_c})*\n\n"

                for linha in linhas:
                    original = linha.strip()
                    if not original: continue
                    termo_base = purificar(original)
                    
                    # Aplica variações
                    busca = termo_base
                    for sigla, nome in SINONIMOS.items():
                        if sigla in termo_base:
                            busca = nome
                            break

                    nome_exame = None
                    preco = 0.0

                    # 1. REGRAS FIXAS (LABCLINICA)
                    if clinica_selecionada == "Labclinica":
                        if "TSH" == termo_base: nome_exame = "TSH"; preco = 12.24
                        elif "GLICOSE" in busca: nome_exame = "GLICOSE"; preco = 6.53
                        elif "CREATININA" == termo_base: nome_exame = "CREATININA"; preco = 6.53

                    # 2. REGRAS DE IMAGEM (SABRY)
                    if nome_exame is None and clinica_selecionada == "Sabry":
                        if termo_base.startswith("RM") or "RESSONANCIA" in termo_base:
                            nome_exame = original.upper(); preco = 545.00
                        elif termo_base.startswith("TC") or "TOMOGRAFIA" in termo_base:
                            nome_exame = original.upper(); preco = 165.00

                    # 3. BUSCA NA TABELA (Geral)
                    if nome_exame is None:
                        # Busca por "Contém" para ser mais flexível
                        match = df[df["NOME_PURIFICADO"].str.contains(busca, na=False)]
                        if not match.empty:
                            # Pega o nome mais curto para evitar pegar exames errados
                            melhor_linha = match.sort_values(by=df.columns[0], key=lambda x: len(str(x))).iloc[0]
                            nome_exame = melhor_linha.iloc[0]
                            
                            # Tenta pegar o preço da segunda coluna (índice 1)
                            p_str = str(melhor_linha.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
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
