import streamlit as st
import pandas as pd
import re
import unicodedata

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")
st.title("🏥 Senhor APP - Orçamentos Oficiais")

def limpar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def converter_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole os exames aqui:", height=200)

if st.button("GERAR ORÇAMENTO EM LISTA"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str)
        
        df['NOME_ORIGINAL'] = df.iloc[:, 0]
        df['BUSCA_LIMPA'] = df.iloc[:, 0].apply(limpar_texto)
        df['PRECO_LIMPO'] = df.iloc[:, 1].apply(converter_preco)
        
        linhas = [l.strip().upper() for l in exames_raw.split('\n') if l.strip()]
        lista_busca = []
        for l in linhas:
            if "TRAB" in l: continue
            partes = re.split(r' E | & | / | \+ ', l)
            for p in partes:
                # UNIFICAÇÃO DE TERMOS (Raio X, Rx vira RX)
                p = p.replace("RAIO X", "RX").replace("RAIO-X", "RX")
                # LIMPANDO MAPA
                if "MAPA" in p: p = "MAPA"
                
                p = p.replace("EM JEJUM", "").replace("JEJUM", "").strip()
                
                p_limpa = limpar_texto(p)
                # SINÔNIMOS DE URINA
                if p_limpa in ["EAS", "URINA TIPO 1", "URINA TIPO I"]: p_limpa = "SUMARIO DE URINA"
                if p_limpa == "GLICEMIA": p_limpa = "GLICOSE"
                
                if p_limpa: lista_busca.append(p_limpa)

        texto_final = f"*Orçamento*\n*Clínica {clinica}*\n\nSegue seu orçamento completo:\n\n"
        total = 0.0
        
        for termo in lista_busca:
            # Busca se o termo está em qualquer parte do nome
            resultado = df[df['BUSCA_LIMPA'].str.contains(termo, na=False)]
            
            if not resultado.empty:
                # Pega o primeiro ou menor preço
                melhor_opcao = resultado.sort_values(by='PRECO_LIMPO').iloc[0]
                total += melhor_opcao['PRECO_LIMPO']
                texto_final += f"* ✅ {melhor_opcao['NOME_ORIGINAL']}: R$ {melhor_opcao['PRECO_LIMPO']:.2f}\n"
            else:
                texto_final += f"* ❌ {termo}: (Não encontrado)\n"
        
        texto_final += f"\n*Total: R$ {total:.2f}*\n\nQuando gostaria de agendar?"
        st.code(texto_final, language="text")
    else:
        st.error("Por favor, cole os exames!")
