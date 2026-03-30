"""Matching service layer.

Non-breaking service that fetches donor/recipient data using existing SQLAlchemy models
and delegates scoring/ranking to ai_models.matching_engine.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any

from fastapi import HTTPException, status
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_models.matching_engine import rank_recipients
from models import Donor, Hospital, Recipient, User, UserRole


class MatchingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _fetch_ml_context(self, ml_base_url: str | None = None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Fetch ML context once (async, non-blocking).

        This avoids per-recipient blocking I/O inside scoring loops.
        """
        base_url = (ml_base_url or os.getenv("ML_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")
        metrics_url = f"{base_url}/ml/metrics"
        predict_url = f"{base_url}/ml/predict"

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                metrics_resp, predict_resp = await asyncio.gather(
                    client.get(metrics_url),
                    client.get(predict_url),
                )
        except Exception:
            return None, None

        metrics = metrics_resp.json() if metrics_resp.status_code == 200 else None
        predict = predict_resp.json() if predict_resp.status_code == 200 else None
        return metrics if isinstance(metrics, dict) else None, predict if isinstance(predict, dict) else None

    @staticmethod
    def _build_survival_fetcher(
        metrics: dict[str, Any] | None,
        predict: dict[str, Any] | None,
    ):
        """Create an in-memory survival scorer for matching_engine.

        Returns a callable(recipient, donor) -> float in [0,1], with no I/O.
        """

        def blood_score(donor: Any, recipient: Any) -> float:
            d = str(getattr(donor, "blood_group", "") or "").strip()
            r = str(getattr(recipient, "blood_group", "") or "").strip()
            if not d or not r:
                return 0.5
            # conservative blood compatibility matrix
            compatibility = {
                "O-": {"O-"},
                "O+": {"O-", "O+"},
                "A-": {"O-", "A-"},
                "A+": {"O-", "O+", "A-", "A+"},
                "B-": {"O-", "B-"},
                "B+": {"O-", "O+", "B-", "B+"},
                "AB-": {"O-", "A-", "B-", "AB-"},
                "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
            }
            return 1.0 if d in compatibility.get(r, set()) else 0.0

        def organ_score(donor: Any, recipient: Any) -> float:
            donor_organs = set(getattr(donor, "organs_selected", None) or [])
            recipient_organs = set(getattr(recipient, "organ_needed", None) or [])
            if not donor_organs or not recipient_organs:
                return 0.0
            return len(donor_organs.intersection(recipient_organs)) / max(1, len(recipient_organs))

        model_acc = 0.6
        if isinstance(metrics, dict):
            try:
                model_acc = max(0.0, min(1.0, float(metrics.get("accuracy", 0.6))))
            except Exception:
                model_acc = 0.6

        forecast = []
        if isinstance(predict, dict) and isinstance(predict.get("forecast"), list):
            forecast = predict.get("forecast")

        def fetcher(recipient: Any, donor: Any) -> float:
            b = blood_score(donor, recipient)
            o = organ_score(donor, recipient)

            region_adj = 0.0
            donor_loc = str(getattr(donor, "location", "") or "").lower()
            for row in forecast:
                region = str(row.get("region", "") or "").lower()
                if donor_loc and region and donor_loc in region:
                    try:
                        region_adj = float(row.get("willingness_rate", 0.0)) * 0.1
                    except Exception:
                        region_adj = 0.0
                    break

            return max(0.0, min(1.0, (0.45 * b) + (0.35 * o) + (0.20 * model_acc) + region_adj))

        return fetcher

    async def _get_donor(self, donor_id: str) -> Donor:
        try:
            donor_uuid = uuid.UUID(donor_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid donor_id")

        result = await self.db.execute(select(Donor).where(Donor.id == donor_uuid))
        donor = result.scalar_one_or_none()
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        return donor

    async def _get_scope_recipients(self, current_user: User) -> list[Recipient]:
        if current_user.role == UserRole.admin:
            result = await self.db.execute(
                select(Recipient).where(Recipient.status.in_(["pending", "approved", "matched"]))
            )
            return result.scalars().all()

        if current_user.role == UserRole.hospital:
            hospital_result = await self.db.execute(
                select(Hospital).where(Hospital.user_id == current_user.id)
            )
            hospital = hospital_result.scalar_one_or_none()
            if not hospital:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Hospital not registered",
                )

            result = await self.db.execute(
                select(Recipient)
                .where(Recipient.hospital_id == hospital.id)
                .where(Recipient.status.in_(["pending", "approved", "matched"]))
            )
            return result.scalars().all()

        raise HTTPException(status_code=403, detail="Hospital or Admin access required")

    async def rank_recipients_for_donor(
        self,
        donor_id: str,
        current_user: User,
        *,
        include_survival: bool = False,
        top_k: int = 20,
        ml_base_url: str | None = None,
    ) -> dict[str, Any]:
        donor = await self._get_donor(donor_id)
        recipients = await self._get_scope_recipients(current_user)

        # Build O(1) lookup map to avoid repeated scans while enriching output.
        recipients_by_id = {str(r.id): r for r in recipients}

        # Cap top_k defensively to avoid oversized responses.
        safe_top_k = min(max(0, top_k), 200)

        survival_fetcher = None
        if include_survival:
            metrics, predict = await self._fetch_ml_context(ml_base_url=ml_base_url)
            survival_fetcher = self._build_survival_fetcher(metrics, predict)

        ranked = rank_recipients(
            donor,
            recipients,
            top_k=safe_top_k,
            include_survival=include_survival,
            # Use non-blocking pre-fetched scorer to avoid per-recipient network calls.
            survival_fetcher=survival_fetcher,
            use_mock_if_unavailable=True,
        )

        enriched = []
        for item in ranked:
            recipient = recipients_by_id.get(item["recipient_id"])
            enriched.append(
                {
                    "recipient_id": item["recipient_id"],
                    "score": item["score"],
                    "explanation": item["explanation"],
                    "recipient": {
                        "full_name": getattr(recipient, "full_name", None),
                        "age": getattr(recipient, "age", None),
                        "blood_group": getattr(recipient, "blood_group", None),
                        "organ_needed": getattr(recipient, "organ_needed", None),
                        "urgency": getattr(recipient, "urgency", None),
                        "status": getattr(recipient, "status", None),
                        "hospital_id": str(getattr(recipient, "hospital_id", "")) if getattr(recipient, "hospital_id", None) else None,
                    },
                }
            )

        return {
            "donor_id": str(donor.id),
            "donor": {
                "full_name": donor.full_name,
                "blood_group": donor.blood_group,
                "organs_selected": donor.organs_selected,
                "location": donor.location,
                "status": donor.status.value if hasattr(donor.status, "value") else str(donor.status),
            },
            "total_candidates": len(enriched),
            "ranked_recipients": enriched,
        }
