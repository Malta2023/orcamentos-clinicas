import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

def purificar(txt):
    if not isinstance(txt, str): return ""
    txt = txt.upper()
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.strip()

URL_SABRY = "https://docs.google.com/spreadsheets/d/1EHiFbpWyPzjyLJhxpC0FGw3A70m3xVZngXrK8LyzFEo/export?format=csv"
URL_LABCLINICA = "https://docs.google.com/spreadsheets/d/1ShcArMEHU9UDB0yWI2fkF75LXGDjXOHpX-5L_1swz5I/export?format=csv"

st.title("🏥 Orçamento Saúde Dirceu")

if st.button("🔄 NOVO ORÇAMENTO"):
    st.cache_data.clear()
    st.rerun()

clinica_selecionada = st.radio("Selecione a clínica:", ["Sabry", "Labclinica"], horizontal=True)
exames_raw = st.text_area("Cole os exames (um por linha ou separados por vírgula):", height=150)

if st.button("✨ GERAR ORÇAMENTO"):
    if exames_raw:
        try:
            # LIMPEZA DE MEMÓRIA: Força a leitura apenas da URL selecionada
            url = URL_SABRY if clinica_selecionada == "Sabry" else URL_LABCLINICA
            df = pd.read_csv(url, dtype=str).fillna("")
            df["NOME_PURIFICADO"] = df.iloc[:, 0].apply(purificar)

            linhas = re.split(r"\n|,|;| E | & ", exames_raw)
            total = 0.0
            sigla = 'S' if clinica_selecionada == "Sabry" else 'L'
            texto = f"*Orçamento Saúde Dirceu ({sigla})*\n\n"

            for linha in linhas:
                original = linha.strip()
                if not original: continue
                termo = purificar(original)

                nome_exame = None
                preco = 0.0
                nao_disponivel = False

                # --- 1. TRAVA DE CATEGORIA: LABCLINICA NÃO TEM IMAGEM PESADA ---
                is_imagem_pesada = "RESSONANCIA" in termo or termo.startswith("RM") or "TOMOGRAFIA" in termo or termo.startswith("TC")
                
                if clinica_selecionada == "Labclinica" and is_imagem_pesada:
                    nao_disponivel = True
                    motivo = "Exame de imagem não disponível na Labclinica"
                
                # --- 2. REGRA DO TSH (Nomenclatura exata) ---
                elif termo == "TSH":
                    match_tsh = df[df["NOME_PURIFICADO"] == "TSH"]
                    if match_tsh.empty:
                        match_tsh = df[df["NOME_PURIFICADO"].str.contains("TSH", na=False)]
                    
                    if not match_tsh.empty:
                        nome_exame = "TSH"
                        p_raw = match_tsh.iloc[0, 1].replace("R$", "").replace(".", "").replace(",", ".")
                        preco = float(re.findall(r"\d+\.\d+|\d+", p_raw)[0])

                # --- 3. REGRA DO ESPELHO PARA IMAGEM (RM, TC, RX, US) - SÓ PARA SABRY ---
                if nome_exame is None and not nao_disponivel:
                    is_rm = "RESSONANCIA" in termo or termo.startswith("RM") or " RM " in f" {termo} "
                    is_tc = "TOMOGRAFIA" in termo or termo.startswith("TC") or " TC " in f" {termo} "
                    is_rx = "RAIO X" in termo or termo.startswith("RX") or " RX " in f" {termo} "
                    is_us = "ULTRAS" in termo or termo.startswith("US") or " US " in f" {termo} "
                    tem_angio = "ANGIO" in termo

                    if (is_rm or is_tc or is_rx or is_us) and not tem_angio:
                        nome_exame = original.upper()
                        cat = "RESSONANCIA" if is_rm else "TOMOGRAFIA" if is_tc else "RAIO X" if is_rx else "ULTRAS"
                        
                        match_img = df[df["NOME_PURIFICADO"].str.contains(cat) & ~df["NOME_PURIFICADO"].str.contains("ANGIO")]
                        if not match_img.empty:
                            p_raw = match_img.iloc[0, 1].replace("R$", "").replace(".", "").replace(",", ".")
                            preco = float(re.findall(r"\d+\.\d+|\d+", p_raw)[0])

                # --- 4. BUSCA GERAL (LABORATÓRIO) ---
                if nome_exame is None and not nao_disponivel:
                    df_busca = df if "ANGIO" in termo else df[~df["NOME_PURIFICADO"].str.contains("ANGIO")]
                    melhor_pontuacao = -1
                    melhor_linha = None
                    
                    for _, row in df_busca.iterrows():
                        pontos = 0
                        t_words = termo.split()
                        n_words = row["NOME_PURIFICADO"].split()
                        for w in t_words:
                            if w in n_words: pontos += 10
                            elif w in row["NOME_PURIFICADO"]: pontos += 2
                        
                        if pontos > melhor_pontuacao and pontos > 0:
                            melhor_pontuacao = pontos
                            melhor_linha = row
                    
                    if melhor_linha is not None:
                        nome_exame = melhor_linha.iloc[0]
                        p_raw = melhor_linha.iloc[1].replace("R$", "").replace(".", "").replace(",", ".")
                        preco = float(re.findall(r"\d+\.\d+|\d+", p_raw)[0])

                # --- MONTAGEM DO RESULTADO ---
                if nao_disponivel:
                    texto += f"⚠️ {original}: (Não disponível nesta clínica)\n"
                elif nome_exame:
                    total += preco
                    texto += f"✅ {nome_exame}: R$ {preco:.2f}\n"
                else:
                    texto += f"❌ {original}: não encontrado\n"

            texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"
            st.code(texto)
            st.markdown(f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" style="background:#25D366;color:white;padding:15px;border-radius:10px;display:block;text-align:center;font-weight:bold;text-decoration:none;">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Erro: {e}")
