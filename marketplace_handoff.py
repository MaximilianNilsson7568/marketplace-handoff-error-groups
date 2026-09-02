"""Marketplace request models and the error-grouping business decision."""

from __future__ import annotations

import hashlib
import traceback
from dataclasses import dataclass
from typing import Callable, TypeVar

from infrai_client import InfraiClient


T = TypeVar("T")


@dataclass(frozen=True)
class SellerAsset:
    seller_id: str
    asset_id: str
    asset_kind: str


@dataclass(frozen=True)
class BuyerUpdate:
    buyer_id: str
    update_kind: str


@dataclass(frozen=True)
class OrderHandoffRequest:
    order_id: str
    asset: SellerAsset
    buyer_update: BuyerUpdate
    stage: str


def grouping_fingerprint(request: OrderHandoffRequest) -> list[str]:
    """Group operationally identical failures, independent of customer identity."""
    return ["marketplace-handoff", request.stage, request.asset.asset_kind]


def run_order_handoff(
    request: OrderHandoffRequest,
    handoff: Callable[[OrderHandoffRequest], T],
    client: InfraiClient,
) -> T:
    """Execute a handoff, capture a domain-shaped exception, then re-raise it."""
    try:
        return handoff(request)
    except Exception as exc:
        fingerprint = grouping_fingerprint(request)
        stable_key = "|".join([request.order_id, *fingerprint, type(exc).__name__])
        idempotency_key = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
        client.capture_error(
            {
                "title": f"Order handoff failed at {request.stage}",
                "message": f"{type(exc).__name__}: {exc}",
                "level": "error",
                "fingerprint": fingerprint,
                "exception": traceback.format_exc(),
                "context": {
                    "order_id": request.order_id,
                    "seller_id": request.asset.seller_id,
                    "asset_id": request.asset.asset_id,
                    "asset_kind": request.asset.asset_kind,
                    "buyer_id": request.buyer_update.buyer_id,
                    "buyer_update_kind": request.buyer_update.update_kind,
                    "handoff_stage": request.stage,
                },
            },
            idempotency_key=idempotency_key,
        )
        raise
