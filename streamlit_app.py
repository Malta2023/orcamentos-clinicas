import streamlit as st
import pandas as pd
import re

# URLs das planilhas
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")
st.title("🏥 Senhor APP - Orçamentos")

def converter_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(re.findall(r"[-+]?\d*\.\d+|\d+", limpo)[0])
    except:
        return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames (um por linha):", height=150)

if st.button("Gerar Orçamento"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url)
        
        # LÓGICA DE EXCLUSÃO E UNIFICAÇÃO
        lista_pedida = []
        for e in exames_raw.split('\n'):
            item = e.strip().upper()
            if not item or "TRAB" in item or "RECEPTOR DE TSH" in item:
                continue # Pula o TRAB se for digitado
            if item == "GLICEMIA": item = "GLICOSE"
            lista_pedida.append(item)

        texto_whats = f"*Orçamento*\n*Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in lista_pedida:
            # Busca aproximada
            match = df[df.iloc[:, 0].str.contains(item, case=False, na=False)]
            
            if not match.empty:
                # Se for TSH, pega a linha com menor preço
                if item == "TSH":
                    match = match.copy()
                    match['preco_num'] = match.iloc[:, 1].apply(converter_preco)
                    linha = match.sort_values(by='preco_num').iloc[0]
                else:
                    linha = match.iloc[0]

                nome_tab = linha[0]
                preco_num = converter_preco(linha[1])
                total += preco_num
                texto_whats += f"✅ {nome_tab}: R$ {preco_num:.2f}\n"
            else:
                texto_whats += f"❌ {item}: (Não encontrado)\n"
        
        texto_whats += f"\n*Total: R$ {total:.2f}*"
        st.code(texto_whats, language="text")
    else:
        st.error("Cole a lista de exames!")
