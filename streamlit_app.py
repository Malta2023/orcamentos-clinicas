import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def purificar_texto(t):
    if not isinstance(t, str): return ""
    # Mata caracteres russos e limpa espaços
    t = t.replace('Н', 'H').replace('Е', 'E').replace('М', 'M').replace('О', 'O').replace('А', 'A').replace('С', 'C')
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.upper().strip()

def extrair_preco(v):
    try:
        if pd.isna(v) or v == "": return 0.0
        # Remove R$, espaços e ajusta separadores decimais
        limpo = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

# URLs Oficiais
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.cache_data.clear()
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", height=200)

tag_clinica = "(S)" if clinica == "Sabry" else "(L)"

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url_selecionada = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        
        try:
            # Lendo a tabela sem cache para garantir valores novos
            df = pd.read_csv(url_selecionada, dtype=str).fillna("")
            
            # Limpeza preventiva da tabela
            df['BUSCA_NOME'] = df.iloc[:, 0].apply(purificar_texto)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            texto_final = f"*Orçamento Saúde Dirceu {tag_clinica}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                
                # Pre-processamento do termo de busca
                termo = purificar_texto(original)
                
                # Sinônimos Inteligentes
                if termo == "GLICEMIA": termo = "GLICOSE"
                if "T4" in termo and "LIVRE" in termo: termo = "T4" # Busca simplificada para T4
                
                # BUSCA: Tenta encontrar qualquer item que CONTÉM o que foi digitado
                # Isso resolve o problema de nomes técnicos longos
                match = df[df['BUSCA_NOME'].str.contains(termo, na=False)]
                
                # Se ainda não achou e for T4, tenta por TIROXINA
                if match.empty and "T4" in termo:
                    match = df[df['BUSCA_NOME'].str.contains("TIROXINA", na=False)]

                if not match.empty:
                    # Se houver mais de um resultado, pega o primeiro que melhor se encaixa
                    res = match.iloc[0]
                    nome_exame_tab = res.iloc[0]
                    preco = extrair_preco(res.iloc[1])
                    
                    total += preco
                    texto_final += f"✅ {nome_exame_tab}: R$ {preco:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            
            st.code(texto_final)
            link_wa = f"https://wa.me/?text={quote(texto_final)}"
            st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao ler planilha: {e}")
    else:
        st.error("Cole os exames primeiro.")

st.caption("Senhor APP v3.3 | Busca Flexível Ativada")
