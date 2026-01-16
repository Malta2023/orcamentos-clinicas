import streamlit as st
import pandas as pd
import re

# URLs das suas planilhas
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP - Sabry", page_icon="🏥")
st.title("🏥 Senhor APP - Orçamentos Rápidos")

def converter_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

clinica = st.selectbox("Escolha a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames aqui (um por linha ou separados por 'e'):", height=250)

if st.button("GERAR ORÇAMENTO EM LISTA"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url)
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.upper().str.strip()
        
        # Processamento inteligente da lista
        linhas = [l.strip().upper() for l in exames_raw.split('\n') if l.strip()]
        lista_final = []
        for linha in linhas:
            if "TRAB" in linha: continue
            # Separa termos como "E", "&", "/" ou "+"
            partes = re.split(r' E | & | / | \+ ', linha)
            for p in partes:
                p = p.replace("EM JEJUM", "").replace("JEJUM", "").replace("24 HORAS", "").replace("24H", "").strip()
                if p == "GLICEMIA": p = "GLICOSE"
                if p: lista_final.append(p)

        texto_whats = f"*Orçamento*\n*Clínica {clinica}*\n\nSegue seu orçamento completo:\n\n"
        total = 0.0
        
        for item in lista_final:
            # Busca flexível na tabela
            match = df[df.iloc[:, 0].str.contains(item, case=False, na=False)]
            
            if not match.empty:
                if "TSH" in item: # Regra do menor preço para TSH
                    match = match.copy()
                    match['p_num'] = match.iloc[:, 1].apply(converter_preco)
                    res = match.sort_values(by='p_num').iloc[0]
                else:
                    res = match.iloc[0]
                
                p_num = converter_preco(res[1])
                total += p_num
                texto_whats += f"* ✅ {res[0]}: R$ {p_num:.2f}\n"
            else:
                texto_whats += f"* ❌ {item}: (Não encontrado)\n"
        
        texto_whats += f"\n*Total: R$ {total:.2f}*\n\nQuando gostaria de agendar?"
        texto_whats += "\n\nAh! Não se esqueça de salvar nosso contato. 📲"
        
        st.subheader("Resultado para copiar:")
        st.code(texto_whats, language="text")
    else:
        st.warning("Por favor, insira ao menos um exame.")
