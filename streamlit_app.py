import streamlit as st
import pandas as pd
import re

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")
st.title("🏥 Senhor APP - Orçamentos")

def converter_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames (um por linha):", height=200)

if st.button("Gerar Orçamento"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url)
        # Normaliza a tabela: tudo para maiúsculo e sem espaços extras
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.upper().str.strip()
        
        # Processa a lista colada pelo usuário
        linhas = [l.strip().upper() for l in exames_raw.split('\n') if l.strip()]
        lista_final = []
        for linha in linhas:
            if "TRAB" in linha: continue
            # Separa exames que o usuário escreveu com "E", "&" ou "/"
            partes = re.split(r' E | & | / ', linha)
            for p in partes:
                p = p.replace("EM JEJUM", "").replace(" 24 HORAS", "").strip()
                if p == "GLICEMIA": p = "GLICOSE"
                if p: lista_final.append(p)

        texto_whats = f"*Orçamento*\n*Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in lista_final:
            # Busca: verifica se o item digitado está contido em algum nome da tabela
            match = df[df.iloc[:, 0].str.contains(rf"\b{item}\b", case=False, na=False, regex=True)]
            
            # Se não achou com a palavra exata, tenta uma busca mais aberta
            if match.empty:
                match = df[df.iloc[:, 0].str.contains(item, case=False, na=False)]

            if not match.empty:
                if "TSH" in item: # Regra do menor TSH
                    match = match.copy()
                    match['p_num'] = match.iloc[:, 1].apply(converter_preco)
                    res = match.sort_values(by='p_num').iloc[0]
                else:
                    res = match.iloc[0]
                
                p_num = converter_preco(res[1])
                total += p_num
                texto_whats += f"✅ {res[0]}: R$ {p_num:.2f}\n"
            else:
                texto_whats += f"❌ {item}: (Não encontrado)\n"
        
        texto_whats += f"\n*Total: R$ {total:.2f}*\n\nQuando gostaria de agendar?"
        st.code(texto_whats, language="text")
        st.success("Agora o sistema está separando exames como TGO e TGP automaticamente!")
    else:
        st.error("Por favor, cole os exames.")
