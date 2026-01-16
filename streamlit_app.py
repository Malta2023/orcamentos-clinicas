import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# URLs das suas planilhas
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")

# Funções de limpeza simples (como eram no início)
def limpar_basico(texto):
    if not isinstance(texto, str): return ""
    # Remove acentos e deixa tudo em maiúsculo
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def converter_dinheiro(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str).fillna("")
        
        # Nome da coluna de busca
        df['BUSCA'] = df.iloc[:, 0].apply(limpar_basico)
        
        # Divide a lista do usuário
        linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw.upper())
        
        texto_final = f"*🏥 Orçamento - Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in linhas:
            original = item.strip()
            if not original: continue
            
            # TRADUÇÕES RÁPIDAS
            p = original.replace("GLICEMIA", "GLICOSE").replace("RX", "RX").replace("RAIO X", "RX")
            p = p.replace("AST", "TGO").replace("ALT", "TGP")
            p_limpa = limpar_basico(p)
            
            # BUSCA NA TABELA
            match = df[df['BUSCA'].str.contains(p_limpa, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                nome_tab = res.iloc[0]
                # Preços fixos para garantir os chatos
                if "HEMOGRAMA" in p_limpa:
                    preco = 12.60 if clinica == "Sabry" else 12.24
                elif "MAPA" in p_limpa:
                    preco = 140.00
                elif "PANORAMICO" in p_limpa and "COLUNA" in p_limpa:
                    preco = 154.00
                else:
                    preco = converter_dinheiro(res.iloc[1])
                
                total += preco
                texto_final += f"✅ {nome_tab}: R$ {preco:.2f}\n"
            else:
                # SE NÃO ACHOU MAS É HEMOGRAMA, FORÇA O VALOR
                if "HEMOGRAMA" in p_limpa:
                    p_fixo = 12.60 if clinica == "Sabry" else 12.24
                    total += p_fixo
                    texto_final += f"✅ HEMOGRAMA: R$ {p_fixo:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
        
        texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
        
        st.code(texto_final)
        st.markdown(f'<a href="https://wa.me/?text={quote(texto_final)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
    else:
        st.error("Cole os exames!")
