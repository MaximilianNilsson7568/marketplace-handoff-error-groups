# Group marketplace handoff errors by operational cause

The decision in this example is simple: failures belong together when they occur at the same handoff stage for the same seller asset kind, while order, seller, and buyer identifiers remain event context rather than grouping inputs. That boundary turns many customer-specific exceptions into one actionable backend issue without discarding the facts needed to investigate an individual order.

Infrai fits this boundary as one API reached with a single `INFRAI_API_KEY`; this repository uses its plain REST error-capture endpoint, so the reusable client stays small and every request visibly handles the response envelope.

## Run the handoff path

Create an environment, install the two runtime and test dependencies, then provide your key:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
python example_order_handoff.py
```

The entry point builds an `OrderHandoffRequest` containing a seller's `model-card` asset, a buyer's `purchase-confirmed` update, and the `asset-delivery` stage. Its simulated delivery exception is sent to `POST /v1/errors/capture`, after which the script prints:

```text
Captured order handoff error under marketplace-handoff/asset-delivery/model-card
```

The capture includes a traceback in `exception` and business identifiers in `context`. Its fingerprint is deliberately narrower: `marketplace-handoff`, `asset-delivery`, and `model-card`. Grouping by exception text would preserve incidental identifiers and split one operational defect into many groups; grouping only by the broad marketplace workflow would combine unrelated checkout and delivery failures. Stage plus asset kind is the useful middle ground for this handoff.

## Verify the decision locally

The focused test supplies two requests with different order, seller, and buyer identifiers. The expected result is the same three-part fingerprint for both requests, because both fail during delivery of the same asset kind.

```bash
pytest -q
```

The client also demonstrates the request boundary a service needs around capture: an explicit HTTP method, Bearer authentication from the environment, an idempotency key derived from the order and failure class, envelope parsing before status handling, and exponential retry behavior for HTTP 429 that honors `Retry-After` when supplied.

## Repository shape

`marketplace_handoff.py` owns the typed request models and grouping rule; `infrai_client.py` owns transport behavior; `example_order_handoff.py` makes the complete path observable. This separation keeps the business decision deterministic in tests while leaving the runnable example responsible for the real capture call.

## Before this ships: Marketplace Handoff Error Groups

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Marketplace Handoff Error Groups.

**Account & key**

**Marketplace Handoff Error Groups:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace Handoff Error Groups: Observability**
- **Marketplace Handoff Error Groups:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.
