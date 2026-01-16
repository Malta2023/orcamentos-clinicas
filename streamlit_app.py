import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥", layout="centered")

# Visual Moderno e Botões Estilizados
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stButton > button {
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    /* Botão Gerar - Azul */
    .stButton > button:first-child {
        background-color: #007bff;
        color: white;
        height: 3em;
        width: 100%;
    }
    /* Botão Novo Orçamento - Cinza */
    .stButton > button:active, .stButton > button:focus, .stButton > button:hover {
        border: 1px solid #007bff;
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
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# URLs Oficiais (Links CSV do Google Drive)
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

def limpar_tudo(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def extrair_preco(valor, nome_exame=""):
    nome_limpo = limpar_tudo(nome_exame)
    # Correções manuais solicitadas
    if "MAPA" in nome_limpo: return 140.00
    if "PANORAMICO" in nome_limpo and "COLUNA" in nome_limpo: return 154.00
    
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

# Início do App
st.title("🏥 Senhor APP")
st.markdown("### 📋 Orçamento Rápido")

# Botão Novo Orçamento no topo para facilitar
if st.button("🔄 NOVO ORÇAMENTO"):
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole a lista de exames:", placeholder="Ex: Hemograma\nGlicemia\nMAPA\nTGO/TGP", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str)
        df['NOME_LIMPO'] = df.iloc[:, 0].apply(limpar_tudo)
        
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
            p_busca = p_busca.replace("TOMOGRAFIA", "TC").replace("ULTRASSOM", "US").replace("ULTRASSONOGRAFIA", "US")
            
            termo = limpar_tudo(p_busca)
            match = df[df['NOME_LIMPO'].str.contains(termo, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                nome_tab = res.iloc[0]
                preco = extrair_preco(res.iloc[1], nome_tab)
                total += preco
                texto_whats += f"✅ {nome_tab}: R$ {preco:.2f}\n"
            else:
                # Regra de segurança para MAPA
                if "MAPA" in termo:
                    total += 140.0
                    texto_whats += f"✅ MAPA 24 HORAS: R$ 140.00\n"
                else:
                    texto_whats += f"❌ {p}: (Não encontrado)\n"
        
        texto_whats += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
        
        st.code(texto_whats, language="text")
        
        # Link WhatsApp
        link_wa = f"https://wa.me/?text={quote(texto_whats)}"
        st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-button">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
    else:
        st.error("Por favor, preencha a lista de exames.")

st.divider()
st.caption("Senhor APP v2.3 | Teresina - PI")
