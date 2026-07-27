# KNN Valuation Studio — versão 6.1.2

Aplicativo Streamlit para inferência de valores imobiliários por comparáveis.

## Regularização

A versão 6 incorpora:

- K adaptativo;
- objetivo mínimo de vizinhos efetivos;
- limite de peso individual;
- potência padrão de distância reduzida para 1;
- média ponderada robusta por winsorização baseada em mediana e MAD;
- alertas graduados de extrapolação;
- pontuação de confiança;
- backtesting leave-one-out;
- exclusão opcional de todos os registros do mesmo imóvel no backtesting.

## Backtesting

A configuração recomendada é avaliar somente as Guias ITBI e excluir grupos
pela inscrição imobiliária. Assim, o sistema não mede o desempenho usando o
próprio imóvel ou outro registro da mesma unidade como comparável.

São calculados:

- MAE;
- mediana do erro absoluto;
- RMSE;
- MdAPE;
- MAPE;
- percentil 90 do erro percentual absoluto;
- viés mediano;
- R²;
- COD;
- PRD.

## Interface

A interface segue uma estrutura de painel contemporâneo e sóbrio:

- configuração técnica na barra lateral;
- formulário principal focado no avaliando;
- cartões de indicadores;
- navegação em abas;
- diagnóstico visual de confiabilidade;
- comparáveis e cálculos exportáveis para Excel.

## Execução

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Observação técnica

A regularização reduz a sensibilidade a vizinhos isolados e valores extremos,
mas não corrige falta estrutural de dados. Quando a área do avaliando estiver
fora da faixa amostral ou os comparáveis mais próximos forem muito diferentes,
o aplicativo sinaliza extrapolação e reduz a pontuação de confiança.


## Testada nos imóveis territoriais

Nos tratamentos territoriais, o KNN utiliza obrigatoriamente:

- área total do lote;
- testada;
- latitude;
- longitude.

A estrutura SIRI é reconhecida automaticamente. O aplicativo cria uma coluna
efetiva de testada, priorizando `anuncio_testada` nas ofertas e
`siat_testada_terreno` nas Guias ITBI.

Área do lote e testada são normalizadas separadamente por estatísticas
robustas. Dentro do peso reservado às características físicas, as duas
características têm participação igual. Com peso físico de 75%, área e testada
respondem por 37,5% da distância composta cada, enquanto a localização responde
pelos 25% restantes.

A testada também participa dos alertas de extrapolação, da tabela de cobertura
e do backtesting. Casos territoriais sem testada válida não entram no
backtesting.


## Correção de implantação no Streamlit Cloud

A versão 6.1.1 evita o `ImportError` causado pela publicação parcial dos
arquivos. Os três módulos abaixo formam uma unidade e devem ser atualizados
no mesmo commit:

- `app.py`;
- `knn_valuation.py`;
- `schema_utils.py`.

O aplicativo verifica a versão interna desses módulos. Quando identifica uma
mistura de versões, apresenta uma mensagem de diagnóstico em vez de encerrar
com um erro de importação redigido pelo Streamlit Cloud.

Após o commit no GitHub:

1. abra **Manage app**;
2. confirme que a branch e o arquivo principal estão corretos;
3. use **Reboot app**;
4. se necessário, limpe o cache do aplicativo.


## Correção da escala percentual

A versão 6.1.2 corrige a apresentação dos campos:

- `erro_percentual`;
- `erro_percentual_absoluto`;
- `peso_maximo`.

Internamente, os valores permanecem como proporções decimais. Por exemplo,
`-0,23` representa `-23%`. Na tabela do Streamlit, essas proporções são
multiplicadas por 100 antes da inclusão do símbolo `%`.

Na exportação para Excel, as proporções permanecem decimais, mas as células
recebem o formato percentual nativo. Assim, o Excel mostra `-23,00%` e mantém
o valor numérico correto para fórmulas posteriores.

MdAPE, MAPE, P90 do erro percentual absoluto e viés mediano também recebem
formato percentual na planilha de métricas.
