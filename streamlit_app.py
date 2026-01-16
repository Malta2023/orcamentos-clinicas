import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def purificar(t):
    if not isinstance(t, str): return ""
    t = t.replace('Н', 'H').replace('Е', 'E').replace('М', 'M').replace('О', 'O').replace('А', 'A').replace('С', 'C')
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.upper().strip()

def extrair_preco(v, n_exame):
    n = purificar(n_exame)
    # Regra de ouro para o Crânio
    if "RESSONANCIA" in n and "CRANIO" in n:
        return 545.00
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
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        try:
            df = pd.read_csv(url, dtype=str).fillna("")
            if clinica == "Labclinica":
                df = df[~df.iloc[:, 0].str.contains("TRAB|RECEPTOR DE TSH", case=False, na=False)].copy()
            
            df['NOME_PURIFICADO'] = df.iloc[:, 0].apply(purificar)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            texto_final = f"*Orçamento Saúde Dirceu {tag_clinica}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                termo = purificar(original)
                
                # Busca básica: contém o que foi digitado
                match = df[df['NOME_PURIFICADO'].str.contains(termo, na=False)].copy()
                
                if not match.empty:
                    # DESEMPATE PARA RESSONANCIA/TOMO/ANGIO
                    if "ANGIO" not in termo:
                        # Se o usuário NÃO digitou ANGIO, prioriza quem NÃO tem ANGIO no nome
                        simples = match[~match['NOME_PURIFICADO'].str.contains("ANGIO", na=False)]
                        if not simples.empty:
                            match = simples
                    
                    # Se houver vários, pega o que tem o nome mais curto (exame básico)
                    match['comprimento'] = match['NOME_PURIFICADO'].str.len()
                    res = match.sort_values('comprimento').iloc[0]
                    
                    nome_tab = res.iloc[0]
                    preco = extrair_preco(res.iloc[1], nome_tab)
                    total += preco
                    texto_final += f"✅ {nome_tab}: R$ {preco:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_final)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto_final)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")
    else:
        st.error("Cole os exames primeiro.")

st.caption("Senhor APP v4.7 | Busca Estabilizada")
