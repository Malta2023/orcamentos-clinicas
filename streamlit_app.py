import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

# Configuração da página
st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def purificar_texto(t):
    if not isinstance(t, str): return ""
    # Converte letras russas/cirílicas para latinas
    t = t.replace('Н', 'H').replace('Е', 'E').replace('М', 'M').replace('О', 'O').replace('А', 'A').replace('С', 'C')
    # Remove acentos
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t.upper().strip()

def extrair_preco(v, n_exame, clinica_ref):
    n = purificar_texto(n_exame)
    # Valores Fixos de Segurança
    if "HEMOGRAMA" == n or "HEMOGRAMA COMPLETO" in n: 
        return 12.60 if clinica_ref == "Sabry" else 12.24
    if "MAPA" in n: return 140.00
    if "PANORAMICO" in n and "COLUNA" in n: return 154.00
    
    try:
        limpo = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

# URLs Oficiais das Tabelas
URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.rerun()

clinica = st.radio("Selecione a Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames aqui:", placeholder="Ex: Hemograma\nHemoglobina\nGlicose", height=200)

# Identificador da clínica para o título
tag_clinica = "(S)" if clinica == "Sabry" else "(L)"

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        url_selecionada = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        
        try:
            df = pd.read_csv(url_selecionada, dtype=str).fillna("")
            
            # Filtro para remover TRAB na Labclinica
            if clinica == "Labclinica":
                df = df[~df.iloc[:, 0].str.contains("TRAB|ANTICORPO ANTI RECEPTOR DE TSH", case=False, na=False)]
            
            df['BUSCA_LIMPA'] = df.iloc[:, 0].apply(purificar_texto)
            
            linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
            
            # Título conforme solicitado pelo usuário
            texto_final = f"*Orçamento Saúde Dirceu {tag_clinica}*\n\n"
            total = 0.0
            
            for item in linhas:
                original = item.strip()
                if not original: continue
                
                p_limpa = purificar_texto(original)
                
                # Sinônimos
                if p_limpa == "GLICEMIA": p_limpa = "GLICOSE"
                if p_limpa in ["AST", "TGO"]: p_limpa = "TGO"
                if p_limpa in ["ALT", "TGP"]: p_limpa = "TGP"

                # BUSCA 1: Nome Exato
                match = df[df['BUSCA_LIMPA'] == p_limpa]
                
                # BUSCA 2: Aproximada
                if match.empty:
                    match = df[df['BUSCA_LIMPA'].str.contains(p_limpa, na=False)]
                
                if not match.empty:
                    res = match.iloc[0]
                    nome_tab = res.iloc[0]
                    preco = extrair_preco(res.iloc[1], nome_tab, clinica)
                    total += preco
                    texto_final += f"✅ {nome_tab}: R$ {preco:.2f}\n"
                else:
                    # Fallback Hemograma
                    if "HEMOGRAMA" in p_limpa:
                        p_h = 12.60 if clinica == "Sabry" else 12.24
                        total += p_h
                        texto_final += f"✅ HEMOGRAMA: R$ {p_h:.2f}\n"
                    else:
                        texto_final += f"❌ {original}: (Não encontrado)\n"
            
            texto_final += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            
            st.code(texto_final)
            link_wa = f"https://wa.me/?text={quote(texto_final)}"
            st.markdown(f'<a href="{link_wa}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao carregar os dados: {e}")
    else:
        st.error("Cole os exames primeiro!")

st.caption("Senhor APP v3.1 | Teresina - PI")
