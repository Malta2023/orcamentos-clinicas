import streamlit as st
import pandas as pd
import re
import unicodedata

# Links Oficiais
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.set_page_config(page_title="Senhor APP", page_icon="🏥")
st.title("🏥 Senhor APP - Orçamentos Oficiais")

def limpar_tudo(texto):
    if not isinstance(texto, str): return ""
    # Remove acentos e espaços inúteis
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.upper().strip()

def extrair_preco(valor):
    try:
        if pd.isna(valor): return 0.0
        # Remove R$, pontos de milhar e troca vírgula por ponto
        limpo = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

clinica = st.selectbox("Selecione a Clínica:", ["Sabry", "Labclinica"])
exames_raw = st.text_area("Cole a lista de exames aqui:", height=200)

if st.button("GERAR ORÇAMENTO"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str)
        
        # Limpeza pesada na tabela para não dar erro
        df['NOME_LIMPO'] = df.iloc[:, 0].apply(limpar_tudo)
        df['PRECO_LIMPO'] = df.iloc[:, 1].apply(extrair_preco)
        
        linhas_user = re.split(r'\n| E | & | \+ ', exames_raw.upper())
        
        texto_whats = f"*Orçamento - Clínica {clinica}*\n\n"
        total = 0.0
        
        for item in linhas_user:
            # Traduções e padronizações
            item_proc = item.replace("RAIO X", "RX").replace("RX", "RX")
            if "MAPA" in item_proc: item_proc = "MAPA"
            if "GLICEMIA" in item_proc: item_proc = "GLICOSE"
            
            termo_busca = limpar_tudo(item_proc)
            if not termo_busca: continue
            
            # Busca flexível: vê se o termo está dentro do nome na tabela
            match = df[df['NOME_LIMPO'].str.contains(termo_busca, na=False)]
            
            if not match.empty:
                # Pega a primeira opção encontrada
                res = match.iloc[0]
                # Correção manual do RX Panorâmico solicitada
                preco = 154.0 if "PANORAMICO" in termo_busca else res['PRECO_LIMPO']
                
                total += preco
                texto_whats += f"✅ {res.iloc[0]}: R$ {preco:.2f}\n"
            else:
                texto_whats += f"❌ {item.strip()}: Não encontrado\n"
        
        texto_whats += f"\n*Total: R$ {total:.2f}*"
        st.code(texto_whats, language="text")
    else:
        st.error("Cole os exames!")
