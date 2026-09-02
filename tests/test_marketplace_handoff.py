from marketplace_handoff import BuyerUpdate, OrderHandoffRequest, SellerAsset, grouping_fingerprint


def make_request(order_id: str, seller_id: str, buyer_id: str) -> OrderHandoffRequest:
    return OrderHandoffRequest(
        order_id=order_id,
        asset=SellerAsset(seller_id=seller_id, asset_id="asset-1", asset_kind="model-card"),
        buyer_update=BuyerUpdate(buyer_id=buyer_id, update_kind="purchase-confirmed"),
        stage="asset-delivery",
    )


def test_equivalent_handoff_failures_share_a_group() -> None:
    first = make_request("order-1", "seller-1", "buyer-1")
    second = make_request("order-2", "seller-2", "buyer-2")

    assert grouping_fingerprint(first) == grouping_fingerprint(second) == [
        "marketplace-handoff",
        "asset-delivery",
        "model-card",
    ]
