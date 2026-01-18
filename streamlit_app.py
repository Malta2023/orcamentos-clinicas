import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

# 1. Configuração visual do Aplicativo
st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

# 2. Função para limpar nomes de exames (tirar acentos e padronizar)
def purificar(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    # Regra importante: Trata GLICEMIA como GLICOSE
    if txt == "GLICEMIA": txt = "GLICOSE"
    return txt.strip()

# 3. Links da sua planilha "Orçamento rapido App"
# Já configurados para baixar os dados automaticamente
URL_SABRY = "https://docs.google.com/spreadsheets/d/1--52OdN2HIuLb6szIvVTL-HBBLmtLshMjWD4cSOuZIE/export?format=csv&gid=1156828551"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1--52OdN2HIuLb6szIvVTL-HBBLmtLshMjWD4cSOuZIE/export?format=csv&gid=0"

st.title("🏥 Orçamento Saúde Dirceu")

# Botão para limpar a tela e começar de novo
if st.button("🔄 NOVO ORÇAMENTO"):
    st.cache_data.clear()
    st.rerun()

# Seleção da Clínica e Campo de Texto
clinica_selecionada = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames (um por linha ou separados por vírgula):", height=150)

# Lógica principal ao clicar no botão de gerar
if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        try:
            # Seleciona a planilha correta conforme a escolha
            url = URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA
            
            # Lê os dados da planilha do Google
            df = pd.read_csv(url, dtype=str).fillna("")
            df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)

            # Divide o texto colado em exames individuais
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

                # --- REGRAS DE PREÇO FIXO: LABCLINICA ---
                if clinica_selecionada == "Labclinica":
                    if "CLEARENCE" in termo and "CREATININA" in termo:
                        nome_exame = "CLEARENCE DE CREATININA"; preco = 8.16
                    elif termo == "CREATININA":
                        nome_exame = "CREATININA"; preco = 6.53
                    elif termo == "TSH":
                        nome_exame = "TSH"; preco = 12.24
                    elif termo == "GLICOSE":
                        nome_exame = "GLICOSE"; preco = 6.53

                # --- REGRAS DE PREÇO FIXO: IMAGEM SABRY ---
                if nome_exame is None and clinica_selecionada == "Sabry":
                    is_rm = "RESSONANCIA" in termo or termo.startswith("RM")
                    is_tc = "TOMOGRAFIA" in termo or termo.startswith("TC")
                    if (is_rm or is_tc) and "ANGIO" not in termo:
                        nome_exame = original.upper()
                        preco = 545.00 if is_rm else 165.00

                # --- BUSCA AUTOMÁTICA NA PLANILHA (Se não for preço fixo) ---
                if nome_exame is None:
                    # Bloqueia RM/TC na Labclinica
                    if clinica_selecionada == "Labclinica" and ("RESSONANCIA" in termo or "TOMOGRAFIA" in termo):
                        pass 
                    else:
                        # Filtra para não pegar "Angio" por engano
                        df_busca = df if "ANGIO" in termo else df[~df["NOME_PURIFICADO"].str.contains("ANGIO")]
                        
                        melhor_pontuacao = -1
                        melhor_linha = None
                        
                        for _, row in df_busca.iterrows():
                            pontos = 0
                            t_words = termo.split()
                            n_words = row["NOME_PURIFICADO"].split()
                            for w in t_words:
                                if w in n_words: pontos += 10
                                elif w in row["NOME_PURIFICADO"]: pontos += 2
                            
                            if pontos > melhor_pontuacao and pontos > 0:
                                melhor_pontuacao = pontos
                                melhor_linha = row
                        
                        if melhor_linha is not None:
                            nome_exame = melhor_linha.iloc[0]
                            # Limpa o preço (tira R$, pontos e vírgulas)
                            p_raw = melhor_linha.iloc[1].replace("R$", "").replace(".", "").replace(",", ".")
                            preco = float(re.findall(r"\d+\.\d+|\d+", p_raw)[0])

                # Monta o texto do resultado
                if nome_exame:
                    total += preco
                    texto += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto += f"❌ {original}: não encontrado\n"

            # Finaliza o texto do orçamento
            texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            
            # Exibe o código para copiar e o botão do WhatsApp
            st.code(texto)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}. Verifique se a planilha está compartilhada corretamente.")
