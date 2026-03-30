"""Pure-Python matching engine.

Design goals:
- No DB writes or side effects.
- Works with existing SQLAlchemy model instances (Donor/Recipient) or mock objects.
- Deterministic, modular scoring suitable for unit testing.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_WEIGHTS = {
    "urgency": 0.35,
    "organ_compatibility": 0.45,
    "ml": 0.20,
}

URGENCY_SCORES = {
    "urgent": 1.0,
    "high": 0.7,
    "standard": 0.4,
    "low": 0.25,
}


# Recipient blood type -> compatible donor blood types.
BLOOD_COMPATIBILITY = {
    "O-": {"O-"},
    "O+": {"O-", "O+"},
    "A-": {"O-", "A-"},
    "A+": {"O-", "O+", "A-", "A+"},
    "B-": {"O-", "B-"},
    "B+": {"O-", "O+", "B-", "B+"},
    "AB-": {"O-", "A-", "B-", "AB-"},
    "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
}


@dataclass(frozen=True)
class MatchBreakdown:
    urgency_score: float
    organ_score: float
    blood_compatibility_score: float
    ml_score: Optional[float]
    survival_score: Optional[float]
    weighted_urgency: float
    weighted_organ: float
    weighted_ml: float
    weighted_survival: float


@dataclass(frozen=True)
class MatchResult:
    recipient_id: str
    score: float
    explanation: dict[str, Any]


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        # Accept comma-separated input for convenience in tests/mocks.
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            text = _safe_text(item)
            if text:
                out.append(text)
        return out
    return []


def _normalized_weights(
    base: Mapping[str, float],
    include_ml: bool,
    include_survival: bool,
) -> dict[str, float]:
    weights = {
        "urgency": float(base.get("urgency", 0.0)),
        "organ_compatibility": float(base.get("organ_compatibility", 0.0)),
        "ml": float(base.get("ml", 0.0) if include_ml else 0.0),
        "survival": float(base.get("survival", base.get("ml", 0.0)) if include_survival else 0.0),
    }
    total = weights["urgency"] + weights["organ_compatibility"] + weights["ml"] + weights["survival"]
    if total <= 0:
        # Fall back to equal split among active components.
        active = ["urgency", "organ_compatibility"]
        if include_ml:
            active.append("ml")
        if include_survival:
            active.append("survival")
        eq = 1.0 / max(1, len(active))
        weights = {"urgency": 0.0, "organ_compatibility": 0.0, "ml": 0.0, "survival": 0.0}
        for key in active:
            weights[key] = eq
        return weights

    return {k: v / total for k, v in weights.items()}


def _http_get_json(url: str, timeout: float = 1.5) -> Optional[dict[str, Any]]:
    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=timeout) as response:  # nosec B310 - controlled internal URL usage
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        return data if isinstance(data, dict) else None
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None


def _survival_mock_score(recipient: Any, donor: Any) -> dict[str, Any]:
    urgency = _urgency_score(recipient)
    organ_score = _organ_compatibility_score(donor, recipient)
    blood_score = _blood_compatibility_score(donor, recipient)

    # Heuristic proxy in [0,1], favors compatibility and penalizes extreme urgency.
    score = _clamp_01((0.55 * blood_score) + (0.35 * organ_score) + (0.20 * (1.0 - urgency)))
    return {
        "score": score,
        "source": "mock",
        "details": {
            "blood_component": blood_score,
            "organ_component": organ_score,
            "urgency_penalty_component": 1.0 - urgency,
        },
    }


def get_survival_score(
    recipient: Any,
    donor: Any,
    *,
    ml_base_url: Optional[str] = None,
    timeout: float = 1.5,
    fetcher: Optional[Any] = None,
    use_mock_if_unavailable: bool = True,
) -> dict[str, Any]:
    """Get survival score with graceful fallback.

    Resolution order:
    1) custom fetcher(recipient, donor)
    2) existing ML endpoints (/ml/metrics and /ml/predict)
    3) pure-python mock heuristic (optional)

    Returns:
        {
          "score": float | None,
          "source": "custom_fetcher" | "ml_endpoint" | "mock" | "unavailable",
          "details": dict
        }
    """
    if callable(fetcher):
        try:
            value = fetcher(recipient, donor)
            if value is not None:
                return {
                    "score": _clamp_01(float(value)),
                    "source": "custom_fetcher",
                    "details": {},
                }
        except Exception:
            # Fall through to endpoint/mock behavior.
            pass

    base_url = ml_base_url or os.getenv("ML_BASE_URL") or "http://127.0.0.1:8000"
    metrics = _http_get_json(f"{base_url.rstrip('/')}/ml/metrics", timeout=timeout)
    predict = _http_get_json(f"{base_url.rstrip('/')}/ml/predict", timeout=timeout)

    if metrics is not None:
        model_acc = _clamp_01(float(metrics.get("accuracy", 0.6)))
        blood_score = _blood_compatibility_score(donor, recipient)
        organ_score = _organ_compatibility_score(donor, recipient)

        # Optional regional adjustment if forecast payload is reachable.
        region_adj = 0.0
        if predict and isinstance(predict.get("forecast"), list):
            donor_loc = _safe_text(getattr(donor, "location", "")).lower()
            for row in predict["forecast"]:
                region = _safe_text(row.get("region", "")).lower()
                if donor_loc and region and donor_loc in region:
                    region_adj = float(row.get("willingness_rate", 0.0)) * 0.1
                    break

        endpoint_score = _clamp_01((0.45 * blood_score) + (0.35 * organ_score) + (0.20 * model_acc) + region_adj)
        return {
            "score": endpoint_score,
            "source": "ml_endpoint",
            "details": {
                "model_accuracy": model_acc,
                "blood_component": blood_score,
                "organ_component": organ_score,
                "region_adjustment": region_adj,
            },
        }

    if use_mock_if_unavailable:
        return _survival_mock_score(recipient, donor)

    return {"score": None, "source": "unavailable", "details": {}}


def _urgency_score(recipient: Any) -> float:
    urgency = _safe_text(getattr(recipient, "urgency", "")).lower()
    return URGENCY_SCORES.get(urgency, URGENCY_SCORES["standard"])


def _blood_compatibility_score(donor: Any, recipient: Any) -> float:
    donor_bg = _safe_text(getattr(donor, "blood_group", ""))
    recipient_bg = _safe_text(getattr(recipient, "blood_group", ""))

    if not donor_bg or not recipient_bg:
        # Unknown blood group -> partial uncertainty score.
        return 0.5

    compatible = donor_bg in BLOOD_COMPATIBILITY.get(recipient_bg, set())
    return 1.0 if compatible else 0.0


def _organ_compatibility_score(donor: Any, recipient: Any) -> float:
    donor_organs = set(_as_str_list(getattr(donor, "organs_selected", None)))
    recipient_organs = set(_as_str_list(getattr(recipient, "organ_needed", None)))

    if not donor_organs or not recipient_organs:
        return 0.0

    overlap = donor_organs.intersection(recipient_organs)
    return len(overlap) / max(1, len(recipient_organs))


def _resolve_ml_score(
    recipient: Any,
    ml_scores: Optional[Mapping[str, float]],
    ml_score_getter: Optional[Any],
) -> Optional[float]:
    recipient_id = _safe_text(getattr(recipient, "id", ""))

    value: Optional[float] = None
    if ml_scores is not None and recipient_id in ml_scores:
        value = float(ml_scores[recipient_id])
    elif callable(ml_score_getter):
        value = ml_score_getter(recipient)

    if value is None:
        return None

    return _clamp_01(value)


def compute_match_score(
    donor: Any,
    recipient: Any,
    *,
    weights: Optional[Mapping[str, float]] = None,
    ml_scores: Optional[Mapping[str, float]] = None,
    ml_score_getter: Optional[Any] = None,
    include_survival: bool = False,
    survival_fetcher: Optional[Any] = None,
    ml_base_url: Optional[str] = None,
    timeout: float = 1.5,
    use_mock_if_unavailable: bool = True,
) -> dict[str, Any]:
    """Compute weighted donor->recipient match score.

    Args:
        donor: Existing Donor SQLAlchemy model instance (or duck-typed object).
        recipient: Existing Recipient SQLAlchemy model instance.
        weights: Optional weights mapping with keys:
            `urgency`, `organ_compatibility`, `ml`.
        ml_scores: Optional mapping {recipient_id: score in [0,1]}.
        ml_score_getter: Optional callable(recipient) -> score in [0,1] or None.

    Returns:
        Structured dict with recipient_id, final score, and explanation breakdown.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    urgency = _clamp_01(_urgency_score(recipient))
    organ = _clamp_01(_organ_compatibility_score(donor, recipient))
    blood = _clamp_01(_blood_compatibility_score(donor, recipient))
    # Blood compatibility gates organ score (hard mismatch heavily penalizes).
    organ_with_blood = organ * (0.2 + 0.8 * blood)

    ml_score = _resolve_ml_score(recipient, ml_scores, ml_score_getter)

    survival_info: dict[str, Any] = {"score": None, "source": "unavailable", "details": {}}
    if include_survival:
        survival_info = get_survival_score(
            recipient,
            donor,
            ml_base_url=ml_base_url,
            timeout=timeout,
            fetcher=survival_fetcher,
            use_mock_if_unavailable=use_mock_if_unavailable,
        )
    survival_score = survival_info.get("score")

    norm_w = _normalized_weights(
        weights,
        include_ml=ml_score is not None,
        include_survival=survival_score is not None,
    )

    weighted_urgency = urgency * norm_w["urgency"]
    weighted_organ = organ_with_blood * norm_w["organ_compatibility"]
    weighted_ml = (ml_score or 0.0) * norm_w["ml"]
    weighted_survival = (survival_score or 0.0) * norm_w["survival"]

    final_score = _clamp_01(weighted_urgency + weighted_organ + weighted_ml + weighted_survival)

    recipient_id = _safe_text(getattr(recipient, "id", ""))
    explanation = {
        "components": {
            "urgency_score": urgency,
            "organ_score": organ,
            "blood_compatibility_score": blood,
            "organ_with_blood_score": _clamp_01(organ_with_blood),
            "ml_score": ml_score,
            "survival_score": survival_score,
            "survival_source": survival_info.get("source"),
            "survival_details": survival_info.get("details", {}),
        },
        "weights": norm_w,
        "weighted": {
            "urgency": weighted_urgency,
            "organ_compatibility": weighted_organ,
            "ml": weighted_ml,
            "survival": weighted_survival,
        },
        "final_score": final_score,
    }

    return {
        "recipient_id": recipient_id,
        "score": final_score,
        "explanation": explanation,
    }


