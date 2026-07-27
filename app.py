from __future__ import annotations

from io import BytesIO
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st

from knn_valuation import (
    ColumnMapping,
    estimate_knn,
    normalize_text,
    prepare_data,
)
from schema_utils import (
    DERIVED_AREA_CONSTRUIDA,
    DERIVED_AREA_LOTE,
    DERIVED_AREA_PRIVATIVA,
    enrich_known_schemas,
    first_existing,
    friendly_column_name,
)


st.set_page_config(
    page_title="Avaliador Imobiliário KNN",
    page_icon="🏠",
    layout="wide",
)

st.title("Avaliador Imobiliário por KNN")
st.caption(
    "Estimativa por vizinhos comparáveis, com ajuste das ofertas em relação às "
    "Guias ITBI e maior peso para similaridade física do que para proximidade."
)


def auto_index(options: list[str], preferred: Iterable[str]) -> int:
    normalized = {normalize_text(value): i for i, value in enumerate(options)}
    for candidate in preferred:
        idx = normalized.get(normalize_text(candidate))
        if idx is not None:
            return idx
    return 0


def optional_column_select(
    label: str,
    columns: list[str],
    preferred: Iterable[str],
    key: str,
) -> str | None:
    options = ["— Não utilizar —"] + columns
    preferred_idx = auto_index(options, preferred)
    selected = st.selectbox(
        label,
        options,
        index=preferred_idx,
        key=key,
        format_func=friendly_column_name,
    )
    return None if selected == "— Não utilizar —" else selected


def money_br(value: float, decimals: int = 2) -> str:
    if not np.isfinite(value):
        return "—"
    formatted = f"{value:,.{decimals}f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def number_br(value: float, decimals: int = 2) -> str:
    if not np.isfinite(value):
        return "—"
    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def dataframe_to_excel(df: pd.DataFrame, diagnostics: dict) -> bytes:
    output = BytesIO()
    diagnostics_df = pd.DataFrame(
        [{"indicador": key, "valor": value} for key, value in diagnostics.items()]
    )
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Comparaveis_KNN", index=False)
        diagnostics_df.to_excel(writer, sheet_name="Diagnosticos", index=False)
    output.seek(0)
    return output.getvalue()


def purpose_suggests_territorial(purpose: str) -> bool:
    normalized = normalize_text(purpose)
    terms = (
        "terreno",
        "gleba",
        "lote",
        "sitio",
        "fazenda",
        "area rural",
        "chacara",
    )
    return any(term in normalized for term in terms)


def valid_coordinate_fraction(series: pd.Series, latitude: bool) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.between(-90, 90) if latitude else numeric.between(-180, 180)
    return float(valid.mean()) if len(valid) else 0.0


uploaded = st.file_uploader(
    "Selecione o arquivo Excel",
    type=["xlsx", "xlsm", "xls"],
    help="O arquivo permanece em memória durante a sessão do aplicativo.",
)

if uploaded is None:
    st.info("Envie um arquivo Excel para iniciar.")
    st.stop()

try:
    excel_file = pd.ExcelFile(uploaded)
except Exception as exc:
    st.error(f"Não foi possível abrir o arquivo: {exc}")
    st.stop()

sheet = st.selectbox("Planilha", excel_file.sheet_names)
try:
    original_df = pd.read_excel(excel_file, sheet_name=sheet)
except Exception as exc:
    st.error(f"Não foi possível ler a planilha selecionada: {exc}")
    st.stop()

if original_df.empty:
    st.error("A planilha selecionada não contém dados.")
    st.stop()

original_df.columns = [str(column) for column in original_df.columns]
df, schema_info = enrich_known_schemas(original_df)
columns = [str(column) for column in df.columns]

if schema_info.siri_detected:
    st.success(
        "Estrutura SIRI reconhecida. As colunas de finalidade, valor, "
        "coordenadas e áreas foram pré-selecionadas automaticamente."
    )

