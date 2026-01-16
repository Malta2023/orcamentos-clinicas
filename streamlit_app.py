import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥", layout="centered")

# Estilo Visual
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div.stButton > button { border-radius: 8px; font-weight: bold; transition: 0.3s; }
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

def normalizar_extremo(texto):
    """ Remove caracteres 'fantasmas' de outros alfabetos e limpa o texto """
    if not isinstance(texto, str): return ""
    
    # Mapa de caracteres que parecem latinos mas são cirílicos/outros
    # Resolve problemas com: H, E, M, O, A, P, C, T, B, X, K, y
    mapa_sujo = {
        'Н': 'H', 'Е': 'E', 'М': 'M', 'О': 'O', 'А': 'A', 'Р': 'P', 
        'С': 'C', 'Т': 'T', 'В': 'B', 'Х': 'X', 'К': 'K', 'у': 'Y'
    }
    for errado, certo in mapa_sujo.items():
        texto = texto.replace(errado, certo)
    
    # Normalização padrão (remove acentos e coloca em maiúsculo)
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def tratar_preco(valor, nome_exame="", clinica_escolhida=""):
    n = normalizar_extremo(nome_exame)
    
    # Travas de Segurança para itens críticos
    if "HEMOGRAMA" in n: return 12.60 if clinica_escolhida == "Sabry" else 12.24
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
exames_raw = st.text_area("Cole os exames aqui:", placeholder="Ex: Hemograma\nGlicemia\nMAPA", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str).fillna("")
        
        # Blindagem nas colunas e nos dados da tabela
        df.columns = [normalizar_extremo(c) for c in df.columns]
        df['NOME_BUSCA'] = df.iloc[:, 0].apply(normalizar_extremo)
        
        linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
        texto_final = f"*🏥 Orçamento - Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in linhas:
            if not item.strip(): continue
            
            # Normaliza a entrada do usuário
            p = normalizar_extremo(item)
            
            # Padronização de nomes comuns
            p = p.replace("RAIO X", "RX").replace("RX", "RX")
            p = p.replace("GLICEMIA", "GLICOSE")
            p = p.replace("AST", "TGO").replace("ALT", "TGP")
            
            # Busca na tabela blindada
            match = df[df['NOME_BUSCA'].str.contains(p, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                nome_exame_tab = res.iloc[0]
                preco = tratar_preco(res.iloc[1], nome_exame_tab, clinica)
                total += preco
                texto_final += f"✅ {nome_exame_tab}: R$ {preco:.2f}\n"
            else:
                # Fallback para Hemograma caso a busca ainda falhe por caractere especial
                if "HEMOGRAMA" in p:
                    p_fixo = 12.60 if clinica == "Sabry" else 12.24
                    total += p_fixo
                    texto_final += f"✅ HEMOGRAMA: R$ {p_fixo:.2f}\n"
                else:
                    texto_final += f"❌ {item.strip()}: (Não encontrado)\n"
        
        texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
        
        st.code(texto_final, language="text")
        link_wa = f"https://wa.me/?text={quote(texto_final)}"
        st.markdown(f'<a href="{link_wa}" target="_blank" class="whatsapp-button">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
    else:
        st.error("Por favor, cole os exames!")

st.caption("Senhor APP v2.6 | Blindagem Anti-Erros de Caractere")
