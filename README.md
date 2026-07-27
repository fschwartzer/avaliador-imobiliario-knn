# Avaliador Imobiliário por KNN

Aplicativo local em Python/Streamlit para estimar o valor aproximado de um imóvel
a partir de uma planilha Excel.

## Regras implementadas

- Considera apenas linhas cuja `finalidade_oferta` seja igual à finalidade
  informada no aplicativo.
- Descarta `Oferta aluguel`.
- Mantém `Guia ITBI` sem ajuste.
- Ajusta `Oferta` pela fórmula:

  `1 - média(valor_unitário_ITBI) / média(valor_unitário_Oferta)`

- O desconto é calculado dentro da finalidade selecionada e limitado entre
  0% e 20%. O cálculo funciona com uma única oferta, mas o aplicativo apresenta
  alerta de fragilidade amostral.
- O KNN utiliza:
  - `area_construida`;
  - `area_privativa`;
  - `latitude`;
  - `longitude`;
  - `siat_area_total_lote`, quando o avaliando é territorial.
- O peso padrão é 75% para características físicas e 25% para localização.
- Os vizinhos recebem peso inversamente proporcional à distância composta.

## Por que converter para valor unitário

Comparar valores totais diretamente tende a confundir efeito de tamanho com
nível de preço. Por isso, quando a coluna contém valor total, o aplicativo
divide o preço pela área de referência selecionada e executa o KNN em R$/m².
A estimativa final é reconvertida para valor total pela área do avaliando.

## Instalação no Windows

1. Extraia os arquivos para uma pasta.
2. Abra o Prompt de Comando ou PowerShell nessa pasta.
3. Crie um ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

5. Execute:

```powershell
streamlit run app.py
```

Também é possível usar `executar_app.bat` depois de instalar as dependências.

## Colunas

Os nomes não precisam ser exatamente iguais, pois a interface permite mapear
cada campo. São necessários:

- tipo da informação;
- finalidade;
- preço ou valor;
- latitude;
- longitude;
- pelo menos uma área.

## Compatibilidade com o arquivo SIRI fornecido

A estrutura do arquivo `SIRI_pesquisa_padrao` é reconhecida automaticamente.
Para unidades construídas, a configuração recomendada é:

- valor: `valor`;
- área de referência: `area_privativa`;
- características: `area_construida` e `area_privativa`;
- coordenadas: `latitude` e `longitude`;
- área territorial: `siat_area_total_lote`, somente para terrenos.

Não deve ser usada `siat_area_privativa` nesse exemplo, pois a coluna está
zerada em todos os registros.

## Limitação importante

O desconto global dentro de cada finalidade pode refletir diferenças de
composição entre as amostras de ITBI e oferta, e não apenas margem de
negociação. Poucas ofertas tornam o fator instável. Em produção, convém
segmentar também por bairro, padrão, faixa de área e período de coleta.

O resultado é uma estimativa exploratória por comparáveis. Não substitui
tratamento amostral, análise de mercado, validação temporal, diagnóstico de
extrapolação ou laudo de avaliação.
