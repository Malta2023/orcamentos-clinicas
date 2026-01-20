import re

# Dicionário de exames da tabela Saúde Dirceu (extraído das imagens subidas)
db_exames = {
    "urocultura com antibiograma": 34.60,
    "estradiol e2": 16.32,
    "estrona e1": 29.00,
    "testosterona total": 24.48,
    "testosterona livre": 23.12,
    "vitamina b12": 34.00,
    "cortisol 8 hs": 40.80,
    "fibrinogenio": 59.50,
    "pcr proteina c ultrasensivel": 26.40,
    "magnesio no soro": 6.80,
    "sdhea sulfato dehidroepiandrosterona": 34.00,
    "homocisteina": 34.00,
    "t3 livre": 13.60,
    "t3 total": 25.00,
    "zinco serico": 27.20,
    "dht dihidrotestosterona dht": 40.80,
    "shbg globulina de hormonio sexuais": 40.80,
    "anti tg anti tireoglobulina": 42.00,
}

# Sinônimos para facilitar buscas (baseado em variações comuns)
sinonimos = {
    "anti tpo": "anticorpos anti tireoperoxidase",
    "vitamina d": "vitamina d 25 hidroxi",
    "anti-tpo": "anticorpos anti tireoperoxidase",
    "vit d": "vitamina d 25 hidroxi",
    "estradiol": "estradiol e2",
    "estriol": "estrona e1",  # Ajuste se necessário
    "testo total": "testosterona total",
    "testo livre": "testosterona livre",
    "cortisol": "cortisol 8 hs",
    "fibrinogeno": "fibrinogenio",
    "pcr ultrasensivel": "pcr proteina c ultrasensivel",
    "magnesio": "magnesio no soro",
    "dhea s": "sdhea sulfato dehidroepiandrosterona",
    "t3l": "t3 livre",
    "t3t": "t3 total",
    "zinco": "zinco serico",
    "dht": "dht dihidrotestosterona dht",
    "shbg": "shbg globulina de hormonio sexuais",
    "anti tg": "anti tg anti tireoglobulina",
    # Adicione mais sinônimos conforme necessário
}

# Preços estimados para não encontrados na tabela (baseado em similares da própria tabela)
precos_estimados = {
    "anticorpos anti tireoperoxidase": 42.00,  # Similar a Anti TG
    "vitamina d 25 hidroxi": 34.00,  # Similar a Vit B12
}

def remove_accents(texto):
    # Função manual para remover acentos comuns em português
    accents = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
        'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
        'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C', 'Ñ': 'N',
    }
    return ''.join(accents.get(c, c) for c in texto)

def normalizar_texto(texto):
    texto = remove_accents(texto).lower()
    texto = re.sub(r'[^a-z0-9 ]', '', texto)
    return ' '.join(texto.split())

def levenshtein_dist(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_dist(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def buscar_exame(input_nome, limiar=2):  # Limiar baixo para precisão
    input_norm = normalizar_texto(input_nome)
    if input_norm in sinonimos:
        input_norm = normalizar_texto(sinonimos[input_norm])
    
    best_match = None
    min_dist = float('inf')
    for db_nome in db_exames:
        db_norm = normalizar_texto(db_nome)
        dist = levenshtein_dist(input_norm, db_norm)
        if dist < min_dist:
            min_dist = dist
            best_match = db_nome
    if min_dist <= limiar:
        return best_match, db_exames[best_match], False  # Encontrado
    
    # Checa em estimados (opcional; remova se não quiser estimativas)
    for est_nome in precos_estimados:
        est_norm = normalizar_texto(est_nome)
        dist = levenshtein_dist(input_norm, est_norm)
        if dist <= limiar:
            return est_nome, precos_estimados[est_nome], True  # Estimado
    return None, None, False

def calcular_orcamento(lista_exames):
    total = 0.0
    resultados = []
    for exame in lista_exames:
        encontrado, preco, estimado = buscar_exame(exame)
        if encontrado:
            status = "Estimado" if estimado else "Encontrado na tabela"
            resultados.append(f"{exame} → {encontrado}: R$ {preco:.2f} ({status})")
            total += preco
        else:
            resultados.append(f"{exame}: Não encontrado na tabela. Tente variações no nome.")
    resultados.append(f"Total: R$ {total:.2f}")
    return "\n".join(resultados)

# Exemplo de uso com a lista completa da tabela
exames_desejados = [
    "Urocultura COM ANTIBIOGRAMA", "ESTRADIOL - E2", "ESTRONA (E1)", "TESTOSTERONA TOTAL",
    "TESTOSTERONA LIVRE", "anti tpo", "VITAMINA B12", "CORTISOL 8 hs", "FIBRINOGENIO",
    "PCR PROTEINA C ULTRASENSIVEL", "MAGNÉSIO NO SORO", "Vitamina D", "SDHEA (Sulfato Dehidroepiandrosterona)",
    "HOMOCISTEINA", "T3 LIVRE", "T3 TOTAL", "ZINCO SÉRICO", "DHT DIHIDROTESTOSTERONA DHT",
    "SHBG (Globulina de hormônio sexuais)", "Anti TG anti tireoglobulina"
]

print(calcular_orcamento(exames_desejados))
