# Avaliador Imobiliário por KNN — versão 5

Aplicativo Streamlit para estimar o valor aproximado de um imóvel a partir de
uma planilha Excel com dados de Guia ITBI, Oferta e Oferta aluguel.

## Correções desta versão

- Reconhece automaticamente o segundo formato de exportação SIRI, incluindo:
  - `siat_finalidade_descricao`;
  - `valor_oferta`;
  - `siat_area_terreno` e `crawler_area_terreno`;
  - `siat_area_construida` e `crawler_area_construida`;
  - `siat_latitude` e `siat_longitude`.
- Não seleciona mais `ord_pesquisador` como longitude quando não existe uma
  coluna chamada literalmente `longitude`.
- Cria áreas efetivas combinando os campos SIAT e crawler conforme a origem do
  registro.
- Reconhece automaticamente finalidades como `TERRENO`, `GLEBA` e `LOTE` como
  imóveis territoriais.
- Quando somente a área do lote é informada, o núcleo do KNN usa essa área mesmo
  que o usuário não tenha marcado manualmente o imóvel como territorial.
- A área de referência passa a ser escolhida depois da finalidade; para
  `TERRENO`, o padrão é a área total do lote.
- Valida se as colunas escolhidas como latitude e longitude realmente contêm
  coordenadas numéricas.

## Execução

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

No Streamlit Community Cloud, envie os arquivos para o GitHub e selecione
`app.py` como arquivo principal.

## Configuração esperada para o arquivo SIRI de 27/07/2026

- Tipo: `tipo_informacao`
- Finalidade: `siat_finalidade_descricao`
- Valor: `valor_oferta`
- Área territorial: `Área total do lote — combinada automaticamente`
- Latitude: `siat_latitude`
- Longitude: `siat_longitude`
- Natureza do valor: `Valor total`
- Tratamento: `Automático`

Para a finalidade `TERRENO`, o aplicativo passa a usar automaticamente a área
total do lote como característica e como área de referência.

## Deduplicação das ofertas

A versão 4 remove repetições do mesmo anúncio antes de calcular o desconto e
antes de executar o KNN.

A configuração padrão para arquivos SIRI é:

- data: `data_encaminhamento`;
- identificador prioritário: `anuncio_website`;
- identificadores alternativos: `imobiliaria_codigo_anuncio` e
  `origem_registro`.

A primeira coluna identificadora preenchida em cada linha forma a chave da
oferta. Em cada chave, o aplicativo ordena os registros pela data e mantém
somente o mais recente. Se houver mais de um registro na mesma data, fica a
última linha do arquivo. A deduplicação não é aplicada às Guias ITBI.

A interface permite desativar a regra ou alterar as colunas usadas.

## Estimativa robusta do desconto das ofertas

A versão 5 preserva a comparação por quantis equivalentes entre as
distribuições de valores unitários de Guia ITBI e Oferta, mas troca a média
pela mediana.

Para cada quantil pareado, calcula-se:

`1 - valor_unitário_ITBI / valor_unitário_Oferta`

O desconto adotado é a mediana desses resultados, limitada ao intervalo de
0% a 20%. A mudança reduz a influência de razões extremas sem alterar:

- o filtro por finalidade;
- a exclusão das ofertas de aluguel;
- a deduplicação das ofertas;
- a conversão para valor unitário;
- o teto de 20%;
- a aplicação do desconto somente às ofertas;
- os parâmetros e pesos do KNN.