with st.expander("1. Mapeamento das colunas", expanded=True):
    c1, c2, c3 = st.columns(3)

    with c1:
        col_tipo = st.selectbox(
            "Tipo de informação",
            columns,
            index=auto_index(columns, ["tipo_informacao", "tipo_informação"]),
            format_func=friendly_column_name,
        )
        col_finalidade = st.selectbox(
            "Finalidade da oferta",
            columns,
            index=auto_index(
                columns,
                [
                    "finalidade_oferta",
                    "siat_finalidade_descricao",
                    "finalidade",
                    "tipo_imovel",
                ],
            ),
            format_func=friendly_column_name,
        )
        col_valor = st.selectbox(
            "Coluna do valor",
            columns,
            index=auto_index(
                columns,
                [
                    "valor",
                    "valor_total",
                    "valor_oferta",
                    "preco",
                    "preço",
                    "valor_unitario",
                    "valor_unitário",
                ],
            ),
            format_func=friendly_column_name,
        )

    with c2:
        col_area_construida = optional_column_select(
            "Área construída",
            columns,
            [
                DERIVED_AREA_CONSTRUIDA,
                "area_construida",
                "crawler_area_construida",
                "siat_area_construida",
            ],
            "map_area_construida",
        )
        col_area_privativa = optional_column_select(
            "Área privativa",
            columns,
            [
                DERIVED_AREA_PRIVATIVA,
                "area_privativa",
                "crawler_area_privativa",
                "itbacopriv",
            ],
            "map_area_privativa",
        )
        col_area_lote = optional_column_select(
            "Área total do lote",
            columns,
            [
                DERIVED_AREA_LOTE,
                "siat_area_total_lote",
                "area_total_lote",
                "siat_area_terreno",
                "crawler_area_terreno",
            ],
            "map_area_lote",
        )

    with c3:
        col_lat = st.selectbox(
            "Latitude",
            columns,
            index=auto_index(columns, ["latitude", "siat_latitude", "lat"]),
            format_func=friendly_column_name,
        )
        col_lon = st.selectbox(
            "Longitude",
            columns,
            index=auto_index(
                columns,
                ["longitude", "siat_longitude", "lon", "lng"],
            ),
            format_func=friendly_column_name,
        )
        value_kind = st.radio(
            "Natureza da coluna de valor",
            ["Valor total", "Valor unitário por m²"],
            horizontal=False,
        )

if schema_info.notes:
        st.caption(" ".join(schema_info.notes))

with st.expander("Tratamento de ofertas repetidas", expanded=False):
    remove_offer_duplicates = st.toggle(
        "Remover ofertas repetidas e manter apenas o registro mais recente",
        value=True,
        help=(
            "A deduplicação afeta somente as linhas classificadas como Oferta. "
            "Guias ITBI não são removidas."
        ),
    )

    original_columns = [str(column) for column in original_df.columns]
    detected_date_column = first_existing(
        original_columns,
        [
            "data_encaminhamento",
            "data_registro",
            "data_coleta",
            "data_anuncio",
            "data",
        ],
    )
    date_options = ["— Não utilizar —"] + original_columns
    date_default = (
        date_options.index(detected_date_column)
        if detected_date_column in date_options
        else 0
    )
    duplicate_date_column_selected = st.selectbox(
        "Data usada para escolher o registro mais recente",
        date_options,
        index=date_default,
        help="Na estrutura SIRI, a opção recomendada é data_encaminhamento.",
    )
    duplicate_date_column = (
        None
        if duplicate_date_column_selected == "— Não utilizar —"
        else duplicate_date_column_selected
    )

    identifier_candidates = [
        "anuncio_website",
        "imobiliaria_codigo_anuncio",
        "origem_registro",
        "id_anuncio",
        "codigo_anuncio",
        "url_anuncio",
    ]
    detected_identifier_columns = [
        column
        for column in identifier_candidates
        if column in original_columns
    ]
    duplicate_identifier_columns = st.multiselect(
        "Identificadores utilizados, em ordem de prioridade",
        original_columns,
        default=detected_identifier_columns,
        help=(
            "O aplicativo usa o primeiro identificador preenchido em cada linha. "
            "Na estrutura SIRI, a URL do anúncio é priorizada e origem_registro "
            "funciona como alternativa."
        ),
    )

    if remove_offer_duplicates:
        if not duplicate_identifier_columns:
            st.warning(
                "Selecione ao menos uma coluna identificadora para aplicar a "
                "deduplicação."
            )
        else:
            st.caption(
                "Prioridade atual: "
                + " → ".join(f"`{column}`" for column in duplicate_identifier_columns)
            )

if valid_coordinate_fraction(df[col_lat], latitude=True) == 0:
    st.error(
        f"A coluna selecionada como latitude (`{col_lat}`) não contém "
        "coordenadas numéricas válidas."
    )
    st.stop()
