# app.py
import re
import unicodedata
import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Orcamentos de Exames", layout="centered")

# --------- util ---------

def remove_acentos(txt: str) -> str:
    txt = "" if txt is None else str(txt)
    return "".join(
        c for c in unicodedata.normalize("NFD", txt)
        if unicodedata.category(c) != "Mn"
    )

def normaliza_nome(nome: str) -> str:
    s = remove_acentos(nome).upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s

# regras salvas
SINONIMOS = {
    "EAS": "SUMARIO DE URINA",
    "URINA TIPO 1": "SUMARIO DE URINA",
    "SUMARIO URINA": "SUMARIO DE URINA",
}

SIGLAS = {
    "TC": "TOMOGRAFIA",
    "RX": "RAIO X",
    "US": "ULTRASSOM",
}

def aplica_regras(txt: str) -> str:
    s = normaliza_nome(txt)
    for sigla, full in SIGLAS.items():
        s = re.sub(rf"\b{sigla}\b", full, s)
    for k, v in SINONIMOS.items():
        s = s.replace(k, v)
    return s


def load_table_from_bytes(file_bytes: bytes, kind: str) -> pd.DataFrame:
    bio = BytesIO(file_bytes)
    df = pd.read_excel(bio)

    if kind == "LABCLINICA":
        df = df.rename(columns={"Exame": "exame", "Valor": "valor"})
        df = df.dropna(subset=["exame"])
        df["valor_num"] = pd.to_numeric(df["valor"], errors="coerce")

    else:  # SABRY
        df.columns = [str(c).strip().lower() for c in df.columns]
        if "exame" not in df.columns or "valor" not in df.columns:
            raise ValueError("Tabela Sabry precisa ter colunas 'exame' e 'valor'.")
        df = df.dropna(subset=["exame"])
        df["valor_num"] = (
            df["valor"].astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df["valor_num"] = pd.to_numeric(df["valor_num"], errors="coerce")

    df["exame_norm"] = df["exame"].apply(aplica_regras)
    return df[["exame", "valor_num", "exame_norm"]]


def parse_input(texto: str) -> list[str]:
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    exames = []
    for l in linhas:
        l = re.sub(r"^\d+\s*[\.)-]?\s*", "", l)  # remove numeração
        exames.append(l)
    return exames


def find_best(df: pd.DataFrame, termo: str):
    t = aplica_regras(termo)

    m = df[df["exame_norm"].str.contains(re.escape(t), na=False)]
    if m.empty:
        parts = [p for p in t.split() if len(p) > 2]
        if parts:
            cond = True
            for p in parts:
                cond = cond & df["exame_norm"].str.contains(re.escape(p), na=False)
            m = df[cond]

    if m.empty:
        return None

    m = m.assign(tam=m["exame_norm"].str.len()).sort_values("tam")
    return m.iloc[0]


def moeda_br(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def file_hash(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:12]


# --------- UI ---------

st.title("Orcamentos de exames")
st.write("Online, abre no celular e no tablet. Escolha a tabela, cole os exames e copie o orçamento.")

col1, col2 = st.columns(2)
with col1:
    tabela_escolhida = st.selectbox("Qual tabela usar?", ["LABCLINICA", "SABRY"], key="kind")
with col2:
    arquivo = st.file_uploader("Enviar tabela (.xlsx)", type=["xlsx"], key="upload")

# --- memoria simples: guarda o ultimo arquivo por tipo (LABCLINICA/SABRY) ---
if "saved" not in st.session_state:
    st.session_state.saved = {"LABCLINICA": None, "SABRY": None}
if "df_cache" not in st.session_state:
    st.session_state.df_cache = {"LABCLINICA": None, "SABRY": None}

# se subir arquivo novo, salva
if arquivo is not None:
    b = arquivo.read()
    st.session_state.saved[tabela_escolhida] = {
        "bytes": b,
        "name": arquivo.name,
        "hash": file_hash(b),
    }
    st.session_state.df_cache[tabela_escolhida] = None
    st.success(f"Tabela {tabela_escolhida} salva: {arquivo.name}")

# botao pra limpar
with st.expander("Opcoes"):
    if st.button("Esquecer tabela salva desta opcao"):
        st.session_state.saved[tabela_escolhida] = None
        st.session_state.df_cache[tabela_escolhida] = None
        st.info("Tabela removida.")

# carrega tabela salva automaticamente
saved = st.session_state.saved.get(tabela_escolhida)
if saved is None:
    st.warning("Nenhuma tabela salva para essa opcao. Envie a planilha.")
    df = None
else:
    if st.session_state.df_cache[tabela_escolhida] is None:
        try:
            df = load_table_from_bytes(saved["bytes"], tabela_escolhida)
            st.session_state.df_cache[tabela_escolhida] = df
        except Exception as e:
            st.session_state.df_cache[tabela_escolhida] = None
            st.error(str(e))
            df = None
    else:
        df = st.session_state.df_cache[tabela_escolhida]

    if df is not None:
        st.caption(f"Usando: {saved['name']} | id: {saved['hash']}")

texto = st.text_area(
    "Cole aqui os exames (um por linha)",
    height=220,
    placeholder="Exemplo:\nhemograma\nsodio\npotassio\ncalcio\n...",
)

if st.button("Gerar orçamento"):
    if df is None:
        st.warning("Envie a tabela primeiro.")
    else:
        exames = parse_input(texto)
        itens = []
        total = 0.0

        for ex in exames:
            row = find_best(df, ex)
            if row is None or pd.isna(row["valor_num"]):
                itens.append((ex, None))
            else:
                v = float(row["valor_num"])
                itens.append((ex, v))
                total += v

        linhas = []
        for nome, v in itens:
            if v is None:
                linhas.append(f"{nome} — nao encontrado")
            else:
                linhas.append(f"{nome} — {moeda_br(v)}")
        linhas.append("")
        linhas.append(f"Total: {moeda_br(total)}")

        st.subheader("Orçamento")
        st.code("\n".join(linhas), language="text")

        st.download_button(
            "Baixar orçamento (txt)",
            data="\n".join(linhas),
            file_name="orcamento.txt",
            mime="text/plain",
        )
