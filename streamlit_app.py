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
    }
    .whatsapp-button {
        display: block;
        background-color: #25D366;
        color: white;
        padding: 15px;
        text-align: center;
        text-decoration: none;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

def limpar_tudo(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def extrair_preco(valor, nome_exame=""):
    nome_limpo = limpar_tudo(nome_exame)
    # Regras de correção manual solicitadas
    if "MAPA" in nome_limpo: return 140.00
    if "PANORAMICO" in nome_limpo and "COLUNA" in nome_limpo: return 154.00
    
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

st.title("🏥 Senhor APP")
st.markdown("### 📋 Orçamento Inteligente")

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", placeholder="Ex: Hemograma, Glicemia, MAPA, TGO...", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str)
        
        df['NOME_LIMPO'] = df.iloc[:, 0].apply(limpar_tudo)
        
        # Separar por linha, vírgula, "e", ou barras
        itens_user = re.split(r'\n|,| E | & | \+ | / ', exames_raw.upper())
        
        texto_whats = f"*🏥 Orçamento - Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in itens_user:
            p = item.strip()
            if not p: continue
            
            # Inteligência de Sinônimos
            p_busca = p.replace("RAIO X", "RX").replace("RAIO-X", "RX")
            p_busca = p_busca.replace("GLICEMIA", "GLICOSE").replace("GLICOSE EM JEJUM", "GLICOSE")
            p_busca = p_busca.replace("AST", "TGO").replace("ALT", "TGP")
            
            termo = limpar_tudo(p_busca)
            
            # Busca na Tabela
            match = df[df['NOME_LIMPO'].str.contains(termo, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                nome_final = res.iloc[0]
                preco = extrair_preco(res.iloc[1], nome_final)
                
                total += preco
                texto_whats += f"✅ {nome_final}: R$ {preco:.2f}\n"
            else:
                # Caso especial para MAPA se não achar na tabela
                if "MAPA" in termo:
                    total += 140.0
                    texto_whats += f"✅ MAPA 24 HORAS: R$ 140.00\n"
                else:
                    texto_whats += f"❌ {p}: (Não encontrado)\n"
        
        texto_whats += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
        
        st.code(texto_whats, language="text")
        
        link_wa = f"https://wa.me/?text={quote(texto_whats)}"
        st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-button">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
    else:
        st.error("Cole os exames!")
