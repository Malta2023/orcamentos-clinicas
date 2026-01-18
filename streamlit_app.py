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

ID_PLANILHA = "1--52OdN2HIuLb6szIvVTL-HBBLmtLshMjWD4cSOuZIE"

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
            # Garante que lê apenas a aba da clínica selecionada
            gid = "1156828551" if clinica_selecionada == "Sabry" else "0"
            url_consulta = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&gid={gid}"
            
            df = pd.read_csv(url_consulta).fillna("")
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

                # --- 1. REGRAS FIXAS LABCLINICA (PRIORIDADE 1) ---
                if clinica_selecionada == "Labclinica":
                    if termo == "TSH":
                        nome_exame = "TSH"; preco = 12.24
                    elif termo in ["GLICOSE", "GLICEMIA"]:
                        nome_exame = "GLICOSE"; preco = 6.53
                    elif termo == "CREATININA":
                        nome_exame = "CREATININA"; preco = 6.53
                    elif "CLEARENCE" in termo and "CREATININA" in termo:
                        nome_exame = "CLEARENCE DE CREATININA"; preco = 8.16

                # --- 2. REGRA DE IMAGEM SABRY (PRIORIDADE 2) ---
                if nome_exame is None and clinica_selecionada == "Sabry":
                    is_rm = "RESSONANCIA" in termo or termo.startswith("RM")
                    is_tc = "TOMOGRAFIA" in termo or termo.startswith("TC")
                    if (is_rm or is_tc) and "ANGIO" not in termo:
                        nome_exame = original.upper()
                        preco = 545.00 if is_rm else 165.00

                # --- 3. BUSCA INTELIGENTE NA PLANILHA (PRIORIDADE 3) ---
                if nome_exame is None:
                    # Tenta primeiro encontrar o nome EXATAMENTE IGUAL ao que foi digitado
                    match_exato = df[df["NOME_PURIFICADO"] == termo]
                    
                    if not match_exato.empty:
                        melhor_linha = match_exato.iloc[0]
                    else:
                        # Se não achar exato, busca o que mais se parece, 
                        # mas ignora nomes muito longos se o termo for curto
                        df_filtrado = df if "ANGIO" in termo else df[~df["NOME_PURIFICADO"].str.contains("ANGIO")]
                        melhor_pontuacao = -1
                        melhor_linha = None
                        
                        for _, row in df_filtrado.iterrows():
                            pontos = 0
                            t_words = termo.split()
                            n_words = row["NOME_PURIFICADO"].split()
                            
                            # Pontua se as palavras batem
                            for w in t_words:
                                if w in n_words: pontos += 20
                            
                            # Penaliza se o nome na planilha for muito maior que o pedido
                            # Isso evita que "Hemoglobina" vire "Eletroforese de Hemoglobina"
                            diferenca_tamanho = len(row["NOME_PURIFICADO"]) - len(termo)
                            pontos -= diferenca_tamanho * 0.5 
                            
                            if pontos > melhor_pontuacao and pontos > 0:
                                melhor_pontuacao = pontos
                                melhor_linha = row
                    
                    if melhor_linha is not None:
                        nome_exame = melhor_linha.iloc[0]
                        p_raw = str(melhor_linha.iloc[1]).replace("R$", "").replace(".", "").replace(",", ".")
                        preco_match = re.findall(r"\d+\.\d+|\d+", p_raw)
                        if preco_match: preco = float(preco_match[0])

                if nome_exame:
                    total += preco
                    texto += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto += f"❌ {original}: não encontrado\n"

            texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")
