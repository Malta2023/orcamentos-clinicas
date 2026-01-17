import pandas as pd
import unicodedata
import re

# ================= FUNÇÕES BASE =================

def purificar(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', texto)
    texto = texto.encode('ASCII', 'ignore').decode('ASCII')
    texto = texto.upper()
    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def contem_algo(texto, lista):
    return any(p in texto for p in lista)

# ================= SINÔNIMOS DE REGIÃO =================

SINONIMOS = {
    "CRANIO": ["CABECA", "CRANIO", "ENCEFALO"],
    "COLUNA": ["COLUNA", "COSTAS", "LOMBAR", "CERVICAL", "TORACICA"],
    "ABDOMEN": ["ABDOMEN", "BARRIGA", "ABDOME"],
    "TORAX": ["TORAX", "PEITO"],
    "PELVE": ["PELVE", "BACIA"],
    "JOELHO": ["JOELHO"],
    "OMBRO": ["OMBRO"],
}

def normalizar_regiao(texto):
    for regiao, termos in SINONIMOS.items():
        if contem_algo(texto, termos):
            return regiao
    return ""

# ================= CARREGA TABELA =================

df = pd.read_csv("/mnt/data/TABELA_LABCLINICA_ATUALIZADA160126.csv")
df["NOME_PURIFICADO"] = df.iloc[:,0].apply(purificar)

# remove lixo
df = df[~df["NOME_PURIFICADO"].str.contains("TAXA|URG|ANGIO", na=False)]

# ================= PROCESSAMENTO =================

def processar_exame(texto_usuario):
    texto = purificar(texto_usuario)

    # identifica tipo
    if contem_algo(texto, ["RESSONANCIA"]):
        tipo = "RESSONANCIA"
        preco_fixo = 545.00
    elif contem_algo(texto, ["TOMOGRAFIA", "TC"]):
        tipo = "TOMOGRAFIA"
        preco_fixo = 165.00
    elif contem_algo(texto, ["ULTRASSOM", "ULTRASONOGRAFIA", "US"]):
        tipo = "ULTRASSOM"
        preco_fixo = None
    else:
        return "❌ Não consegui identificar o tipo de exame."

    # identifica região
    regiao = normalizar_regiao(texto)

    # se não informou região
    if not regiao:
        return f"👉 Você quer {tipo.lower()}, mas de qual região?"

    # busca na tabela
    df_busca = df[df["NOME_PURIFICADO"].str.contains(tipo, na=False)]
    df_busca = df_busca[df_busca["NOME_PURIFICADO"].str.contains(regiao, na=False)]

    if df_busca.empty:
        return f"❌ Não encontrei {tipo.lower()} para a região informada. Pode explicar melhor?"

    exame = df_busca.iloc[0]
    nome = exame.iloc[0]

    if preco_fixo:
        preco = preco_fixo
    else:
        p_str = str(exame.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.')
        nums = re.findall(r"\d+\.\d+|\d+", p_str)
        preco = float(nums[0]) if nums else 0.0

    return f"✅ {nome}\n💰 Valor: R$ {preco:.2f}"

# ================= EXEMPLO DE USO =================

# print(processar_exame("ressonancia"))
# print(processar_exame("ressonancia da cabeca"))
# print(processar_exame("tc torax"))
# print(processar_exame("us abdomen"))