if valid_coordinate_fraction(df[col_lon], latitude=False) == 0:
    st.error(
        f"A coluna selecionada como longitude (`{col_lon}`) não contém "
        "coordenadas numéricas válidas."
    )
    st.stop()

mapping = ColumnMapping(
    tipo_informacao=col_tipo,
    finalidade_oferta=col_finalidade,
    valor=col_valor,
    area_construida=col_area_construida,
    area_privativa=col_area_privativa,
    latitude=col_lat,
    longitude=col_lon,
    siat_area_total_lote=col_area_lote,
)

purpose_series = df[col_finalidade].dropna().astype(str).str.strip()
purposes = sorted(value for value in purpose_series.unique() if value)
if not purposes:
    st.error("Não há finalidades válidas na coluna selecionada.")
    st.stop()

st.subheader("2. Imóvel avaliando")

left, middle, right = st.columns(3)

with left:
    selected_purpose = st.selectbox("Finalidade", purposes)
    property_mode = st.selectbox(
        "Tratamento do imóvel",
        ["Automático", "Territorial", "Construído"],
        help=(
            "No modo automático, finalidades com termos como terreno, lote ou "
            "gleba utilizam a área total do lote."
        ),
    )

suggested_territorial = purpose_suggests_territorial(selected_purpose)

with middle:
    target_area_construida = (
        st.number_input(
            "Área construída (m²)",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )
        if col_area_construida
        else 0.0
    )
    target_area_privativa = (
        st.number_input(
            "Área privativa (m²)",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )
        if col_area_privativa
        else 0.0
    )
    target_area_lote = (
        st.number_input(
            "Área total do lote (m²)",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )
        if col_area_lote
        else 0.0
    )

with right:
    target_lat = st.number_input(
        "Latitude",
        min_value=-90.0,
        max_value=90.0,
        value=-30.030000,
        format="%.7f",
    )
    target_lon = st.number_input(
        "Longitude",
        min_value=-180.0,
        max_value=180.0,
        value=-51.230000,
        format="%.7f",
    )

has_built_area = target_area_construida > 0 or target_area_privativa > 0
has_lot_area = target_area_lote > 0
if property_mode == "Territorial":
    territorial = True
elif property_mode == "Construído":
    territorial = False
else:
    territorial = suggested_territorial or (has_lot_area and not has_built_area)

st.caption(
    "Tratamento efetivo: **territorial**." if territorial
    else "Tratamento efetivo: **construído**."
)

possible_reference_columns = [
    column
    for column in [col_area_privativa, col_area_construida, col_area_lote]
    if column is not None
]
if not possible_reference_columns:
    st.error("Mapeie ao menos uma coluna de área.")
    st.stop()

if territorial and col_area_lote in possible_reference_columns:
    preferred_reference = col_area_lote
elif col_area_privativa in possible_reference_columns:
    preferred_reference = col_area_privativa
elif col_area_construida in possible_reference_columns:
    preferred_reference = col_area_construida
else:
    preferred_reference = possible_reference_columns[0]

reference_area_column = st.selectbox(
    "Área de referência para converter o valor total em valor unitário",
    possible_reference_columns,
    index=possible_reference_columns.index(preferred_reference),
    format_func=friendly_column_name,
    key=f"reference_{normalize_text(selected_purpose)}_{property_mode}",
    help=(
        "Para terrenos, use a área total do lote. Para unidades construídas, "
        "use preferencialmente a área privativa ou a área construída."
    ),
)

purpose_mask = df[col_finalidade].map(normalize_text).eq(
    normalize_text(selected_purpose)
)
purpose_types = df.loc[purpose_mask, col_tipo].map(normalize_text)
n_purpose = int(purpose_mask.sum())
n_itbi_purpose = int(purpose_types.eq("guia itbi").sum())
n_offer_purpose = int(purpose_types.eq("oferta").sum())
n_rent_purpose = int(purpose_types.eq("oferta aluguel").sum())

q1, q2, q3, q4 = st.columns(4)
q1.metric("Dados da finalidade", n_purpose)
q2.metric("Guias ITBI", n_itbi_purpose)
q3.metric("Ofertas", n_offer_purpose)
q4.metric("Ofertas de aluguel excluídas", n_rent_purpose)

