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

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.cache_data.clear()
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", height=200)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        try:
            df = pd.read_csv(url, dtype=str).fillna("")
            df['NOME_PURIFICADO'] = df.iloc[:, 0].apply(purificar)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            texto_final = f"*Orçamento Saúde Dirceu {'(S)' if clinica == 'Sabry' else '(L)'}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                termo = purificar(original)
                
                nome_exame = None
                preco = 0.0

                # --- 1. REGRA ESPECIAL: RESSONÂNCIA (SEMPRE 545,00) ---
                if "RESSONANCIA" in termo and "ANGIO" not in termo:
                    nome_exame = original.upper()
                    preco = 545.00
                
                # --- 2. REGRA DO ESPELHO PARA OUTROS EXAMES DE IMAGEM ---
                elif any(x in termo for x in ["RAIO X", "RX", "TOMOGRAFIA", "ULTRASSOM", "ULTRASSONOGRAFIA"]) and "ANGIO" not in termo:
                    nome_exame = original.upper()
                    
                    # Busca o valor na tabela para a categoria
                    cat = "RAIO X" if "RAIO X" in termo or "RX" in termo else \
                          "TOMOGRAFIA" if "TOMOGRAFIA" in termo else \
                          "ULTRASSOM" if "ULTRASSOM" in termo or "ULTRASSONOGRAFIA" in termo else ""
                    
                    match_img = df[df['NOME_PURIFICADO'].str.contains(cat, na=False) & ~df['NOME_PURIFICADO'].str.contains("ANGIO", na=False)]
                    if not match_img.empty:
                        res = match_img.iloc[0]
                        p_str = str(res.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.')
                        nums = re.findall(r"\d+\.\d+|\d+", p_str)
                        preco = float(nums[0]) if nums else 0.0

                # --- 3. BUSCA NORMAL PARA O RESTANTE (LABORATÓRIO) ---
                if not nome_exame:
                    match = df[df['NOME_PURIFICADO'].str.contains(termo, na=False)].copy()
                    if not match.empty:
                        if "ANGIO" not in termo:
                            match = match[~match['NOME_PURIFICADO'].str.contains("ANGIO", na=False)]
                        
                        if not match.empty:
                            match['tam'] = match['NOME_PURIFICADO'].str.len()
                            res = match.sort_values('tam').iloc[0]
                            nome_exame = res.iloc[0]
                            p_str = str(res.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.')
                            nums = re.findall(r"\d+\.\d+|\d+", p_str)
                            preco = float(nums[0]) if nums else 0.0

                if nome_exame:
                    total += preco
                    texto_final += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_final)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto_final)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")
