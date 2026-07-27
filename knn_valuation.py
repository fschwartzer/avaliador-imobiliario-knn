from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


TIPO_ITBI = "guia itbi"
TIPO_OFERTA = "oferta"
TIPO_ALUGUEL = "oferta aluguel"


@dataclass(frozen=True)
class ColumnMapping:
    tipo_informacao: str
    finalidade_oferta: str
    valor: str
    area_construida: str | None
    area_privativa: str | None
    latitude: str
    longitude: str
    siat_area_total_lote: str | None


@dataclass(frozen=True)
class PreparationResult:
    data: pd.DataFrame
    discount: float
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class EstimateResult:
    estimated_unit_value: float
    estimated_total_value: float
    weighted_std_unit: float
    effective_neighbors: float
    neighbors: pd.DataFrame
    active_features: list[str]
    geographic_scale_km: float
    diagnostics: dict[str, Any]


def normalize_text(value: Any) -> str:
    """Normaliza texto para comparações sem diferenciar caixa e acentos."""
    if pd.isna(value):
        return ""
    text = str(value).strip().casefold()
    replacements = str.maketrans(
        "áàãâäéèêëíìîïóòõôöúùûüç",
        "aaaaaeeeeiiiiooooouuuuc",
    )
    return " ".join(text.translate(replacements).split())