with st.expander("3. Parâmetros do KNN", expanded=True):
    p1, p2, p3 = st.columns(3)
    with p1:
        k = st.number_input(
            "Número de vizinhos (k)",
            min_value=1,
            max_value=50,
            value=7,
            step=1,
        )
    with p2:
        similarity_weight = st.slider(
            "Peso das características físicas",
            min_value=0.55,
            max_value=0.95,
            value=0.75,
            step=0.05,
            help="O restante do peso é atribuído à localização.",
        )
    with p3:
        distance_power = st.slider(
            "Potência do peso por distância",
            min_value=1.0,
            max_value=4.0,
            value=2.0,
            step=0.5,
            help="Valores maiores concentram mais peso nos vizinhos mais próximos.",
        )

target = {
    "area_construida": target_area_construida if target_area_construida > 0 else None,
    "area_privativa": target_area_privativa if target_area_privativa > 0 else None,
    "siat_area_total_lote": target_area_lote if target_area_lote > 0 else None,
    "latitude": target_lat,
    "longitude": target_lon,
}

if reference_area_column == col_area_construida:
    target[reference_area_column] = target["area_construida"]
elif reference_area_column == col_area_privativa:
    target[reference_area_column] = target["area_privativa"]
elif reference_area_column == col_area_lote:
    target[reference_area_column] = target["siat_area_total_lote"]

calculate = st.button("Calcular estimativa", type="primary", use_container_width=True)

if not calculate:
    with st.expander("Prévia dos dados"):
        st.dataframe(original_df.head(50), use_container_width=True)
    st.stop()

try:
    preparation = prepare_data(
        df=df,
        mapping=mapping,
        selected_purpose=selected_purpose,
        value_kind=value_kind,
        reference_area_column=reference_area_column,
        discount_cap=0.20,
        remove_offer_duplicates=remove_offer_duplicates,
        duplicate_date_column=duplicate_date_column,
        duplicate_identifier_columns=tuple(duplicate_identifier_columns),
    )
    estimate = estimate_knn(
        preparation=preparation,
        mapping=mapping,
        target=target,
        reference_area_column=reference_area_column,
        k=int(k),
        similarity_weight=float(similarity_weight),
        distance_power=float(distance_power),
        territorial=territorial,
    )
except Exception as exc:
    st.error(str(exc))
    st.stop()

st.subheader("Resultado")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Valor total estimado", money_br(estimate.estimated_total_value))
m2.metric(
    "Valor unitário estimado",
    f"{money_br(estimate.estimated_unit_value)}/m²",
)
m3.metric("Desconto aplicado às ofertas", f"{preparation.discount:.1%}")
m4.metric(
    "Vizinhos efetivos",
    number_br(estimate.effective_neighbors, 2),
    help="Cai quando um ou poucos vizinhos concentram grande parte do peso.",
)

if estimate.estimated_unit_value > 0:
    dispersion_pct = estimate.weighted_std_unit / estimate.estimated_unit_value
else:
    dispersion_pct = np.nan

st.caption(
    f"Desvio ponderado entre os vizinhos: "
    f"{money_br(estimate.weighted_std_unit)}/m² "
    f"({dispersion_pct:.1%} da estimativa). "
    "Esse indicador mede dispersão dos comparáveis; não é intervalo de confiança."
)

duplicates_removed = int(
    preparation.diagnostics.get("offer_duplicates_removed", 0)
)
duplicate_groups = int(
    preparation.diagnostics.get("offer_duplicate_groups", 0)
)
if preparation.diagnostics.get("offer_deduplication_enabled"):
    st.info(
        f"Deduplicação: **{duplicates_removed}** registro(s) repetido(s) "
        f"removido(s), distribuídos em **{duplicate_groups}** grupo(s) de "
        "ofertas. Em cada grupo foi mantido o registro mais recente."
    )

deduplication_warning = preparation.diagnostics.get("deduplication_warning")
if deduplication_warning:
    st.warning(deduplication_warning)

warning = preparation.diagnostics.get("discount_warning")
if warning:
    st.warning(warning)

coverage = estimate.diagnostics.get("feature_coverage", {})
for feature_name, stats in coverage.items():
    nearest_gap = float(stats.get("nearest_relative_difference", 0.0))
    if nearest_gap > 0.30:
        st.warning(
            f"Baixa aderência em `{friendly_column_name(feature_name)}`: o dado "
            f"mais próximo difere {nearest_gap:.1%} do avaliando. Os vizinhos "
            f"selecionados variam de {number_br(stats['selected_min'])} a "
            f"{number_br(stats['selected_max'])}, enquanto o avaliando possui "
            f"{number_br(stats['target'])}. A estimativa deve ser tratada como "
            "extrapolação ou interpolação em lacuna amostral."
        )

