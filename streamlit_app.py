import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

# Configuração da Página
st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

def purificar(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    if txt == "GLICEMIA": txt = "GLICOSE"
    return txt.strip()

# --- COLOQUE OS LINKS DAS PLANILHAS SEPARADAS AQUI ---
# Importante: O link deve terminar em /export?format=csv
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1--52OdN2HIuLb6szIvVTL-HBBLmtLshMjWD4cSOuZIE/edit?usp=sharing

"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1--52OdN2HIuLb6szIvVTL-HBBLmtLshMjWD4cSOuZIE/edit?usp=sharing

"

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
            # Seleção de URL sem risco de mistura
            url = URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA
            
            df = pd.read_csv(url).fillna("")
            df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)

            linhas = re.split(r"\n|,|;| E | & ", exames_raw)
            total = 0.0
            sigla = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto = f"*Orçamento Saúde Dirceu ({sigla})*\n\n"

            for linha in linhas:
                original = linha.strip()
                if not original: continue
                termo = purificar(original)
                nome_exame = None
                preco = 0.0

                # --- 1. REGRAS DE PREÇO FIXO (LABCLINICA) ---
                if clinica_selecionada == "Labclinica":
                    if termo == "TSH":
                        nome_exame = "TSH"; preco = 12.24
                    elif termo in ["GLICOSE", "GLICEMIA"]:
                        nome_exame = "GLICOSE"; preco = 6.53
                    elif termo == "CREATININA":
                        nome_exame = "CREATININA"; preco = 6.53
                    elif "CLEARENCE" in termo and "CREATININA" in termo:
                        nome_exame = "CLEARENCE DE CREATININA"; preco = 8.16

                # --- 2. REGRAS DE IMAGEM (SABRY) ---
                if nome_exame is None and clinica_selecionada == "Sabry":
                    is_rm = "RESSONANCIA" in termo or termo.startswith("RM")
                    is_tc = "TOMOGRAFIA" in termo or termo.startswith("TC")
                    if (is_rm or is_tc) and "ANGIO" not in termo:
                        nome_exame = original.upper()
                        preco = 545.00 if is_rm else 165.00

                # --- 3. BUSCA COM PRIORIDADE AO NOME CURTO/EXATO ---
                if nome_exame is None:
                    # Tenta match exato primeiro (Ex: Hemoglobina)
                    match_exato = df[df["NOME_PURIFICADO"] == termo]
                    
                    if not match_exato.empty:
                        # Se houver mais de um, pega o que tem o nome mais curto
                        melhor_linha = match_exato.sort_values(by=df.columns[0], key=lambda x: x.str.len()).iloc[0]
                    else:
                        # Busca aproximada com trava para não pegar exames longos demais
                        df_f = df if "ANGIO" in termo else df[~df["NOME_PURIFICADO"].str.contains("ANGIO")]
                        melhor_pontuacao = -1
                        melhor_linha = None
                        
                        for _, row in df_f.iterrows():
                            pontos = 0
                            t_words = termo.split()
                            n_words = row["NOME_PURIFICADO"].split()
                            for w in t_words:
                                if w in n_words: pontos += 20
                            
                            # Penaliza nomes gigantes (evita Hemoglobina -> Eletroforese de Hemoglobina)
                            pontos -= (len(row["NOME_PURIFICADO"]) - len(termo)) * 0.8
                            
                            if pontos > melhor_pontuacao and pontos > 0:
                                melhor_pontuacao = pontos; melhor_linha = row
                    
                    if melhor_linha is not None:
                        nome_exame = melhor_linha.iloc[0]
                        p_raw = str(melhor_linha.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                        res = re.findall(r"\d+\.\d+|\d+", p_raw)
                        if res: preco = float(res[0])

                if nome_exame:
                    total += preco
                    texto += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto += f"❌ {original}: não encontrado\n"

            texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao carregar planilha: {e}")
