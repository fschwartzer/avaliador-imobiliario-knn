# KNN Valuation Studio — versão 6

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
