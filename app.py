from __future__ import annotations

from io import BytesIO
from typing import Iterable
import hashlib

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="KNN Valuation Studio",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    import knn_valuation as _knn
    import schema_utils as _schema
except Exception as exc:
    st.error(
        "Não foi possível carregar os módulos internos do aplicativo. "
        "Substitua no repositório os arquivos app.py, knn_valuation.py e "
        "schema_utils.py pelo mesmo pacote da versão 6.1.1."
    )
    st.code(f"{type(exc).__name__}: {exc}")
    st.stop()

_required_knn = {
    "BacktestResult",
    "ColumnMapping",
    "EstimateResult",
    "PreparationResult",
    "backtest_knn",
    "estimate_knn",
    "normalize_text",
    "prepare_data",
}
_required_schema = {
    "DERIVED_AREA_CONSTRUIDA",
    "DERIVED_AREA_LOTE",
    "DERIVED_AREA_PRIVATIVA",
    "DERIVED_TESTADA",
    "enrich_known_schemas",
    "first_existing",
    "friendly_column_name",
}

_missing_knn = sorted(name for name in _required_knn if not hasattr(_knn, name))
_missing_schema = sorted(
    name for name in _required_schema if not hasattr(_schema, name)
)

_knn_version = getattr(_knn, "MODULE_API_VERSION", "anterior")
_schema_version = getattr(_schema, "MODULE_API_VERSION", "anterior")

if (
    _missing_knn
    or _missing_schema
    or _knn_version != "6.1.1"
    or _schema_version != "6.1.1"
):
    st.error("Os arquivos publicados pertencem a versões diferentes.")
    st.markdown(
        """
        O `app.py` da versão 6.1.1 precisa ser publicado junto com os arquivos
        `knn_valuation.py` e `schema_utils.py` fornecidos no mesmo pacote.
        Substitua os três arquivos no GitHub, confirme o commit e reinicie o app.
        """
    )
    st.code(
        "\n".join(
            [
                f"knn_valuation.py: versão {_knn_version}",
                f"schema_utils.py: versão {_schema_version}",
                "Itens ausentes no KNN: "
                + (", ".join(_missing_knn) if _missing_knn else "nenhum"),
                "Itens ausentes no schema: "
                + (", ".join(_missing_schema) if _missing_schema else "nenhum"),
            ]
        )
    )
    st.stop()

BacktestResult = _knn.BacktestResult
ColumnMapping = _knn.ColumnMapping
EstimateResult = _knn.EstimateResult
PreparationResult = _knn.PreparationResult
backtest_knn = _knn.backtest_knn
estimate_knn = _knn.estimate_knn
normalize_text = _knn.normalize_text
prepare_data = _knn.prepare_data

DERIVED_AREA_CONSTRUIDA = _schema.DERIVED_AREA_CONSTRUIDA
DERIVED_AREA_LOTE = _schema.DERIVED_AREA_LOTE
DERIVED_AREA_PRIVATIVA = _schema.DERIVED_AREA_PRIVATIVA
DERIVED_TESTADA = _schema.DERIVED_TESTADA
enrich_known_schemas = _schema.enrich_known_schemas
first_existing = _schema.first_existing
friendly_column_name = _schema.friendly_column_name


