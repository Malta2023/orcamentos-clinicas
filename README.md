import streamlit as st
import pandas as pd
import re

# URLs das suas planilhas (Versão CSV para leitura direta)
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP - Orçamentos", page_icon="🏥")
st.title("🏥 Simulador de Orçamentos")

# Função para limpar o preço e converter para número somável
def limpar_preco(valor):
    if pd.isna(valor): return 0.0
    # Remove R$, espaços, pontos de milhar e troca vírgula por ponto decimal
    limpo = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(limpo)
    except:
        return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames aqui (um por linha):", height=200, placeholder="Ex:\nHemograma\nSódio\nGlicose")

if st.button("Gerar Orçamento para WhatsApp"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip() # Remove espaços extras nos títulos
            
            lista_pedida = [e.strip().upper() for e in exames_raw.split('\n') if e.strip()]
            texto_whats = f"*Orçamento*\n*Clínica {clinica}*\n\nSegue seu orçamento completo:\n\n"
            total = 0.0
            
            for item in lista_pedida:
                # Busca o exame na primeira coluna da sua planilha
                match = df[df.iloc[:, 0].str.contains(item, case=False, na=False)]
                if not match.empty:
                    nome_tab = match.iloc[0, 0]
                    preco_raw = match.iloc[0, 1]
                    preco_num = limpar_preco(preco_raw)
                    total += preco_num
                    texto_whats += f"✅ {nome_tab} — R$ {preco_num:.2f}\n"
                else:
                    texto_whats += f"❌ {item} — (Não encontrado)\n"
            
            texto_whats += f"\n*Total: R$ {total:.2f}*\n\nQuando gostaria de agendar?"
            
            st.subheader("Texto pronto para copiar:")
            st.code(texto_whats, language="text")
            st.success("Tudo pronto! Basta copiar o texto acima e enviar.")
            
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")
    else:
        st.error("Por favor, cole a lista de exames.")
