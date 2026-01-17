import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote
from rapidfuzz import process, fuzz

# Configuração da página
st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

# --- DICIONÁRIO DE SINÔNIMOS ---
SINONIMOS = {
    "RM": "RESSONANCIA",
    "TC": "TOMOGRAFIA",
    "RX": "RAIO X",
    "US": "ULTRASSONOGRAFIA",
    "ULTRAS": "ULTRASSONOGRAFIA",
    "ULTRA": "ULTRASSONOGRAFIA",
    "ECO": "ECOCARDIOGRAMA",
    "HEMOGRAMA": "SANGUE",
    "SANGUE": "HEMOGRAMA",
    "URINA": "EAS",
    "FEZES": "PARASITOLOGICO",
    "ABD": "ABDOME",
    "ABD TOTAL": "ABDOME TOTAL",
    "SUPRA": "SUPRARENAL",
}

def purificar(txt):
    """Remove acentos, converte para maiúsculas e limpa espaços."""
    if not isinstance(txt, str): return ""
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.upper().strip()

def expandir_sinonimos(termo):
    """Expande o termo de busca com sinônimos conhecidos."""
    palavras = termo.split()
    resultado = []
    for p in palavras:
        resultado.append(p)
        if p in SINONIMOS:
            resultado.append(SINONIMOS[p])
    return " ".join(resultado)

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Orçamento Saúde Dirceu")

# --- BOTÃO NOVO ORÇAMENTO ---
if st.button("🔄 NOVO ORÇAMENTO"):
    st.cache_data.clear()
    st.rerun()

clinica = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames (um por linha ou separados por vírgula):", height=150)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        try:
            url = URL_SABRY if clinica == "Sabry" else URL_LABCLINICA
            df = pd.read_csv(url, dtype=str).fillna("")
            
            # Criar coluna purificada para busca
            df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)
            lista_produtos_purificados = df["NOME_PURIFICADO"].tolist()

            # Separar os exames inseridos
            linhas = re.split(r"\n|,|;| E | & ", exames_raw)
            total = 0.0
            texto = f"*Orçamento Saúde Dirceu ({'S' if clinica=='Sabry' else 'L'})*\n\n"

            for linha in linhas:
                original = linha.strip()
                if not original: continue
                
                termo_limpo = purificar(original)
                termo_expandido = expandir_sinonimos(termo_limpo)

                nome_exame = None
                preco = 0.0

                # --- 1. BUSCA INTELIGENTE COM RAPIDFUZZ ---
                # Filtro prévio para garantir que categorias principais (RM, TC, RX, US) batam
                categorias = ["RESSONANCIA", "TOMOGRAFIA", "RAIO X", "ULTRASSONOGRAFIA"]
                cat_presente = next((c for c in categorias if c in termo_expandido), None)
                
                df_filtrado = df
                if cat_presente:
                    # Se o usuário pediu uma categoria específica, filtramos a lista para essa categoria
                    df_filtrado = df[df["NOME_PURIFICADO"].str.contains(cat_presente)]
                
                if df_filtrado.empty: df_filtrado = df # Fallback se o filtro for muito restritivo
                
                lista_busca = df_filtrado["NOME_PURIFICADO"].tolist()
                indices_originais = df_filtrado.index.tolist()

                resultado = process.extractOne(
                    termo_expandido, 
                    lista_busca, 
                    scorer=fuzz.token_sort_ratio
                )
                
                if resultado and resultado[1] < 75:
                    resultado_flex = process.extractOne(
                        termo_expandido, 
                        lista_busca, 
                        scorer=fuzz.token_set_ratio
                    )
                    if resultado_flex and resultado_flex[1] > resultado[1]:
                        resultado = resultado_flex

                if resultado and resultado[1] >= 60:
                    indice_real = indices_originais[resultado[2]]
                    melhor_linha = df.loc[indice_real]
                    nome_exame = melhor_linha.iloc[0]
                    
                    # Processamento do preço
                    p_raw = melhor_linha.iloc[1].replace("R$", "").replace(".", "").replace(",", ".")
                    match_preco = re.findall(r"\d+\.\d+|\d+", p_raw)
                    if match_preco:
                        preco = float(match_preco[0])
                    else:
                        preco = 0.0

                # --- 2. MONTAGEM DO TEXTO ---
                if nome_exame:
                    total += preco
                    texto += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto += f"❌ {original}: não encontrado\n"

            texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            
            st.code(texto)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
    else:
        st.warning("Por favor, cole os exames antes de gerar o orçamento.")

st.caption("v7.0 - Busca Inteligente com RapidFuzz e Sinônimos")