CUSTOM_CSS = """
<style>
:root {
    --ink: #172033;
    --muted: #667085;
    --line: #E5EAF1;
    --surface: #FFFFFF;
    --canvas: #F5F7FA;
    --navy: #173B57;
    --teal: #0E7C7B;
    --soft-teal: #E9F5F4;
    --amber: #A15C00;
    --soft-amber: #FFF4E5;
    --red: #B42318;
    --soft-red: #FEECEB;
}
.stApp {
    background:
        radial-gradient(circle at 85% 5%, rgba(14,124,123,.08), transparent 24rem),
        var(--canvas);
    color: var(--ink);
}
.block-container {
    max-width: 1480px;
    padding-top: 1.8rem;
    padding-bottom: 4rem;
}
[data-testid="stSidebar"] {
    border-right: 1px solid var(--line);
    background: rgba(255,255,255,.94);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.4rem;
}
.hero {
    position: relative;
    overflow: hidden;
    padding: 2rem 2.2rem;
    border-radius: 22px;
    border: 1px solid rgba(23,59,87,.14);
    background:
        linear-gradient(135deg, rgba(255,255,255,.98), rgba(236,246,246,.92));
    box-shadow: 0 18px 45px rgba(23,59,87,.08);
    margin-bottom: 1.4rem;
}
.hero:after {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -80px;
    top: -120px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(14,124,123,.17), rgba(23,59,87,.04));
}
.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: .45rem;
    padding: .32rem .68rem;
    border-radius: 999px;
    background: rgba(14,124,123,.10);
    color: #096968;
    font-size: .76rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
}
.hero h1 {
    font-size: clamp(2rem, 3.5vw, 3.25rem);
    line-height: 1.02;
    letter-spacing: -.045em;
    margin: .85rem 0 .7rem;
    max-width: 900px;
    color: var(--ink);
}
.hero p {
    max-width: 850px;
    color: var(--muted);
    font-size: 1.02rem;
    line-height: 1.65;
    margin: 0;
}
.section-title {
    margin: 1.3rem 0 .75rem;
}
.section-title h2 {
    font-size: 1.28rem;
    margin: 0;
    letter-spacing: -.02em;
}
.section-title p {
    color: var(--muted);
    margin: .25rem 0 0;
    font-size: .91rem;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,.92);
    border: 1px solid var(--line);
    padding: 1rem 1.05rem;
    border-radius: 16px;
    box-shadow: 0 8px 25px rgba(23,59,87,.045);
}
[data-testid="stMetricLabel"] {
    color: var(--muted);
}
[data-testid="stMetricValue"] {
    color: var(--ink);
    letter-spacing: -.03em;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--line) !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,.78);
    box-shadow: 0 10px 28px rgba(23,59,87,.035);
}
.stButton > button, .stDownloadButton > button {
    border-radius: 12px;
    font-weight: 700;
    border: 0;
    min-height: 2.8rem;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--navy), var(--teal));
    box-shadow: 0 10px 22px rgba(14,124,123,.18);
}
.stTabs [data-baseweb="tab-list"] {
    gap: .45rem;
    background: rgba(255,255,255,.72);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: .35rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: .45rem .9rem;
}
.stTabs [aria-selected="true"] {
    background: var(--soft-teal);
    color: var(--teal);
}
.risk-card {
    border-radius: 16px;
    padding: 1rem 1.1rem;
    border: 1px solid var(--line);
    background: #fff;
    min-height: 128px;
}
.risk-card.low { border-left: 5px solid #0E7C7B; }
.risk-card.moderate { border-left: 5px solid #D97706; }
.risk-card.high { border-left: 5px solid #B42318; }
.risk-label {
    color: var(--muted);
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .05em;
    text-transform: uppercase;
}
.risk-value {
    font-size: 1.5rem;
    font-weight: 800;
    margin: .25rem 0;
    color: var(--ink);
}
.risk-text {
    color: var(--muted);
    font-size: .88rem;
    line-height: 1.45;
}
.inline-note {
    padding: .9rem 1rem;
    border-radius: 14px;
    background: rgba(23,59,87,.045);
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: .9rem;
}
.small-muted { color: var(--muted); font-size: .84rem; }
div[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def auto_index(options: list[str], preferred: Iterable[str]) -> int:
    normalized = {normalize_text(value): i for i, value in enumerate(options)}
    for candidate in preferred:
        found = normalized.get(normalize_text(candidate))
        if found is not None:
            return found
    return 0


def optional_column_select(
    label: str,
    columns: list[str],
    preferred: Iterable[str],
    key: str,
) -> str | None:
    options = ["— Não utilizar —"] + columns
    selected = st.selectbox(
        label,
        options,
        index=auto_index(options, preferred),
        key=key,
        format_func=friendly_column_name,
    )
    return None if selected == "— Não utilizar —" else selected


def money_br(value: float, decimals: int = 2) -> str:
    if not np.isfinite(value):
        return "—"
    text = f"{value:,.{decimals}f}"
    return "R$ " + text.replace(",", "X").replace(".", ",").replace("X", ".")


def number_br(value: float, decimals: int = 2) -> str:
    if not np.isfinite(value):
        return "—"
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def percent_br(value: float, decimals: int = 1) -> str:
    if not np.isfinite(value):
        return "—"
    return f"{value * 100:.{decimals}f}%".replace(".", ",")


def purpose_suggests_territorial(purpose: str) -> bool:
    normalized = normalize_text(purpose)
    return any(
        term in normalized
        for term in (
            "terreno",
            "gleba",
            "lote",
            "sitio",
            "fazenda",
            "area rural",
            "chacara",
        )
    )


def dataframe_to_excel(
    neighbors: pd.DataFrame,
    diagnostics: dict,
    backtest: BacktestResult | None,
) -> bytes:
    output = BytesIO()
    diagnostics_df = pd.DataFrame(
        [{"indicador": key, "valor": str(value)} for key, value in diagnostics.items()]
    )
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        neighbors.to_excel(writer, sheet_name="Comparaveis_KNN", index=False)
        diagnostics_df.to_excel(writer, sheet_name="Diagnosticos", index=False)
        if backtest is not None:
            backtest.predictions.to_excel(
                writer, sheet_name="Backtesting_Previsoes", index=False
            )
            pd.DataFrame(
                [{"metrica": key, "valor": value} for key, value in backtest.metrics.items()]
            ).to_excel(writer, sheet_name="Backtesting_Metricas", index=False)
    output.seek(0)
    return output.getvalue()


def risk_card(level: str, confidence: int, reasons: list[str]) -> None:
    css_level = {"baixo": "low", "moderado": "moderate", "alto": "high"}.get(
        level, "moderate"
    )
    reason = reasons[0] if reasons else "Boa aderência aos dados observados."
    st.markdown(
        f"""
        <div class="risk-card {css_level}">
            <div class="risk-label">Confiabilidade da estimativa</div>
            <div class="risk-value">{level.capitalize()} risco · {confidence}/100</div>
            <div class="risk-text">{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <span class="eyebrow">KNN Valuation Studio · versão 6.1.1</span>
        <h1>Avaliação por comparáveis com regularização e validação realista.</h1>
        <p>
            K adaptativo, limite de influência individual, média robusta por MAD,
            diagnóstico de extrapolação e backtesting com exclusão do próprio imóvel.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Base de dados")
    uploaded = st.file_uploader(
        "Arquivo Excel",
        type=["xlsx", "xlsm", "xls"],
        help="O arquivo é processado em memória durante a sessão.",
    )

if uploaded is None:
    st.info(
        "Envie uma planilha Excel na barra lateral. A interface reconhecerá "
        "automaticamente a estrutura SIRI quando disponível."
    )
    st.stop()

file_bytes = uploaded.getvalue()
file_signature = hashlib.sha1(file_bytes).hexdigest()
try:
    excel_file = pd.ExcelFile(BytesIO(file_bytes))
except Exception as exc:
    st.error(f"Não foi possível abrir o arquivo: {exc}")
    st.stop()

with st.sidebar:
    sheet = st.selectbox("Planilha", excel_file.sheet_names)

run_signature = f"{file_signature}:{sheet}"
if st.session_state.get("_file_signature") != run_signature:
    st.session_state["_file_signature"] = run_signature
    st.session_state.pop("valuation_run", None)
    st.session_state.pop("backtest_run", None)

try:
    original_df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet)
