# Avaliador Imobiliário por KNN — versão 3

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
