import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥", layout="centered")

# CSS para tornar o layout moderno e "com vida"
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        height: 3.5em;
        width: 100%;
        font-size: 18px;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #0056b3; border: none; }
    .whatsapp-button {
        display: inline-block;
        background-color: #25D366;
        color: white;
        padding: 15px 25px;
        text-align: center;
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        margin-top: 10px;
    }
    .stTextArea textarea { border-radius: 10px; border: 1px solid #d1d3e2; }
    </style>
    """, unsafe_allow_html=True)

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

def limpar_tudo(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def extrair_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

st.title("🏥 Senhor APP")
st.markdown("### 📋 Gerador de Orçamento Profissional")

with st.expander("📝 Instruções de Uso", expanded=False):
    st.write("1. Selecione a clínica.\n2. Cole a lista de exames.\n3. Clique em Gerar e envie direto para o cliente!")

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", placeholder="Ex:\nHemograma\nGlicemia em jejum\nTGO e TGP\nRx de Tórax", height=200)

if st.button("✨ GERAR ORÇAMENTO AGORA"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str)
        
        df['NOME_LIMPO'] = df.iloc[:, 0].apply(limpar_tudo)
        df['PRECO_LIMPO'] = df.iloc[:, 1].apply(extrair_preco)
        
        linhas_user = re.split(r'\n| E | & | \+ | / ', exames_raw.upper())
        
        texto_whats = f"*🏥 Orçamento - Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in linhas_user:
            # Dicionário de Sinônimos e Traduções
            p = item.strip()
            if not p: continue
            
            # Padronização de termos comuns
            p = p.replace("RAIO X", "RX").replace("RAIO-X", "RX")
            p = p.replace("GLICEMIA", "GLICOSE").replace("GLICOSE EM JEJUM", "GLICOSE")
            p = p.replace("TOMOGRAFIA", "TC").replace("ULTRASSOM", "US").replace("ULTRASSONOGRAFIA", "US")
            p = p.replace("AST", "TGO").replace("ALT", "TGP")
            
            termo_busca = limpar_tudo(p)
            
            # Busca aproximada na tabela
            match = df[df['NOME_LIMPO'].str.contains(termo_busca, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                # Trava para RX Panorâmico de Coluna na Sabry
                preco = 154.0 if "PANORAMICO" in termo_busca and clinica == "Sabry" else res['PRECO_LIMPO']
                total += preco
                texto_whats += f"✅ {res.iloc[0]}: R$ {preco:.2f}\n"
            else:
                texto_whats += f"❌ {p}: (Não encontrado)\n"
        
        resumo_final = f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*\n\n_Gerado por Senhor APP_"
        texto_whats += resumo_final
        
        st.info("Resultado Gerado com Sucesso!")
        st.code(texto_whats, language="text")
        
        # Link do WhatsApp
        link_wa = f"https://wa.me/?text={quote(texto_whats)}"
        st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-button">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
    else:
        st.error("⚠️ Por favor, cole a lista de exames para continuar.")

st.divider()
st.caption("Senhor APP v2.1 | Inteligência e Modernidade")
