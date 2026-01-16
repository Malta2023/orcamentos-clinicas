import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥", layout="centered")

# Visual Moderno
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stButton > button { border-radius: 8px; font-weight: bold; }
    .stButton > button:first-child { background-color: #007bff; color: white; width: 100%; height: 3.5em; }
    .whatsapp-button {
        display: block; background-color: #25D366; color: white; padding: 15px;
        text-align: center; text-decoration: none; font-size: 18px; font-weight: bold;
        border-radius: 10px; margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

def limpar_texto(t):
    if not isinstance(t, str): return ""
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.upper().strip()

def extrair_preco(valor, nome_exame=""):
    n = limpar_texto(nome_exame)
    # Correções Diretas (Travadas no código para não errar)
    if "HEMOGRAMA" in n: return 12.60 if clinica == "Sabry" else 12.24
    if "MAPA" in n: return 140.00
    if "PANORAMICO" in n and "COLUNA" in n: return 154.00
    
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
exames_raw = st.text_area("Cole os exames (um por linha):", placeholder="Ex: Hemograma\nGlicemia\nMAPA", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str).fillna("")
        
        # Limpando os nomes das colunas e os dados (tira espaços extras da planilha)
        df.columns = [limpar_texto(c) for c in df.columns]
        df['NOME_BUSCA'] = df.iloc[:, 0].apply(limpar_texto)
        
        linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw.upper())
        texto_final = f"* Orçamento - Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in linhas:
            original = item.strip()
            if not original: continue
            
            # Sinonimos e Padronização
            p = original.replace("RAIO X", "RX").replace("RX", "RX")
            p = p.replace("GLICEMIA", "GLICOSE").replace("GLICOSE EM JEJUM", "GLICOSE")
            p = p.replace("AST", "TGO").replace("ALT", "TGP")
            
            busca = limpar_texto(p)
            match = df[df['NOME_BUSCA'].str.contains(busca, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                nome_tabela = res.iloc[0]
                preco = extrair_preco(res.iloc[1], nome_tabela)
                total += preco
                texto_final += f"✅ {nome_tabela}: R$ {preco:.2f}\n"
            else:
                # Caso o Hemograma não seja lido na busca por algum erro de caractere na planilha
                if "HEMOGRAMA" in busca:
                    p_hemo = 12.60 if clinica == "Sabry" else 12.24
                    total += p_hemo
                    texto_final += f"✅ HEMOGRAMA: R$ {p_hemo:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
        
        texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
        
        st.code(texto_final, language="text")
        link_wa = f"https://wa.me/?text={quote(texto_final)}"
        st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-button">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
    else:
        st.error("Cole os exames primeiro!")

st.caption("Senhor APP v2.4 | Teresina - PI")
