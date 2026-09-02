"""Runnable example: capture a failed marketplace order handoff."""

from marketplace_handoff import (
    BuyerUpdate,
    OrderHandoffRequest,
    SellerAsset,
    run_order_handoff,
)
from infrai_client import InfraiClient


def deliver_asset(request: OrderHandoffRequest) -> str:
    raise ValueError(f"asset {request.asset.asset_id} is not ready for delivery")


def main() -> None:
    request = OrderHandoffRequest(
        order_id="order-1042",
        asset=SellerAsset(
            seller_id="seller-17", asset_id="model-card-8", asset_kind="model-card"
        ),
        buyer_update=BuyerUpdate(buyer_id="buyer-29", update_kind="purchase-confirmed"),
        stage="asset-delivery",
    )
    try:
        run_order_handoff(request, deliver_asset, InfraiClient())
    except ValueError:
        print("Captured order handoff error under marketplace-handoff/asset-delivery/model-card")


if __name__ == "__main__":
    main()