def to_numeric(series: pd.Series) -> pd.Series:
    """
    Converte números armazenados como número ou texto.
    Aceita formatos como 1234.56, 1.234,56 e R$ 1.234,56.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace(r"[Rr]\$", "", regex=True)
        .str.replace(r"\s+", "", regex=True)
    )

    has_comma = cleaned.str.contains(",", regex=False, na=False)
    has_dot = cleaned.str.contains(".", regex=False, na=False)
    both = has_comma & has_dot

    # 1.234,56 -> 1234.56
    cleaned.loc[both] = (
        cleaned.loc[both]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    # 1234,56 -> 1234.56
    cleaned.loc[has_comma & ~has_dot] = cleaned.loc[has_comma & ~has_dot].str.replace(
        ",", ".", regex=False
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _positive_values(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    return arr[np.isfinite(arr) & (arr > 0)]


def estimate_offer_discount(
    itbi_unit_values: Iterable[float],
    offer_unit_values: Iterable[float],
    cap: float = 0.20,
) -> tuple[float, dict[str, Any]]:
    """
    Estima o desconto por quantis pareados.

    Como as linhas de ITBI e oferta normalmente não identificam o mesmo imóvel,
    comparar linhas aleatórias criaria uma razão sem significado. A solução
    compara quantis equivalentes das duas distribuições e calcula a média de:

        1 - valor_unitário_ITBI / valor_unitário_OFERTA

    O resultado é limitado ao intervalo [0, cap].
    """
    itbi = _positive_values(itbi_unit_values)
    offers = _positive_values(offer_unit_values)

    diagnostics: dict[str, Any] = {
        "n_itbi_discount": int(itbi.size),
        "n_offer_discount": int(offers.size),
        "discount_method": "média de descontos em quantis pareados",
        "discount_cap": float(cap),
    }

    if itbi.size < 2 or offers.size < 2:
        diagnostics["discount_warning"] = (
            "Desconto igual a zero: são necessários ao menos dois dados de "
            "Guia ITBI e dois de Oferta na finalidade selecionada."
        )
        return 0.0, diagnostics

    n_quantiles = int(np.clip(min(itbi.size, offers.size), 5, 19))
    quantiles = np.linspace(0.10, 0.90, n_quantiles)

    q_itbi = np.quantile(itbi, quantiles)
    q_offer = np.quantile(offers, quantiles)

    valid = np.isfinite(q_itbi) & np.isfinite(q_offer) & (q_offer > 0)
    raw_discounts = 1.0 - (q_itbi[valid] / q_offer[valid])
    raw_discounts = raw_discounts[np.isfinite(raw_discounts)]

    if raw_discounts.size == 0:
        diagnostics["discount_warning"] = "Não foi possível calcular o desconto."
        return 0.0, diagnostics

    # Calcula primeiro a média solicitada e limita apenas o desconto final.
    discount = float(np.clip(np.mean(raw_discounts), 0.0, cap))

    diagnostics.update(
        {
            "raw_discount_mean": float(np.mean(raw_discounts)),
            "raw_discount_median": float(np.median(raw_discounts)),
            "quantiles_used": int(raw_discounts.size),
        }
    )
    return discount, diagnostics



def _parse_registration_dates(series: pd.Series) -> pd.Series:
    """
    Converte datas textuais ou seriais do Excel.

    A prioridade é o padrão brasileiro dia/mês/ano. Valores numéricos
    plausíveis são interpretados como datas seriais do Excel.
    """
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)

    numeric = pd.to_numeric(series, errors="coerce")
    serial_mask = parsed.isna() & numeric.between(1, 100000)
    if serial_mask.any():
        parsed.loc[serial_mask] = pd.to_datetime(
            numeric.loc[serial_mask],
            unit="D",
            origin="1899-12-30",
            errors="coerce",
        )
    return parsed


def deduplicate_offers(
    data: pd.DataFrame,
    date_column: str | None,
    identifier_columns: Iterable[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Remove repetições da mesma oferta, mantendo a observação mais recente.

    A chave é formada pelo primeiro identificador não vazio disponível, na
    ordem informada. Exemplos adequados: URL do anúncio, código do anúncio e
    origem do registro. Guias ITBI não são deduplicadas por esta função.
    """
    diagnostics: dict[str, Any] = {
        "offer_deduplication_enabled": True,
        "offer_duplicates_removed": 0,
        "offer_duplicate_groups": 0,
        "offer_rows_without_identifier": 0,
        "offer_rows_without_valid_date": 0,
        "offer_deduplication_date_column": date_column or "",
        "offer_deduplication_identifier_columns": "",
    }

    usable_identifier_columns = [
        column
        for column in identifier_columns
        if column and column in data.columns
    ]
    diagnostics["offer_deduplication_identifier_columns"] = ", ".join(
        usable_identifier_columns
    )

    if not usable_identifier_columns:
        diagnostics["deduplication_warning"] = (
            "A deduplicação não foi aplicada porque nenhuma coluna "
            "identificadora do anúncio foi encontrada."
        )
        return data, diagnostics

    offer_mask = data["_tipo_norm"].eq(TIPO_OFERTA)
    offers = data.loc[offer_mask].copy()
    if offers.empty:
        return data, diagnostics

    duplicate_key = pd.Series("", index=offers.index, dtype="string")
    source_column = pd.Series("", index=offers.index, dtype="string")

    ignored_identifiers = {"", "transacao", "transação", "nan", "none", "<na>"}
    for column in usable_identifier_columns:
        normalized = offers[column].map(normalize_text).astype("string")
        valid = ~normalized.isin(ignored_identifiers)
        fill_mask = duplicate_key.eq("") & valid
        duplicate_key.loc[fill_mask] = (
            normalize_text(column) + "::" + normalized.loc[fill_mask]
        )
        source_column.loc[fill_mask] = column

    offers["_chave_oferta_deduplicacao"] = duplicate_key
    offers["_fonte_chave_oferta"] = source_column

    without_identifier = duplicate_key.eq("")
    diagnostics["offer_rows_without_identifier"] = int(without_identifier.sum())

    candidates = offers.loc[~without_identifier].copy()
    if candidates.empty:
        diagnostics["deduplication_warning"] = (
            "A deduplicação não foi aplicada porque os identificadores das "
            "ofertas estão vazios."
        )
        return data, diagnostics

    if date_column and date_column in candidates.columns:
        candidates["_data_registro_deduplicacao"] = _parse_registration_dates(
            candidates[date_column]
        )
    else:
        candidates["_data_registro_deduplicacao"] = pd.NaT
        diagnostics["deduplication_warning"] = (
            "A coluna de data não foi encontrada. Em empates, foi mantida a "
            "última linha existente no arquivo."
        )

    diagnostics["offer_rows_without_valid_date"] = int(
        candidates["_data_registro_deduplicacao"].isna().sum()
    )

    # NaT fica antes das datas válidas; keep='last' preserva a data mais recente.
    # A linha do Excel é o critério final de desempate para ocorrências na mesma data.
    candidates = candidates.sort_values(
        [
            "_chave_oferta_deduplicacao",
            "_data_registro_deduplicacao",
            "_row_excel",
        ],
        ascending=[True, True, True],
        na_position="first",
        kind="mergesort",
    )

    group_sizes = candidates.groupby(
        "_chave_oferta_deduplicacao",
        dropna=False,
    ).size()
    diagnostics["offer_duplicate_groups"] = int((group_sizes > 1).sum())

    duplicated = candidates.duplicated(
        subset=["_chave_oferta_deduplicacao"],
        keep="last",
    )
    indices_to_remove = candidates.index[duplicated]
    diagnostics["offer_duplicates_removed"] = int(len(indices_to_remove))

    cleaned = data.drop(index=indices_to_remove).copy()

    # Preserva metadados nas ofertas mantidas para auditoria e exportação.
    kept_metadata = candidates.loc[
        ~duplicated,
        [
            "_chave_oferta_deduplicacao",
            "_fonte_chave_oferta",
            "_data_registro_deduplicacao",
        ],
    ]
    for column in kept_metadata.columns:
        cleaned.loc[kept_metadata.index, column] = kept_metadata[column]

    return cleaned, diagnostics