st.write(
    f"Foram considerados **{estimate.diagnostics['n_candidates']}** candidatos "
    f"válidos e selecionados **{estimate.diagnostics['k_used']}** vizinhos. "
    f"Peso físico: **{similarity_weight:.0%}**; peso geográfico: "
    f"**{1 - similarity_weight:.0%}**."
)

neighbors = estimate.neighbors.copy()
display_columns = [
    "_row_excel",
    col_tipo,
    col_finalidade,
    col_valor,
    reference_area_column,
]
display_columns += [
    column
    for column in [
        duplicate_date_column,
        "_fonte_chave_oferta",
        "_chave_oferta_deduplicacao",
        "_data_registro_deduplicacao",
    ]
    if column
]
display_columns += [
    column
    for column in [
        col_area_construida,
        col_area_privativa,
        col_area_lote,
        col_lat,
        col_lon,
    ]
    if column and column not in display_columns
]
display_columns += [
    "_valor_unitario_original",
    "_valor_unitario_ajustado",
    "_distancia_caracteristicas",
    "_distancia_geografica_km",
    "_distancia_composta",
    "_peso_knn",
    "_contribuicao_valor_unitario",
]
display_columns = [column for column in display_columns if column in neighbors.columns]

rename = {
    "_row_excel": "linha_excel",
    "_valor_unitario_original": "valor_unitario_original",
    "_valor_unitario_ajustado": "valor_unitario_ajustado",
    "_distancia_caracteristicas": "distancia_caracteristicas",
    "_distancia_geografica_km": "distancia_geografica_km",
    "_distancia_composta": "distancia_composta",
    "_peso_knn": "peso_knn",
    "_contribuicao_valor_unitario": "contribuicao_valor_unitario",
}
neighbors_display = neighbors[display_columns].rename(columns=rename)
neighbors_display = neighbors_display.sort_values("peso_knn", ascending=False)

st.subheader("Comparáveis selecionados")
st.dataframe(
    neighbors_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "peso_knn": st.column_config.NumberColumn(format="%.2%%"),
        "distancia_geografica_km": st.column_config.NumberColumn(format="%.3f km"),
        "distancia_caracteristicas": st.column_config.NumberColumn(format="%.3f"),
        "distancia_composta": st.column_config.NumberColumn(format="%.3f"),
        "valor_unitario_original": st.column_config.NumberColumn(format="R$ %.2f"),
        "valor_unitario_ajustado": st.column_config.NumberColumn(format="R$ %.2f"),
        "contribuicao_valor_unitario": st.column_config.NumberColumn(format="R$ %.2f"),
    },
)

map_df = neighbors[[col_lat, col_lon]].rename(
    columns={col_lat: "latitude", col_lon: "longitude"}
)
target_map = pd.DataFrame(
    [{"latitude": target_lat, "longitude": target_lon}]
)
st.subheader("Localização dos vizinhos")
st.map(pd.concat([target_map, map_df], ignore_index=True))

diagnostics = {
    "valor_total_estimado": estimate.estimated_total_value,
    "valor_unitario_estimado": estimate.estimated_unit_value,
    "desvio_ponderado_unitario": estimate.weighted_std_unit,
    "desconto_ofertas": preparation.discount,
    "finalidade": selected_purpose,
    "tratamento_territorial": territorial,
    "area_referencia": reference_area_column,
    "caracteristicas_ativas": ", ".join(estimate.active_features),
    **preparation.diagnostics,
    **estimate.diagnostics,
}

excel_bytes = dataframe_to_excel(neighbors_display, diagnostics)
st.download_button(
    "Baixar comparáveis e diagnósticos em Excel",
    data=excel_bytes,
    file_name="resultado_avaliacao_knn.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

with st.expander("Como o cálculo foi feito"):
    st.markdown(
        """
1. Filtra a finalidade informada.
2. Mantém apenas `Guia ITBI` e `Oferta`; `Oferta aluguel` é descartada.
3. Converte os valores para R$/m² pela área de referência.
4. Calcula o desconto entre os valores unitários de ITBI e oferta, limitado
   a 20%, e aplica esse desconto somente às ofertas.
5. Normaliza as áreas por mediana e intervalo interquartil.
6. Combina distância física e distância geográfica, com maior peso padrão
   para as características do imóvel.
7. Seleciona os `k` vizinhos e calcula a média ponderada pelo inverso da
   distância composta.
        """
    )
