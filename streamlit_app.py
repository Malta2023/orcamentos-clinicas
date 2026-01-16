import streamlit as st
import pandas as pd

# URLs das planilhas (Versão CSV)
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥")

st.title("🏥 Simulador de Orçamentos")

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames aqui (um por linha):", height=200)

if st.button("Gerar Orçamento para WhatsApp"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        lista_pedida = [e.strip().upper() for e in exames_raw.split('\n') if e.strip()]
        
        texto_whats = f"*Orçamento*\n*Clínica {clinica}*\n\nSegue seu orçamento completo:\n"
        total = 0.0
        
        for item in lista_pedida:
            # Busca simples por nome contido na tabela
            match = df[df.iloc[:, 0].str.contains(item, case=False, na=False)]
            if not match.empty:
                nome_tab = match.iloc[0, 0]
                preco = float(match.iloc[0, 1])
                total += preco
                texto_whats += f"{nome_tab} — R$ {preco:.2f}\n"
            else:
                texto_whats += f"{item} — (Consultar valor)\n"
        
        texto_whats += f"\n*Total: R$ {total:.2f}*\n\nQuando gostaria de agendar?\n"
        texto_whats += "Ah! Não se esqueça de salvar nosso contato... 📲\n"
        texto_whats += "Instagram: https://www.instagram.com/clinicapopularsaudedirceu"
        
        st.subheader("Texto pronto para copiar:")
        st.code(texto_whats, language="text")
    else:
        st.error("Por favor, cole os exames.")