def validate_mapping(df: pd.DataFrame, mapping: ColumnMapping) -> None:
    required = [
        mapping.tipo_informacao,
        mapping.finalidade_oferta,
        mapping.valor,
        mapping.latitude,
        mapping.longitude,
    ]
    optional = [
        mapping.area_construida,
        mapping.area_privativa,
        mapping.siat_area_total_lote,
    ]
    missing = [column for column in required if column not in df.columns]
    missing += [
        column for column in optional if column is not None and column not in df.columns
    ]
    if missing:
        raise ValueError(
            "As seguintes colunas mapeadas não existem no arquivo: "
            + ", ".join(sorted(set(missing)))
        )


def prepare_data(
    df: pd.DataFrame,
    mapping: ColumnMapping,
    selected_purpose: str,
    value_kind: str,
    reference_area_column: str,
    discount_cap: float = 0.20,
    remove_offer_duplicates: bool = True,
    duplicate_date_column: str | None = None,
    duplicate_identifier_columns: Iterable[str] = (),
) -> PreparationResult:
    validate_mapping(df, mapping)

    if reference_area_column not in df.columns:
        raise ValueError("A coluna de área de referência não existe no arquivo.")

    data = df.copy()
    data["_row_excel"] = np.arange(2, len(data) + 2)
    data["_tipo_norm"] = data[mapping.tipo_informacao].map(normalize_text)
    data["_finalidade_norm"] = data[mapping.finalidade_oferta].map(normalize_text)

    purpose_norm = normalize_text(selected_purpose)
    data = data.loc[data["_finalidade_norm"] == purpose_norm].copy()

    # Desconsidera aluguel e quaisquer categorias não previstas.
    data = data.loc[data["_tipo_norm"].isin([TIPO_ITBI, TIPO_OFERTA])].copy()

    deduplication_diagnostics: dict[str, Any] = {
        "offer_deduplication_enabled": bool(remove_offer_duplicates),
        "offer_duplicates_removed": 0,
        "offer_duplicate_groups": 0,
        "offer_rows_without_identifier": 0,
        "offer_rows_without_valid_date": 0,
    }
    if remove_offer_duplicates:
        data, deduplication_diagnostics = deduplicate_offers(
            data=data,
            date_column=duplicate_date_column,
            identifier_columns=duplicate_identifier_columns,
        )

    numeric_columns = {
        mapping.valor,
        mapping.latitude,
        mapping.longitude,
        reference_area_column,
    }
    for column in [
        mapping.area_construida,
        mapping.area_privativa,
        mapping.siat_area_total_lote,
    ]:
        if column:
            numeric_columns.add(column)

    for column in numeric_columns:
        data[column] = to_numeric(data[column])

    value_kind_norm = normalize_text(value_kind)
    if value_kind_norm == "valor total":
        area_ref = data[reference_area_column]
        data["_valor_unitario_original"] = data[mapping.valor] / area_ref
    elif value_kind_norm in {"valor unitario", "valor unitario por m2", "valor unitario por m²"}:
        data["_valor_unitario_original"] = data[mapping.valor]
    else:
        raise ValueError("Natureza do valor inválida.")

    valid_value = (
        np.isfinite(data["_valor_unitario_original"])
        & (data["_valor_unitario_original"] > 0)
    )
    data = data.loc[valid_value].copy()

    itbi_values = data.loc[
        data["_tipo_norm"] == TIPO_ITBI, "_valor_unitario_original"
    ]
    offer_values = data.loc[
        data["_tipo_norm"] == TIPO_OFERTA, "_valor_unitario_original"
    ]

    discount, discount_diagnostics = estimate_offer_discount(
        itbi_values, offer_values, cap=discount_cap
    )

    data["_fator_ajuste"] = np.where(
        data["_tipo_norm"].eq(TIPO_OFERTA),
        1.0 - discount,
        1.0,
    )
    data["_valor_unitario_ajustado"] = (
        data["_valor_unitario_original"] * data["_fator_ajuste"]
    )

    diagnostics = {
        **discount_diagnostics,
        **deduplication_diagnostics,
        "purpose": selected_purpose,
        "n_filtered": int(len(data)),
        "n_itbi": int(data["_tipo_norm"].eq(TIPO_ITBI).sum()),
        "n_offer": int(data["_tipo_norm"].eq(TIPO_OFERTA).sum()),
        "reference_area_column": reference_area_column,
        "value_kind": value_kind,
    }

    return PreparationResult(data=data, discount=discount, diagnostics=diagnostics)