except Exception as exc:
    st.error(f"Não foi possível ler a planilha: {exc}")
    st.stop()

if original_df.empty:
    st.error("A planilha selecionada não contém dados.")
    st.stop()

original_df.columns = [str(column) for column in original_df.columns]
df, schema_info = enrich_known_schemas(original_df)
columns = [str(column) for column in df.columns]
original_columns = [str(column) for column in original_df.columns]

with st.sidebar:
    if schema_info.siri_detected:
        st.success("Estrutura SIRI reconhecida.")

    with st.expander("Mapeamento de colunas", expanded=False):
        col_tipo = st.selectbox(
            "Tipo de informação",
            columns,
            index=auto_index(columns, ["tipo_informacao", "tipo_informação"]),
            format_func=friendly_column_name,
        )
        col_finalidade = st.selectbox(
            "Finalidade",
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
            "Valor",
            columns,
            index=auto_index(
                columns,
                [
                    "valor",
                    "valor_oferta",
                    "valor_total",
                    "preco",
                    "valor_unitario",
                ],
            ),
            format_func=friendly_column_name,
        )
        col_area_construida = optional_column_select(
            "Área construída",
            columns,
            [
                DERIVED_AREA_CONSTRUIDA,
                "area_construida",
                "crawler_area_construida",
                "siat_area_construida",
            ],
            "v6_area_construida",
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
            "v6_area_privativa",
        )
        col_area_lote = optional_column_select(
            "Área do lote",
            columns,
            [
                DERIVED_AREA_LOTE,
                "siat_area_total_lote",
                "siat_area_terreno",
                "crawler_area_terreno",
            ],
            "v6_area_lote",
        )
        col_testada = optional_column_select(
            "Testada",
            columns,
            [
                DERIVED_TESTADA,
                "testada",
                "testada_terreno",
                "siat_testada_terreno",
                "anuncio_testada",
            ],
            "v61_testada",
        )
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
                columns, ["longitude", "siat_longitude", "lon", "lng"]
            ),
            format_func=friendly_column_name,
        )
        value_kind = st.radio(
            "Natureza do valor",
            ["Valor total", "Valor unitário por m²"],
        )

    with st.expander("Ofertas repetidas", expanded=False):
        remove_offer_duplicates = st.toggle(
            "Manter apenas o registro mais recente",
            value=True,
        )
        detected_date = first_existing(
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
        selected_date = st.selectbox(
            "Data de referência",
            date_options,
            index=date_options.index(detected_date) if detected_date else 0,
        )
        duplicate_date_column = (
            None if selected_date == "— Não utilizar —" else selected_date
        )
        identifier_candidates = [
            "anuncio_website",
            "imobiliaria_codigo_anuncio",
            "origem_registro",
            "idf_registro",
            "id_anuncio",
            "codigo_anuncio",
        ]
        defaults = [
            column for column in identifier_candidates if column in original_columns
        ]
        duplicate_identifier_columns = st.multiselect(
            "Identificadores, por prioridade",
            original_columns,
            default=defaults,
        )

    with st.expander("Regularização do KNN", expanded=True):
        min_k = st.number_input(
            "K inicial",
            min_value=3,
            max_value=30,
            value=7,
            step=1,
        )
        max_k = st.number_input(
            "K máximo adaptativo",
            min_value=int(min_k),
            max_value=80,
            value=max(30, int(min_k)),
            step=1,
        )
        min_effective = st.slider(
            "Mínimo de vizinhos efetivos",
            min_value=2.0,
            max_value=15.0,
            value=5.0,
            step=0.5,
        )
        max_weight = st.slider(
            "Peso máximo por comparável",
            min_value=0.10,
            max_value=0.50,
            value=0.30,
            step=0.05,
        )
        similarity_weight = st.slider(
            "Peso das características físicas",
            min_value=0.55,
            max_value=0.95,
            value=0.75,
            step=0.05,
        )
        distance_power = st.slider(
            "Potência da distância",
            min_value=0.5,
            max_value=2.5,
            value=1.0,
            step=0.25,
        )
        robust_threshold = st.slider(
            "Limiar robusto — MAD",
            min_value=1.5,
            max_value=4.0,
            value=2.5,
            step=0.25,
        )

mapping = ColumnMapping(
    tipo_informacao=col_tipo,
    finalidade_oferta=col_finalidade,
    valor=col_valor,
    area_construida=col_area_construida,
    area_privativa=col_area_privativa,
    latitude=col_lat,
    longitude=col_lon,
    siat_area_total_lote=col_area_lote,
    testada=col_testada,
)

purpose_series = df[col_finalidade].dropna().astype(str).str.strip()
purposes = sorted(value for value in purpose_series.unique() if value)
if not purposes:
    st.error("Não foram encontradas finalidades válidas.")
    st.stop()

st.markdown(
    """
    <div class="section-title">
        <h2>Imóvel avaliando</h2>
        <p>Defina a tipologia e as características do imóvel que será estimado.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("valuation_form"):
    with st.container(border=True):
        row1 = st.columns([1.2, 1, 1])
        with row1[0]:
            selected_purpose = st.selectbox("Finalidade", purposes)
        suggested_territorial = purpose_suggests_territorial(selected_purpose)
        with row1[1]:
            property_mode = st.radio(
                "Tratamento",
                ["Territorial", "Unidade construída"],
                index=0 if suggested_territorial else 1,
                horizontal=True,
            )
        territorial = property_mode == "Territorial"
        with row1[2]:
            area_options = [
                column
                for column in (
                    col_area_lote if territorial else None,
                    col_area_privativa if not territorial else None,
                    col_area_construida if not territorial else None,
                )
                if column
            ]
            if not area_options:
                st.error("Mapeie uma área compatível com o tratamento selecionado.")
                st.stop()
            reference_area_column = st.selectbox(
                "Área de referência do valor",
                area_options,
                format_func=friendly_column_name,
            )

        if territorial:
            row2 = st.columns(4)
            with row2[0]:
                target_area_lote = (
                    st.number_input(
                        "Área total do lote (m²)",
                        min_value=0.0,
                        value=0.0,
                        step=10.0,
                    )
                    if col_area_lote
                    else 0.0
                )
            with row2[1]:
                target_testada = (
                    st.number_input(
                        "Testada (m)",
                        min_value=0.0,
                        value=0.0,
                        step=0.5,
                        help=(
                            "Comprimento da frente principal do imóvel. "
                            "Participa da similaridade física do KNN."
                        ),
                    )
                    if col_testada
                    else 0.0
                )
            with row2[2]:
                target_lat = st.number_input(
                    "Latitude",
                    min_value=-90.0,
                    max_value=90.0,
                    value=-30.0300000,
                    format="%.7f",
                )
            with row2[3]:
                target_lon = st.number_input(
                    "Longitude",
                    min_value=-180.0,
                    max_value=180.0,
                    value=-51.2300000,
                    format="%.7f",
                )
            target_area_privativa = 0.0
            target_area_construida = 0.0
        else:
            row2 = st.columns(4)
            with row2[0]:
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
            with row2[1]:
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
            with row2[2]:
                target_lat = st.number_input(
                    "Latitude",
                    min_value=-90.0,
                    max_value=90.0,
                    value=-30.0300000,
                    format="%.7f",
                )
            with row2[3]:
                target_lon = st.number_input(
                    "Longitude",
                    min_value=-180.0,
                    max_value=180.0,
                    value=-51.2300000,
                    format="%.7f",
                )
            target_area_lote = 0.0
            target_testada = 0.0

        calculate = st.form_submit_button(
            "Calcular estimativa regularizada",
            type="primary",
            use_container_width=True,
        )

purpose_mask = df[col_finalidade].map(normalize_text).eq(
    normalize_text(selected_purpose)
)
types = df.loc[purpose_mask, col_tipo].map(normalize_text)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Dados da finalidade", int(purpose_mask.sum()))
c2.metric("Guias ITBI", int(types.eq("guia itbi").sum()))
c3.metric("Ofertas", int(types.eq("oferta").sum()))
c4.metric("Aluguéis excluídos", int(types.eq("oferta aluguel").sum()))

target = {
    "area_construida": target_area_construida if target_area_construida > 0 else None,
    "area_privativa": target_area_privativa if target_area_privativa > 0 else None,
    "siat_area_total_lote": target_area_lote if target_area_lote > 0 else None,
    "testada": target_testada if target_testada > 0 else None,
    "latitude": target_lat,
    "longitude": target_lon,
}
if reference_area_column == col_area_construida:
    target[reference_area_column] = target["area_construida"]
elif reference_area_column == col_area_privativa:
    target[reference_area_column] = target["area_privativa"]
elif reference_area_column == col_area_lote:
    target[reference_area_column] = target["siat_area_total_lote"]

if calculate:
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
            min_k=int(min_k),
            max_k=int(max_k),
            min_effective_neighbors=float(min_effective),
            similarity_weight=float(similarity_weight),
            distance_power=float(distance_power),
            max_individual_weight=float(max_weight),
            robust_mad_threshold=float(robust_threshold),
            territorial=territorial,
        )
        st.session_state["valuation_run"] = {
            "preparation": preparation,
            "estimate": estimate,
            "mapping": mapping,
            "target": target,
            "reference_area_column": reference_area_column,
            "territorial": territorial,
            "purpose": selected_purpose,
            "settings": {
                "min_k": int(min_k),
                "max_k": int(max_k),
                "min_effective": float(min_effective),
                "similarity_weight": float(similarity_weight),
                "distance_power": float(distance_power),
                "max_weight": float(max_weight),
                "robust_threshold": float(robust_threshold),
            },
            "columns": {
                "tipo": col_tipo,
                "finalidade": col_finalidade,
                "valor": col_valor,
                "area_construida": col_area_construida,
                "area_privativa": col_area_privativa,
                "area_lote": col_area_lote,
                "testada": col_testada,
                "lat": col_lat,
                "lon": col_lon,
                "duplicate_date": duplicate_date_column,
            },
        }
        st.session_state.pop("backtest_run", None)
    except Exception as exc:
        st.error(str(exc))

run = st.session_state.get("valuation_run")
if run is None:
    st.markdown(
        """
        <div class="inline-note">
            A estimativa será apresentada aqui após o cálculo. O K crescerá
            automaticamente até atingir o número efetivo de vizinhos definido
            na barra lateral ou até chegar ao limite máximo.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

preparation: PreparationResult = run["preparation"]
estimate: EstimateResult = run["estimate"]
settings = run["settings"]
run_columns = run["columns"]

st.markdown(
    """
    <div class="section-title">
        <h2>Resultado consolidado</h2>
        <p>Valor central, regularização aplicada e leitura da confiabilidade.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

r1, r2, r3, r4 = st.columns(4)
r1.metric("Valor total estimado", money_br(estimate.estimated_total_value))
r2.metric(
    "Valor unitário robusto",
    f"{money_br(estimate.estimated_unit_value)}/m²",
)
r3.metric(
    "K adaptativo utilizado",
    str(estimate.diagnostics["k_used"]),
    delta=(
        f"{estimate.effective_neighbors:.1f} vizinhos efetivos"
    ),
    delta_color="off",
)
r4.metric(
    "Maior peso individual",
    percent_br(estimate.diagnostics["max_weight_observed"]),
    delta=f"teto: {percent_br(settings['max_weight'])}",
    delta_color="off",
)

tabs = st.tabs(
    [
        "Resumo executivo",
        "Comparáveis",
        "Diagnóstico",
        "Backtesting",
    ]
)

with tabs[0]:
    left, right = st.columns([1.45, 1])
    with left:
        with st.container(border=True):
            st.markdown("#### Leitura do resultado")
            dispersion = (
                estimate.weighted_std_unit / estimate.estimated_unit_value
                if estimate.estimated_unit_value > 0
                else np.nan
            )
            st.write(
                f"A estimativa utilizou **{estimate.diagnostics['k_used']}** "
                f"comparáveis, equivalentes a **{estimate.effective_neighbors:.2f}** "
                "vizinhos efetivos após limitar a influência individual."
            )
            st.write(
                f"A dispersão robusta foi de **{money_br(estimate.weighted_std_unit)}/m²** "
                f"({percent_br(dispersion)} do valor estimado)."
            )
            adjusted_count = estimate.diagnostics["robust_adjusted_count"]
            adjusted_weight = estimate.diagnostics["robust_adjusted_weight"]
            st.write(
                f"O tratamento por MAD ajustou **{adjusted_count}** valor(es), "
                f"correspondentes a **{percent_br(adjusted_weight)}** do peso total."
            )
            st.progress(estimate.diagnostics["confidence_score"] / 100)
            st.caption(
                "A pontuação sintetiza aderência em área, distância, número "
                "efetivo de vizinhos e intensidade do tratamento robusto."
            )
    with right:
        risk_card(
            estimate.diagnostics["risk_level"],
            estimate.diagnostics["confidence_score"],
            estimate.diagnostics["risk_reasons"],
        )

    st.markdown("#### Distribuição dos comparáveis")
    chart_df = estimate.neighbors[
        ["_valor_unitario_ajustado", "_valor_unitario_robusto"]
    ].copy()
    chart_df.index = [
        f"Vizinho {i + 1}" for i in range(len(chart_df))
    ]
    chart_df.columns = ["Valor ajustado", "Valor após tratamento robusto"]
    st.bar_chart(chart_df)

    dedup_removed = preparation.diagnostics.get("offer_duplicates_removed", 0)
    if preparation.diagnostics.get("offer_deduplication_enabled"):
        st.info(
            f"Foram removidos {dedup_removed} registros repetidos de ofertas "
            "antes do cálculo do desconto e da seleção dos comparáveis."
        )
    if preparation.diagnostics.get("discount_warning"):
        st.warning(preparation.diagnostics["discount_warning"])

with tabs[1]:
    neighbors = estimate.neighbors.copy()
    display_columns = [
        "_row_excel",
        run_columns["tipo"],
        run_columns["finalidade"],
        run_columns["valor"],
        run["reference_area_column"],
    ]
    display_columns += [
        column
        for column in [
            run_columns["duplicate_date"],
            run_columns["area_construida"],
            run_columns["area_privativa"],
            run_columns["area_lote"],
            run_columns["testada"],
            run_columns["lat"],
            run_columns["lon"],
        ]
        if column and column not in display_columns
    ]
    display_columns += [
        "_valor_unitario_original",
        "_valor_unitario_ajustado",
        "_valor_unitario_robusto",
        "_ajuste_robusto",
        "_distancia_caracteristicas",
        "_distancia_geografica_km",
        "_distancia_composta",
        "_peso_knn",
        "_contribuicao_valor_unitario",
    ]
    display_columns = [
        column for column in display_columns if column in neighbors.columns
    ]
    rename = {
        "_row_excel": "linha_excel",
        "_valor_unitario_original": "valor_unitario_original",
        "_valor_unitario_ajustado": "valor_unitario_ajustado",
        "_valor_unitario_robusto": "valor_unitario_robusto",
        "_ajuste_robusto": "ajuste_robusto",
        "_distancia_caracteristicas": "distancia_caracteristicas",
        "_distancia_geografica_km": "distancia_geografica_km",
        "_distancia_composta": "distancia_composta",
        "_peso_knn": "peso_knn",
        "_contribuicao_valor_unitario": "contribuicao_valor_unitario",
    }
    neighbors_display = (
        neighbors[display_columns]
        .rename(columns=rename)
        .sort_values("peso_knn", ascending=False)
    )

    st.dataframe(
        neighbors_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "peso_knn": st.column_config.NumberColumn(format="%.2f%%"),
            "distancia_geografica_km": st.column_config.NumberColumn(
                format="%.3f km"
            ),
            "valor_unitario_original": st.column_config.NumberColumn(
                format="R$ %.2f"
            ),
            "valor_unitario_ajustado": st.column_config.NumberColumn(
                format="R$ %.2f"
            ),
            "valor_unitario_robusto": st.column_config.NumberColumn(
                format="R$ %.2f"
            ),
            "ajuste_robusto": st.column_config.NumberColumn(format="R$ %.2f"),
        },
    )

    map_df = neighbors[
        [run_columns["lat"], run_columns["lon"]]
    ].rename(
        columns={
            run_columns["lat"]: "latitude",
            run_columns["lon"]: "longitude",
        }
    )
    target_map = pd.DataFrame(
        [
            {
                "latitude": run["target"]["latitude"],
                "longitude": run["target"]["longitude"],
            }
        ]
    )
    st.map(pd.concat([target_map, map_df], ignore_index=True))

with tabs[2]:
    d1, d2, d3 = st.columns(3)
    d1.metric(
        "Vizinhos efetivos",
        number_br(estimate.effective_neighbors, 2),
        delta=f"objetivo: {number_br(settings['min_effective'], 1)}",
        delta_color="off",
    )
    d2.metric(
        "Desconto das ofertas",
        percent_br(preparation.discount),
        delta="mediana de razões pareadas",
        delta_color="off",
    )
    d3.metric(
        "Candidatos válidos",
        str(estimate.diagnostics["n_candidates"]),
        delta=run["purpose"],
        delta_color="off",
    )

    risk_reasons = estimate.diagnostics["risk_reasons"]
    if risk_reasons:
        for reason in risk_reasons:
            st.warning(reason)
    else:
        st.success("Não foram detectados sinais relevantes de extrapolação.")

    st.markdown("#### Cobertura das características")
    coverage_rows = []
    for feature, stats in estimate.diagnostics["feature_coverage"].items():
        coverage_rows.append(
            {
                "caracteristica": friendly_column_name(feature),
                "avaliando": stats["target"],
                "minimo_amostra": stats["candidate_min"],
                "maximo_amostra": stats["candidate_max"],
                "minimo_vizinhos": stats["selected_min"],
                "maximo_vizinhos": stats["selected_max"],
                "diferenca_mais_proxima": stats["nearest_relative_difference"],
                "fora_da_faixa": stats["outside_candidate_range"],
            }
        )
    st.dataframe(
        pd.DataFrame(coverage_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "diferenca_mais_proxima": st.column_config.NumberColumn(
                format="%.2f%%"
            )
        },
    )

    with st.expander("Parâmetros e rastreabilidade"):
        diagnostics_df = pd.DataFrame(
            [
                {"indicador": key, "valor": str(value)}
                for key, value in {
                    **preparation.diagnostics,
                    **estimate.diagnostics,
                }.items()
                if key not in {"feature_coverage", "risk_reasons"}
            ]
        )
        st.dataframe(diagnostics_df, use_container_width=True, hide_index=True)

with tabs[3]:
    st.markdown("#### Validação fora da própria observação")
    st.caption(
        "Cada imóvel testado é removido da base. Quando uma coluna de grupo é "
        "informada, todos os registros do mesmo imóvel também são excluídos."
    )

    bt1, bt2, bt3 = st.columns(3)
    with bt1:
        backtest_scope_label = st.selectbox(
            "Conjunto de avaliação",
            ["Guias ITBI — recomendado", "Todos os dados ajustados"],
        )
        evaluation_scope = (
            "itbi"
            if backtest_scope_label.startswith("Guias")
            else "all"
        )
    with bt2:
        group_candidates = ["— Apenas a própria linha —"] + original_columns
        default_group = first_existing(
            original_columns,
            [
                "siat_inscricao",
                "inscricao",
                "num_inscricao",
                "siat_lote_fiscal",
            ],
        )
        group_column_selected = st.selectbox(
            "Agrupar e excluir o mesmo imóvel",
            group_candidates,
            index=(
                group_candidates.index(default_group)
                if default_group in group_candidates
                else 0
            ),
        )
        group_column = (
            None
            if group_column_selected == "— Apenas a própria linha —"
            else group_column_selected
        )
    with bt3:
        sample_size = st.slider(
            "Observações testadas",
            min_value=30,
            max_value=300,
            value=120,
            step=10,
        )

    run_backtest = st.button(
        "Executar backtesting",
        type="primary",
        use_container_width=True,
    )
    if run_backtest:
        with st.spinner(
            "Executando validação com exclusão do imóvel avaliado..."
        ):
            try:
                result = backtest_knn(
                    preparation=preparation,
                    mapping=run["mapping"],
                    reference_area_column=run["reference_area_column"],
                    territorial=run["territorial"],
                    min_k=settings["min_k"],
                    max_k=settings["max_k"],
                    min_effective_neighbors=settings["min_effective"],
                    similarity_weight=settings["similarity_weight"],
                    distance_power=settings["distance_power"],
                    max_individual_weight=settings["max_weight"],
                    robust_mad_threshold=settings["robust_threshold"],
                    sample_size=sample_size,
                    group_column=group_column,
                    evaluation_scope=evaluation_scope,
                    random_state=42,
                )
                st.session_state["backtest_run"] = result
            except Exception as exc:
                st.error(str(exc))

    backtest_result: BacktestResult | None = st.session_state.get("backtest_run")
    if backtest_result is not None:
        metrics = backtest_result.metrics
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Mediana do erro absoluto", money_br(metrics["medae_unit"]) + "/m²")
        b2.metric("MdAPE", percent_br(metrics["mdape"]))
        b3.metric("R²", number_br(metrics["r2"], 3))
        b4.metric("P90 do erro percentual", percent_br(metrics["p90_ape"]))

        b5, b6, b7, b8 = st.columns(4)
        b5.metric("MAE", money_br(metrics["mae_unit"]) + "/m²")
        b6.metric("RMSE", money_br(metrics["rmse_unit"]) + "/m²")
        b7.metric("COD", number_br(metrics["cod"], 2) + "%")
        b8.metric("PRD", number_br(metrics["prd"], 3))

        scatter = backtest_result.predictions[
            ["valor_unitario_real", "valor_unitario_estimado"]
        ].rename(
            columns={
                "valor_unitario_real": "Valor real",
                "valor_unitario_estimado": "Valor estimado",
            }
        )
        st.scatter_chart(
            scatter,
            x="Valor real",
            y="Valor estimado",
        )

        error_distribution = (
            backtest_result.predictions["erro_percentual_absoluto"]
            .mul(100)
            .sort_values()
            .reset_index(drop=True)
            .to_frame("Erro percentual absoluto (%)")
        )
        st.line_chart(error_distribution)

        st.dataframe(
            backtest_result.predictions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "erro_percentual": st.column_config.NumberColumn(format="%.2f%%"),
                "erro_percentual_absoluto": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
                "peso_maximo": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )
    else:
        st.markdown(
            """
            <div class="inline-note">
                O backtesting é executado sob demanda porque repete a estimativa
                para cada observação escolhida. Use Guias ITBI como conjunto de
                avaliação para medir a capacidade de aproximar transações.
            </div>
            """,
            unsafe_allow_html=True,
        )

backtest_result = st.session_state.get("backtest_run")
diagnostics_export = {
    "valor_total_estimado": estimate.estimated_total_value,
    "valor_unitario_estimado": estimate.estimated_unit_value,
    "finalidade": run["purpose"],
    "area_referencia": run["reference_area_column"],
    **preparation.diagnostics,
    **estimate.diagnostics,
}
export_neighbors = estimate.neighbors.copy()
excel_bytes = dataframe_to_excel(
    export_neighbors,
    diagnostics_export,
    backtest_result,
)
st.download_button(
    "Baixar resultado completo em Excel",
    data=excel_bytes,
    file_name="avaliacao_knn_v6.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)

with st.expander("Metodologia da versão 6"):
    st.markdown(
        """
1. Filtra a finalidade e exclui ofertas de aluguel.
2. Deduplica ofertas, preservando somente a coleta mais recente.
3. Ajusta as ofertas pela mediana das razões em quantis pareados com ITBI,
   limitada a 20%.
4. Nos imóveis territoriais, normaliza área do lote e TESTADA por
   estatísticas robustas; ambas participam da distância física.
5. Inicia no K escolhido e aumenta o conjunto até alcançar o número efetivo
   de vizinhos ou o K máximo.
6. Limita o peso individual e redistribui o excedente.
7. Winsoriza valores unitários extremos por mediana e MAD antes da média
   ponderada.
8. Classifica extrapolação por cobertura de área, localização, concentração
   de pesos e intensidade do tratamento robusto.
9. No backtesting, exclui a própria observação e, quando configurado, todos os
   registros do mesmo imóvel.
        """
    )
