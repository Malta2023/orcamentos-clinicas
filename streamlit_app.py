import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def purificar_para_busca(t):
    """ Remove acentos, caracteres russos, espaços e símbolos para uma busca infalível """
    if not isinstance(t, str): return ""
    # Converte letras russas/cirílicas para latinas
    t = t.replace('Н', 'H').replace('Е', 'E').replace('М', 'M').replace('О', 'O').replace('А', 'A').replace('С', 'C')
    # Normaliza acentos
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    # REMOVE TUDO: espaços, traços, parênteses (deixa só letras e números)
    t = re.sub(r'[^A-Z0-9]', '', t.upper())
    return t

def extrair_preco(v):
    try:
        if pd.isna(v) or v == "": return 0.0
        limpo = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.cache_data.clear()
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", height=200)

tag_clinica = "(S)" if clinica == "Sabry" else "(L)"

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url_selecionada = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        
        try:
            df = pd.read_csv(url_selecionada, dtype=str).fillna("")
            
            # Filtro de exclusão do TRAB na Labclinica
            if clinica == "Labclinica":
                df = df[~df.iloc[:, 0].str.contains("TRAB|RECEPTOR DE TSH", case=False, na=False)]
            
            # Cria a coluna de busca "blindada" (sem espaços ou símbolos)
            df['BUSCA_LIMPA'] = df.iloc[:, 0].apply(purificar_para_busca)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            texto_final = f"*Orçamento Saúde Dirceu {tag_clinica}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                
                # Transforma a entrada do usuário (ex: "t4 livre") em "T4LIVRE"
                termo_busca = purificar_para_busca(original)
                
                # Sinônimos de Glicose e Fígado
                if termo_busca == "GLICEMIA": termo_busca = "GLICOSE"
                if termo_busca == "AST": termo_busca = "TGO"
                if termo_busca == "ALT": termo_busca = "TGP"
                
                # Busca por CONTÉM na coluna blindada
                match = df[df['BUSCA_LIMPA'].str.contains(termo_busca, na=False)]
                
                if not match.empty:
                    res = match.iloc[0]
                    nome_tab = res.iloc[0]
                    preco = extrair_preco(res.iloc[1])
                    total += preco
                    texto_final += f"✅ {nome_tab}: R$ {preco:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_final)
            
            link_wa = f"https://wa.me/?text={quote(texto_final)}"
            st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")
    else:
        st.error("Cole os exames primeiro.")

st.caption("Senhor APP v3.6 | Busca Blindada (T4 Livre e Hemograma)")
