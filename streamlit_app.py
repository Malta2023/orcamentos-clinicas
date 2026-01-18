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
    if txt == "GLICEMIA": txt = "GLICOSE"
    return txt.strip()

# LINKS DOS ARQUIVOS SEPARADOS (DIRETO DAS SUAS NOVAS PLANILHAS)
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1WHg78O473jhUJ0DyLozPff8JwSES13FDxK9nJhh0_Rk/gviz/tq?tqx=out:csv"
URL_SABRY = "https://docs.google.com/spreadsheets/d/1_MwGqudeX1Rpgdbd-zNub5BLcSlLa7Z7Me6shuc7BFk/gviz/tq?tqx=out:csv"

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

                # 1. REGRAS FIXAS (LABCLINICA)
                if clinica_selecionada == "Labclinica":
                    if termo == "TSH": nome_exame = "TSH"; preco = 12.24
                    elif termo in ["GLICOSE", "GLICEMIA"]: nome_exame = "GLICOSE"; preco = 6.53
                    elif termo == "CREATININA": nome_exame = "CREATININA"; preco = 6.53
                    elif "CLEARENCE" in termo and "CREATININA" in termo: nome_exame = "CLEARENCE DE CREATININA"; preco = 8.16

                # 2. REGRAS DE IMAGEM (SABRY)
                if nome_exame is None and clinica_selecionada == "Sabry":
                    if termo.startswith("RM") or "RESSONANCIA" in termo:
                        nome_exame = original.upper(); preco = 545.00
                    elif termo.startswith("TC") or "TOMOGRAFIA" in termo:
                        nome_exame = original.upper(); preco = 165.00

                # 3. BUSCA SIMPLIFICADA E SEGURA
                if nome_exame is None:
                    # Passo A: Tenta encontrar o nome EXATO
                    match_exato = df[df["NOME_PURIFICADO"] == termo]
                    
                    if not match_exato.empty:
                        melhor_linha = match_exato.iloc[0]
                    else:
                        # Passo B: Se não achar exato, vê se o que você digitou ESTÁ DENTRO de algum nome
                        # Mas só faz isso se você digitou algo com mais de 3 letras
                        if len(termo) > 3:
                            # Filtra a tabela: só quem contém o texto digitado
                            possiveis = df[df["NOME_PURIFICADO"].str.contains(termo)]
                            if not possiveis.empty:
                                # Pega o nome mais curto que contém a palavra (evita pegar nomes gigantes)
                                melhor_linha = possiveis.sort_values(by=df.columns[0], key=lambda x: x.str.len()).iloc[0]
                            else:
                                melhor_linha = None
                        else:
                            melhor_linha = None
                    
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
            st.error(f"Erro: {e}")
