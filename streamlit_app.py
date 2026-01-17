function buscarExameMaisProximo(exameDigitado, regiaoDigitada) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const aba = ss.getSheetByName("TABELA");
  const dados = aba.getDataRange().getValues();

  exameDigitado = normalizarTexto(exameDigitado);
  regiaoDigitada = normalizarTexto(regiaoDigitada);

  let melhorResultado = null;
  let menorDistancia = 9999;

  for (let i = 1; i < dados.length; i++) {
    const exameTabela = normalizarTexto(dados[i][0]);
    const regiaoTabela = normalizarTexto(dados[i][1]);
    const valor = dados[i][2];

    if (regiaoTabela !== regiaoDigitada) continue;

    const distancia = distanciaLevenshtein(exameDigitado, exameTabela);

    if (distancia < menorDistancia) {
      menorDistancia = distancia;
      melhorResultado = {
        exame: dados[i][0],
        regiao: dados[i][1],
        valor: valor
      };
    }
  }

  if (!melhorResultado || menorDistancia > 6) {
    return "Exame não encontrado na tabela";
  }

  return melhorResultado;
}

function normalizarTexto(texto) {
  return texto
    .toString()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function distanciaLevenshtein(a, b) {
  const matriz = [];

  for (let i = 0; i <= b.length; i++) {
    matriz[i] = [i];
  }

  for (let j = 0; j <= a.length; j++) {
    matriz[0][j] = j;
  }

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matriz[i][j] = matriz[i - 1][j - 1];
      } else {
        matriz[i][j] = Math.min(
          matriz[i - 1][j - 1] + 1,
          matriz[i][j - 1] + 1,
          matriz[i - 1][j] + 1
        );
      }
    }
  }

  return matriz[b.length][a.length];
}
