import streamlit as st
import pandas as pd
import re

# URLs fixas
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")
st.title("🏥 Senhor APP - Versão Corrigida")

def converter_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        # Remove R$, espaços, pontos de milhar e troca vírgula por ponto
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames (Um por linha):", height=200)

if st.button("GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        # Lê a planilha forçando todas as colunas como texto para evitar erros de leitura
        df = pd.read_csv(url, dtype=str)
        
        # Cria uma coluna de busca simplificada na tabela
        df['BUSCA_NOME'] = df.iloc[:, 0].str.upper().str.strip()
        
        # Processa o que o usuário digitou
        linhas_digitadas = exames_raw.split('\n')
        lista_exames = []
        for l in linhas_digitadas:
            # Separa "E", "&", "/" para pegar exames como TGO e TGP
            partes = re.split(r' E | & | / | \+ ', l.upper())
            for p in partes:
                item = p.replace("EM JEJUM", "").replace("JEJUM", "").replace("24 HORAS", "").replace("24H", "").strip()
                if item == "GLICEMIA": item = "GLICOSE"
                if item: lista_exames.append(item)

        texto_final = f"*Orçamento*\n*Clínica {clinica}*\n\n"
        total_geral = 0.0
        
        for busca in lista_exames:
            # Busca se o termo digitado está dentro de algum nome da tabela
            resultado = df[df['BUSCA_NOME'].str.contains(busca, na=False)]
            
            if not resultado.empty:
                # Regra do menor preço (especialmente para TSH)
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
