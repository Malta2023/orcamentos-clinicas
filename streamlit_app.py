def buscar_exame(df, termo):
    palavras = [p for p in termo.split() if len(p) > 3]
    if not palavras:
        return None

    df_temp = df.copy()

    # REGRA: se o usuário NÃO digitou ANGIO, exclui tudo que tem ANGIO
    if "ANGIO" not in termo:
        df_temp = df_temp[~df_temp['NOME_PURIFICADO'].str.contains("ANGIO", na=False)]

    for p in palavras:
        df_temp = df_temp[df_temp['NOME_PURIFICADO'].str.contains(p, na=False, regex=False)]

    if df_temp.empty:
        return None

    df_temp['tam'] = df_temp['NOME_PURIFICADO'].str.len()
    return df_temp.sort_values('tam').iloc[0]
