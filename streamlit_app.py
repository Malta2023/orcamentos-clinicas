import streamlit as st
import pandas as pd
import unicodedata
import re
from urllib.parse import quote

st.set_page_config(page_title="Orçamento Saúde Dirceu", layout="centered")

# ---------- FUNÇÕES ----------
def limpar(txt):
    if not isinstance(txt, str):
        return ""
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.upper().strip()

def preco_tabela(df, termo):
    termo = limpar(termo)

    # SINÔNIMOS
    if termo in ["GLICEMIA", "GLICOSE"]:
        termo = "GLICOSE"

    # TSH PURO
    if termo == "TSH":
        df_tsh = df[
            (df["NOME"].str.contains("TSH")) &
            (~df["NOME"].str.contains("TRAB")) &
            (~df["NOME"].str.contains("ANTICORPO")) &
            (~df["NOME"].str.contains("ANTI")) &
            (~df["NOME"].str.contains("RECEPTOR"))
        ]
        if not df_tsh.empty:
            return df_tsh.iloc[0]["EXAME"], df_tsh.iloc[0]["VALOR"]
        return None, None

    # BUSCA NORMAL
    match = df[df["NOME"].str.contains(termo)]
    if match.empty:
        return None, None

    match["LEN"] = match["NOME"].str.len()
    res = match.sort_values("LEN").iloc[0]
    return res["EXAME"], res["VALOR"]

# ---------- APP ----------
st.title("🏥 Orçamento Saúde Dirceu")

arquivo = st.file_uploader("Envie a tabela CSV", type="csv")

if arquivo:
    df = pd.read_csv(arquivo, dtype=str).fillna("")
    df.columns = ["EXAME", "VALOR"]
    df["NOME"] = df["EXAME"].apply(limpar)

    exames_raw = st.text_area("Digite os exames (um por linha)", height=200)

    if st.button("Gerar orçamento"):
        total = 0.0
        texto = "*Orçamento Saúde Dirceu*\n\n"

        linhas = re.split(r"\n|,|;", exames_raw)

        for item in linhas:
            item = item.strip()
            if not item:
                continue

            termo = limpar(item)

            # REGRAS FIXAS
            if "RESSONANCIA" in termo or termo.startswith("RM"):
                texto += "✅ RESSONÂNCIA: R$ 545.00\n"
                total += 545.00
                continue

            if "TOMOGRAFIA" in termo or termo.startswith("TC"):
                texto += "✅ TOMOGRAFIA: R$ 165.00\n"
                total += 165.00
                continue

            nome, valor = preco_tabela(df, termo)

            if nome:
                valor = float(valor.replace("R$", "").replace(".", "").replace(",", "."))
                texto += f"✅ {nome}: R$ {valor:.2f}\n"
                total += valor
            else:
                texto += f"❌ {item}: não encontrado\n"

        texto += f"\n*💰 Total: R$ {total:.2f}*\n\n*Quando gostaria de agendar?*"

        st.code(texto)
        st.markdown(
            f'<a href="https://wa.me/?text={quote(texto)}" target="_blank" '
            f'style="background:#25D366;color:white;padding:14px;display:block;'
            f'text-align:center;border-radius:8px;font-weight:bold;">📲 Enviar WhatsApp</a>',
            unsafe_allow_html=True
        )