def _robust_center_scale(values: np.ndarray) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 0.0, 1.0

    center = float(np.median(values))
    q25, q75 = np.quantile(values, [0.25, 0.75])
    scale = float(q75 - q25)

    if not np.isfinite(scale) or scale <= 1e-12:
        mad = float(np.median(np.abs(values - center)))
        scale = 1.4826 * mad

    if not np.isfinite(scale) or scale <= 1e-12:
        std = float(np.std(values))
        scale = std

    if not np.isfinite(scale) or scale <= 1e-12:
        scale = max(abs(center), 1.0)

    return center, scale


def _local_xy_km(
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    target_lat: float,
    target_lon: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Projeção local simples em quilômetros, adequada à vizinhança urbana."""
    earth_radius_km = 6371.0088
    lat0_rad = np.radians(target_lat)
    x = earth_radius_km * np.cos(lat0_rad) * np.radians(longitudes - target_lon)
    y = earth_radius_km * np.radians(latitudes - target_lat)
    return x, y


def estimate_knn(
    preparation: PreparationResult,
    mapping: ColumnMapping,
    target: dict[str, float | None],
    reference_area_column: str,
    k: int = 7,
    similarity_weight: float = 0.75,
    distance_power: float = 2.0,
    territorial: bool = False,
) -> EstimateResult:
    if not 0.0 < similarity_weight < 1.0:
        raise ValueError("O peso de similaridade deve estar entre 0 e 1.")
    if k < 1:
        raise ValueError("k deve ser ao menos 1.")
    if distance_power <= 0:
        raise ValueError("A potência da distância deve ser positiva.")

    data = preparation.data.copy()

    lat_target = float(target["latitude"])
    lon_target = float(target["longitude"])
    if not np.isfinite(lat_target) or not np.isfinite(lon_target):
        raise ValueError("Latitude e longitude do avaliando são obrigatórias.")

    feature_pairs = [
        ("area_construida", mapping.area_construida),
        ("area_privativa", mapping.area_privativa),
    ]

    lot_target = target.get("siat_area_total_lote")
    lot_target_valid = (
        lot_target is not None
        and np.isfinite(float(lot_target))
        and float(lot_target) > 0
    )
    built_target_valid = any(
        target.get(key) is not None
        and np.isfinite(float(target[key]))
        and float(target[key]) > 0
        for key in ("area_construida", "area_privativa")
    )

    # Segurança adicional: quando só há área de lote informada, o núcleo
    # reconhece o avaliando como territorial mesmo que a interface não tenha
    # marcado explicitamente essa condição.
    effective_territorial = territorial or (lot_target_valid and not built_target_valid)
    if effective_territorial:
        feature_pairs.append(("siat_area_total_lote", mapping.siat_area_total_lote))

    active_features: list[tuple[str, str]] = []
    for target_key, data_column in feature_pairs:
        target_value = target.get(target_key)
        if (
            data_column
            and target_value is not None
            and np.isfinite(float(target_value))
            and float(target_value) > 0
        ):
            active_features.append((target_key, data_column))

    if effective_territorial:
        lot_active = any(key == "siat_area_total_lote" for key, _ in active_features)
        if not lot_active:
            raise ValueError(
                "Para imóvel territorial, informe e mapeie 'siat_area_total_lote'."
            )

    if not active_features:
        raise ValueError(
            "Informe ao menos uma característica de área válida para o avaliando."
        )

    required_cols = [
        mapping.latitude,
        mapping.longitude,
        "_valor_unitario_ajustado",
    ] + [column for _, column in active_features]

    valid_mask = np.ones(len(data), dtype=bool)
    for column in required_cols:
        values = to_numeric(data[column])
        data[column] = values
        valid_mask &= np.isfinite(values)

    valid_mask &= data["_valor_unitario_ajustado"].gt(0).to_numpy()
    valid_mask &= data[mapping.latitude].between(-90, 90).to_numpy()
    valid_mask &= data[mapping.longitude].between(-180, 180).to_numpy()

    for _, column in active_features:
        valid_mask &= data[column].gt(0).to_numpy()

    data = data.loc[valid_mask].copy()
    if data.empty:
        raise ValueError(
            "Nenhuma linha válida permaneceu após aplicar os filtros e exigir "
            "as características usadas pelo KNN."
        )

    n_neighbors = min(int(k), len(data))
    n_area_features = len(active_features)

    feature_matrix_parts: list[np.ndarray] = []
    target_matrix_parts: list[float] = []
    attr_squared = np.zeros(len(data), dtype=float)

    per_area_weight = similarity_weight / n_area_features

    for target_key, column in active_features:
        values = data[column].to_numpy(dtype=float)
        target_value = float(target[target_key])
        center, scale = _robust_center_scale(values)

        z_values = (values - center) / scale
        z_target = (target_value - center) / scale
        delta = z_values - z_target

        attr_squared += (delta**2) / n_area_features
        feature_matrix_parts.append(z_values * np.sqrt(per_area_weight))
        target_matrix_parts.append(z_target * np.sqrt(per_area_weight))

    latitudes = data[mapping.latitude].to_numpy(dtype=float)
    longitudes = data[mapping.longitude].to_numpy(dtype=float)
    x_km, y_km = _local_xy_km(
        latitudes, longitudes, lat_target, lon_target
    )
    radial_km = np.sqrt(x_km**2 + y_km**2)

    positive_radial = radial_km[np.isfinite(radial_km) & (radial_km > 0)]
    if positive_radial.size:
        geographic_scale_km = float(np.median(positive_radial))
    else:
        geographic_scale_km = 1.0
    geographic_scale_km = max(geographic_scale_km, 0.25)

    location_weight = 1.0 - similarity_weight
    feature_matrix_parts.extend(
        [
            (x_km / geographic_scale_km) * np.sqrt(location_weight),
            (y_km / geographic_scale_km) * np.sqrt(location_weight),
        ]
    )
    target_matrix_parts.extend([0.0, 0.0])

    feature_matrix = np.column_stack(feature_matrix_parts)
    target_matrix = np.asarray(target_matrix_parts, dtype=float).reshape(1, -1)

    model = NearestNeighbors(n_neighbors=n_neighbors, metric="euclidean")
    model.fit(feature_matrix)
    distances, indices = model.kneighbors(target_matrix)

    idx = indices[0]
    composite_distance = distances[0]
    neighbors = data.iloc[idx].copy()

    epsilon = 1e-9
    raw_weights = 1.0 / np.power(composite_distance + epsilon, distance_power)
    normalized_weights = raw_weights / raw_weights.sum()

    unit_values = neighbors["_valor_unitario_ajustado"].to_numpy(dtype=float)
    estimated_unit = float(np.sum(normalized_weights * unit_values))

    reference_target_value = target.get(reference_area_column)
    if reference_target_value is None or not np.isfinite(float(reference_target_value)):
        # A chave do alvo usa nomes canônicos; tenta resolver pela coluna mapeada.
        mapping_to_target_key = {
            mapping.area_construida: "area_construida",
            mapping.area_privativa: "area_privativa",
            mapping.siat_area_total_lote: "siat_area_total_lote",
        }
        target_key = mapping_to_target_key.get(reference_area_column)
        reference_target_value = target.get(target_key) if target_key else None

    if (
        reference_target_value is None
        or not np.isfinite(float(reference_target_value))
        or float(reference_target_value) <= 0
    ):
        raise ValueError(
            "Informe a área do avaliando correspondente à área de referência do valor."
        )

    estimated_total = estimated_unit * float(reference_target_value)

    weighted_variance = float(
        np.sum(normalized_weights * np.square(unit_values - estimated_unit))
    )
    weighted_std = float(np.sqrt(max(weighted_variance, 0.0)))
    effective_neighbors = float(1.0 / np.sum(normalized_weights**2))

    neighbor_attr_distance = np.sqrt(attr_squared[idx])
    neighbor_geo_distance = radial_km[idx]

    neighbors["_distancia_caracteristicas"] = neighbor_attr_distance
    neighbors["_distancia_geografica_km"] = neighbor_geo_distance
    neighbors["_distancia_composta"] = composite_distance
    neighbors["_peso_knn"] = normalized_weights
    neighbors["_contribuicao_valor_unitario"] = normalized_weights * unit_values

    feature_coverage: dict[str, dict[str, float]] = {}
    for target_key, column in active_features:
        target_value = float(target[target_key])
        candidate_values = data[column].to_numpy(dtype=float)
        selected_values = neighbors[column].to_numpy(dtype=float)
        relative_differences = np.abs(candidate_values - target_value) / target_value
        feature_coverage[column] = {
            "target": target_value,
            "candidate_min": float(np.min(candidate_values)),
            "candidate_max": float(np.max(candidate_values)),
            "selected_min": float(np.min(selected_values)),
            "selected_max": float(np.max(selected_values)),
            "nearest_relative_difference": float(np.min(relative_differences)),
        }

    diagnostics = {
        "k_requested": int(k),
        "k_used": int(n_neighbors),
        "similarity_weight": float(similarity_weight),
        "location_weight": float(location_weight),
        "distance_power": float(distance_power),
        "n_candidates": int(len(data)),
        "reference_target_area": float(reference_target_value),
        "effective_territorial": bool(effective_territorial),
        "feature_coverage": feature_coverage,
    }

    return EstimateResult(
        estimated_unit_value=estimated_unit,
        estimated_total_value=estimated_total,
        weighted_std_unit=weighted_std,
        effective_neighbors=effective_neighbors,
        neighbors=neighbors,
        active_features=[column for _, column in active_features],
        geographic_scale_km=geographic_scale_km,
        diagnostics=diagnostics,
    )
