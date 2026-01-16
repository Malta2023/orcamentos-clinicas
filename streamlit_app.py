import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def purificar_texto(t):
    if not isinstance(t, str): return ""
    # Mata caracteres russos (H e E) e converte para latinos
    t = t.replace('Н', 'H').replace('Е', 'E').replace('М', 'M').replace('О', 'O').replace('А', 'A').replace('С', 'C')
    # Remove acentos e padroniza
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.upper().strip()

def extrair_preco(v, n_exame, clinica_ref):
    n = purificar_texto(n_exame)
    # Regras de Ouro (Valores Fixos)
    if "HEMOGRAMA" == n or "HEMOGRAMA COMPLETO" in n: 
        return 12.60 if clinica_ref == "Sabry" else 12.24
    if "MAPA" in n: return 140.00
    if "PANORAMICO" in n and "COLUNA" in n: return 154.00
    
    try:
        limpo = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

# URLs Oficiais
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", placeholder="Ex: Hemograma\nHemoglobina\nGlicose", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else
