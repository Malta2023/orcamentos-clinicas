import streamlit as st
import pandas as pd
import re

# URLs das planilhas (Versão CSV)
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥")
st.title("🏥 Simulador de Orçamentos")

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames aqui (um por linha):", height=200)

def limpar_preco(valor):
    if pd.isna(valor): return 0.0
    # Remove R$, espaços e troca vírgula por ponto
    limpo = re.sub(r'[^\d,.-]', '', str(valor)).replace(',', '.')
    try:
        return float(limpo)
    except:
        return 0.0

if st.button("Gerar Orçamento para WhatsApp"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url)
        
        lista_pedida = [e.strip().upper() for e in exames_raw.split('\n') if e.strip()]
        texto_whats = f"*Orçamento*\n*Clínica {clinica}*\n\nSegue seu orçamento completo:\n"
        total = 0.0
        
        for item in lista_pedida:
            match = df[df.iloc[:, 0].str.contains(item, case=False, na=False)]
            if not match.empty:
                nome_tab = match.iloc[0, 0]
                preco = limpar_preco(match.iloc[0, 1])
                total += preco
                texto_whats += f"{nome_tab} — R$ {preco:.2f}\n"
            else:
                texto_whats += f"{item} — (Consultar valor)\n"
        
        texto_whats += f"\n*Total: R$ {total:.2f}*\n\nQuando gostaria de agendar?"
        
        st.subheader("Texto pronto para copiar:")
        st.code(texto_whats, language="text")
        st.info("Dica: Copie o texto acima e cole direto no WhatsApp do cliente!")
    else:
        st.error("Por favor, cole os exames.")
