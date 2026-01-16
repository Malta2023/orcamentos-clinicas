import streamlit as st
import pandas as pd
import re

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")
st.title("🏥 Senhor APP - Versão Flexível")

def converter_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames aqui:", height=200)

if st.button("GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str)
        
        # Cria uma coluna de busca limpa (Maiúsculo e sem acentos básicos para facilitar)
        df['BUSCA_NOME'] = df.iloc[:, 0].str.upper().str.strip()
        
        linhas_digitadas = exames_raw.split('\n')
        lista_exames = []
        for l in linhas_digitadas:
            # Separa exames unidos por "E", "&", "/", "+"
            partes = re.split(r' E | & | / | \+ ', l.upper())
            for p in partes:
                item = p.replace("EM JEJUM", "").replace("JEJUM", "").replace("24 HORAS", "").strip()
                if item == "GLICEMIA": item = "GLICOSE"
                # Se for Raio X, simplifica a busca para a parte principal
                if "RAIO X" in item:
                    item = item.replace("RAIO X", "").strip()
                if item: lista_exames.append(item)

        texto_final = f"*Orçamento*\n*Clínica {clinica}*\n\n"
        total_geral = 0.0
        
        for busca in lista_exames:
            # BUSCA INTELIGENTE: Procura o termo em qualquer parte do nome na tabela
            resultado = df[df['BUSCA_NOME'].str.contains(busca, na=False, case=False)]
            
            if not resultado.empty:
                # Se achar vários (ex: vários Sódios), pega o primeiro ou o de menor preço
                resultado = resultado.copy()
                resultado['PRECO_NUM'] = resultado.iloc[:, 1].apply(converter_preco)
                melhor_opcao = resultado.sort_values(by='PRECO_NUM').iloc[0]
                
                nome_exame = melhor_opcao.iloc[0]
                preco_exame = melhor_opcao['PRECO_NUM']
                
                total_geral += preco_exame
                texto_final += f"* ✅ {nome_exame}: R$ {preco_exame:.2f}\n"
            else:
                texto_final += f"* ❌ {busca}: (Não encontrado)\n"
        
        texto_final += f"\n*Total: R$ {total_geral:.2f}*\n\nQuando gostaria de agendar?"
        st.code(texto_final, language="text")
    else:
        st.error("Por favor, cole os exames!")