def rank_recipients(
    donor: Any,
    recipients: Sequence[Any],
    *,
    top_k: Optional[int] = None,
    weights: Optional[Mapping[str, float]] = None,
    ml_scores: Optional[Mapping[str, float]] = None,
    ml_score_getter: Optional[Any] = None,
    include_survival: bool = False,
    survival_fetcher: Optional[Any] = None,
    ml_base_url: Optional[str] = None,
    timeout: float = 1.5,
    use_mock_if_unavailable: bool = True,
) -> list[dict[str, Any]]:
    """Rank recipients for a donor using compute_match_score.

    Pure function: no DB writes, no side effects.
    """
    ranked = [
        compute_match_score(
            donor,
            recipient,
            weights=weights,
            ml_scores=ml_scores,
            ml_score_getter=ml_score_getter,
            include_survival=include_survival,
            survival_fetcher=survival_fetcher,
            ml_base_url=ml_base_url,
            timeout=timeout,
            use_mock_if_unavailable=use_mock_if_unavailable,
        )
        for recipient in recipients
    ]

    ranked.sort(
        key=lambda row: (
            -float(row["score"]),
            -float(row["explanation"]["components"]["urgency_score"]),
        )
    )

    if top_k is not None and top_k >= 0:
        return ranked[:top_k]
    return ranked


__all__ = [
    "compute_match_score",
    "rank_recipients",
    "get_survival_score",
    "DEFAULT_WEIGHTS",
]
