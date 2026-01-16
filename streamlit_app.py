import streamlit as st
import pandas as pd
import re
import unicodedata
from urllib.parse import quote

st.set_page_config(page_title="Senhor APP", page_icon="🏥", layout="centered")

def limpeza_total(texto):
    """ Remove acentos, caracteres invisíveis, espaços duplos e letras de outros alfabetos """
    if not isinstance(texto, str): return ""
    # Converte letras parecidas (cirílico para latino)
    mapa = {'Н': 'H', 'Е': 'E', 'М': 'M', 'О': 'O', 'А': 'A', 'Р': 'P', 'С': 'C', 'Т': 'T', 'В': 'B', 'Х': 'X', 'К': 'K'}
    for errado, certo in mapa.items():
        texto = texto.replace(errado, certo)
    # Remove acentos
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    # Mantém APENAS letras e números (remove espaços invisíveis, tabs, etc)
    texto = re.sub(r'[^A-Z0-9]', '', texto.upper())
    return texto

def extrair_valor(v, nome_exame="", clinica_ref=""):
    n = limpeza_total(nome_exame)
    # Valores fixos de segurança
    if "HEMOGRAMA" in n: return 12.60 if clinica_ref == "Sabry" else 12.24
    if "MAPA" in n: return 140.00
    if "PANORAMICO" in n and "COLUNA" in n: return 154.00
    try:
        limpo = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", limpo)
        return float(nums[0]) if nums else 0.0
    except: return 0.0

st.title("🏥 Senhor APP")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.rerun()

clinica = st.radio("Clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Exames:", height=150)

if st.button("✨ GERAR"):
    if exames_raw:
        url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
        df = pd.read_csv(url, dtype=str).fillna("")
        
        # Cria coluna de busca "limpa de verdade"
        df['BUSCA_PURIFICADA'] = df.iloc[:, 0].apply(limpeza_total)
        
        linhas = re.split(r'\n|,| E | & | \+ | / ', exames_raw)
        texto_whats = f"*🏥 Orçamento - {clinica}*\n\n"
        total = 0.0
        
        for item in linhas:
            if not item.strip(): continue
            
            # Padronização de nomes comuns antes da limpeza total
            p_original = item.strip().upper()
            p_tratado = p_original.replace("GLICEMIA", "GLICOSE").replace("RX", "RX").replace("RAIO X", "RX")
            
            # Limpeza radical
            termo_limpo = limpeza_total(p_tratado)
            
            # Busca
            match = df[df['BUSCA_PURIFICADA'].str.contains(termo_limpo, na=False)]
            
            if not match.empty:
                res = match.iloc[0]
                nome_exame = res.iloc[0]
                preco = extrair_valor(res.iloc[1], nome_exame, clinica)
                total += preco
                texto_whats += f"✅ {nome_exame}: R$ {preco:.2f}\n"
            else:
                # O "ÚLTIMO SUSPIRO" para o Hemograma
                if "HEMOGRAMA" in termo_limpo:
                    p_h = 12.60 if clinica == "Sabry" else 12.24
                    total += p_h
                    texto_whats += f"✅ HEMOGRAMA: R$ {p_h:.2f}\n"
                else:
                    texto_whats += f"❌ {p_original}: (Não encontrado)\n"
        
        texto_whats += f"\n*💰 Total: R$ {total:.2f}*\n\n*Agendar?*"
        st.code(texto_whats)
        st.markdown(f'<a href="https://wa.me/?text={quote(texto_whats)}" target="_blank" style="background-color:#25D366; color:white; padding:15px; border-radius:10px; display:block; text-align:center; text-decoration:none; font-weight:bold;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
