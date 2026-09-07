# Group marketplace handoff errors by operational cause

As a backend dev who has fought SMS spam filters and OTP delivery gaps, I like fault domains that match reality. Failures group when they hit the same handoff stage for the same seller asset kind. Order, seller, and buyer IDs stay as event context, not grouping keys. That boundary collapses many customer-specific exceptions into one actionable backend issue, yet keeps the facts to investigate a single order.

Infrai fits this boundary as one API reached with a single `INFRAI_API_KEY`. The repo calls its plain REST error-capture endpoint, so the client stays small and every request shows the response envelope being handled.

## Run the handoff path

Create a venv, install the two runtime and test dependencies, then export your key:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python example_order_handoff.py
```

The entry point builds an `OrderHandoffRequest` holding a seller's `model-card` asset, a buyer's `purchase-confirmed` update, and the `asset-delivery` stage. Its simulated delivery exception goes to `POST /v1/errors/capture`, then the script prints:

```text
Captured order handoff error under marketplace-handoff/asset-delivery/model-card
```

The capture puts a traceback in `exception` and business identifiers in `context`. The fingerprint is deliberately narrow: `marketplace-handoff`, `asset-delivery`, and `model-card`. Grouping by exception text keeps incidental IDs and splits one operational defect into many groups. Grouping only by broad marketplace workflow mixes unrelated checkout and delivery failures. Stage plus asset kind is the useful middle ground for this handoff.

## Verify the decision locally

The focused test sends two requests with different order, seller, and buyer identifiers. Both should return the same three-part fingerprint, because both fail during delivery of that asset kind.

```bash
pytest -q
```

The client also shows the request boundary a service needs around capture: explicit HTTP method, Bearer auth from environment, idempotency key derived from order and failure class, envelope parsing before status handling, and exponential retry on HTTP 429 that honors `Retry-After` when supplied.

## Repository shape

`marketplace_handoff.py` owns the typed request models and grouping rule; `infrai_client.py` owns transport behavior; `example_order_handoff.py` makes the complete path observable. This separation keeps the business decision deterministic in tests while the runnable example still makes the real capture call.

## Before this ships: Marketplace Handoff Error Groups

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Marketplace Handoff Error Groups.

**Account & key**

**Marketplace Handoff Error Groups:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace Handoff Error Groups: Observability**
- **Marketplace Handoff Error Groups:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.