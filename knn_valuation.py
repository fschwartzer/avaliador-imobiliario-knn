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
    Calcula o desconto médio solicitado pelo usuário:

        1 - média(valor unitário ITBI) / média(valor unitário Oferta)

    O cálculo ocorre depois do filtro por finalidade e usa valores unitários,
    para não confundir diferença de área com diferença entre preço ofertado e
    preço de transação. O desconto final é limitado ao intervalo [0, cap].

    O cálculo é permitido mesmo quando existe apenas uma oferta, mas a baixa
    quantidade é registrada como alerta de fragilidade amostral.
    """
    itbi = _positive_values(itbi_unit_values)
    offers = _positive_values(offer_unit_values)

    diagnostics: dict[str, Any] = {
        "n_itbi_discount": int(itbi.size),
        "n_offer_discount": int(offers.size),
        "discount_method": (
            "1 - média do valor unitário ITBI / média do valor unitário Oferta"
        ),
        "discount_cap": float(cap),
    }

    if itbi.size == 0 or offers.size == 0:
        diagnostics["discount_warning"] = (
            "Desconto igual a zero: a finalidade selecionada não possui, ao "
            "mesmo tempo, dados de Guia ITBI e de Oferta."
        )
        return 0.0, diagnostics

    mean_itbi = float(np.mean(itbi))
    mean_offer = float(np.mean(offers))

    if not np.isfinite(mean_offer) or mean_offer <= 0:
        diagnostics["discount_warning"] = (
            "Desconto igual a zero: a média unitária das ofertas é inválida."
        )
        return 0.0, diagnostics

    raw_discount = float(1.0 - (mean_itbi / mean_offer))
    discount = float(np.clip(raw_discount, 0.0, cap))

    diagnostics.update(
        {
            "mean_itbi_unit_value": mean_itbi,
            "mean_offer_unit_value": mean_offer,
            "raw_discount": raw_discount,
            "discount_was_capped": bool(raw_discount > cap),
        }
    )

    warnings: list[str] = []
    if itbi.size < 3:
        warnings.append(
            f"há apenas {itbi.size} Guia(s) ITBI na finalidade selecionada"
        )
    if offers.size < 3:
        warnings.append(
            f"há apenas {offers.size} Oferta(s) na finalidade selecionada"
        )
    if raw_discount <= 0:
        warnings.append(
            "a média unitária das ofertas não superou a média unitária das "
            "Guias ITBI; por isso não foi aplicado desconto"
        )
    if raw_discount > cap:
        warnings.append(
            f"o desconto bruto foi limitado ao teto de {cap:.0%}"
        )

    if warnings:
        diagnostics["discount_warning"] = (
            "Atenção à estimativa do desconto: " + "; ".join(warnings) + "."
        )

    return discount, diagnostics



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
    if territorial:
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

    if territorial:
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

    diagnostics = {
        "k_requested": int(k),
        "k_used": int(n_neighbors),
        "similarity_weight": float(similarity_weight),
        "location_weight": float(location_weight),
        "distance_power": float(distance_power),
        "n_candidates": int(len(data)),
        "reference_target_area": float(reference_target_value),
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
