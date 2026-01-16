import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def purificar_texto(t):
    if not isinstance(t, str): return ""
    # Converte letras russas/cirílicas para latinas (H e E)
    t = t.replace('Н', 'H').replace('Е', 'E').replace('М', 'M').replace('О', 'O').replace('А', 'A').replace('С', 'C')
    # Remove acentos e padroniza
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.upper().strip()

def extrair_preco(v):
    try:
        if pd.isna(v) or v == "": return 0.0
        limpo = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

# URLs Oficiais das Tabelas
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
            # Lendo a tabela diretamente
            df = pd.read_csv(url_selecionada, dtype=str).fillna("")
            
            # --- BLOQUEIO DEFINITIVO DO TRAB NA LABCLINICA ---
            if clinica == "Labclinica":
                # Remove qualquer linha que contenha TRAB ou RECEPTOR DE TSH
                df = df[~df.iloc[:, 0].str.contains("TRAB|RECEPTOR DE TSH", case=False, na=False)]
            
            df['BUSCA_NOME'] = df.iloc[:, 0].apply(purificar_texto)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            texto_final = f"*Orçamento Saúde Dirceu {tag_clinica}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                
                termo = purificar_texto(original)
                
                # Sinônimos básicos
                if termo == "GLICEMIA": termo = "GLICOSE"
                if termo == "AST": termo = "TGO"
                if termo == "ALT": termo = "TGP"
                
                # BUSCA POR "CONTÉM" (Flexível para T4 Livre, Hemograma e outros)
                match = df[df['BUSCA_NOME'].str.contains(termo, na=False)]
                
                if not match.empty:
                    res = match.iloc[0]
                    nome_tab = res.iloc[0]
                    preco = extrair_preco(res.iloc[1])
                    
                    total += preco
                    texto_final += f"✅ {nome_tab}: R$ {preco:.2f}\n"
                else:
                    texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            
            st.code(texto_final)
            link_wa = f"https://wa.me/?text={quote(texto_final)}"
            st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao carregar os dados: {e}")
    else:
        st.error("Por favor, cole os exames primeiro.")

st.caption("Senhor APP v3.5 | TRAB Removido da Labclinica")
