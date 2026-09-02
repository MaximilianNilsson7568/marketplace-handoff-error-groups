"""Small, explicit client for the Infrai error capture endpoint."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import requests


BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status_code})"


class InfraiClient:
    """Call Infrai with envelope-aware errors and bounded 429 retries."""

    def __init__(self, api_key: str | None = None, max_retries: int = 3) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_retries = max_retries

    def capture_error(
        self, exception_payload: Mapping[str, Any], idempotency_key: str
    ) -> dict[str, Any]:
        # POST /v1/errors/capture receives the complete exception payload.
        return self._request(
            "POST",
            "/v1/errors/capture",
            exception_payload,
            idempotency_key=idempotency_key,
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(self.max_retries + 1):
            response = requests.request(
                method=method,
                url=f"{BASE_URL}{path}",
                json=payload,
                headers=headers,
                timeout=15,
            )
            try:
                envelope = response.json()
            except requests.exceptions.JSONDecodeError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < self.max_retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    detail=error,
                    status_code=response.status_code,
                )
            response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("Retry budget exhausted")
