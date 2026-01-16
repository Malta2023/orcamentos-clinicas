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
    # Regra de Segurança: Ressonância de Crânio sempre 545.00
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
            df_raw = pd.read_csv(url, dtype=str).fillna("")
            
            if clinica == "Labclinica":
                df = df_raw[~df_raw.iloc[:, 0].str.contains("TRAB|RECEPTOR DE TSH", case=False, na=False)].copy()
            else:
                df = df_raw.copy()
            
            df['NOME_PURIFICADO'] = df.iloc[:, 0].apply(purificar)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            texto_final = f"*Orçamento Saúde Dirceu {tag_clinica}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                
                termo_usuario = purificar(original)
                
                # --- LÓGICA DE EXCLUSÃO RÍGIDA ---
                match = pd.DataFrame()
                
                # Se o usuário digitou a palavra ANGIO, busca específica para Angio
                if "ANGIO" in termo_usuario:
                    match = df[df['NOME_PURIFICADO'].str.contains("ANGIO", na=False) & 
                               df['NOME_PURIFICADO'].str.contains(termo_usuario.replace("ANGIO", "").strip(), na=False)]
                
                # Se NÃO digitou ANGIO, mas digitou TOMO ou RESSONANCIA, bloqueia resultados com a palavra ANGIO
                elif "TOMO" in termo_usuario or "RESSONANCIA" in termo_usuario:
                    mask = ~df['NOME_PURIFICADO'].str.contains("ANGIO", na=False)
                    palavras = termo_usuario.split()
                    for p in palavras:
                        mask &= df['NOME_PURIFICADO'].str.contains(p, na=False)
                    match = df[mask]
                
                # Busca reserva (Exata ou Palavras-chave) caso não entre nas regras de Angio/Simples
                if match.empty:
                    match = df[df['NOME_PURIFICADO'] == termo_usuario]
                
                if match.empty:
                    palavras = termo_usuario.split()
                    if palavras:
                        mask = df['NOME_PURIFICADO'].str.contains(palavras[0], na=False)
                        for p in palavras[1:]:
                            mask &= df['NOME_PURIFICADO'].str.contains(p, na=False)
                        match = df[mask]
                
                if not match.empty:
                    res = match.iloc[0]
                    nome_tab = res.iloc[0]
                    preco = extrair_preco(res.iloc[1], nome_tab)
                    total += preco
                    texto_final += f"✅ {nome_tab}: R$ {preco:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto_final)
            
            link_wa = f"https://wa.me/?text={quote(texto_final)}"
            st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro no sistema: {e}")
    else:
        st.error("Por favor, cole os exames primeiro.")

st.caption("Senhor APP v4.3 | Separação Angio/Simples (Tomo e Ressonância)")
