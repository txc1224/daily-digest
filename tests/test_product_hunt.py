from fetchers import product_hunt


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_product_hunt_falls_back_when_api_returns_no_posts(monkeypatch):
    monkeypatch.setenv("PRODUCT_HUNT_TOKEN", "token")

    def fake_post(*args, **kwargs):
        return _DummyResponse({"data": {"posts": {"edges": []}}})

    def fake_fallback(limit):
        return [{"name": "fallback-product", "tagline": "备用数据", "url": "https://example.com", "votes": 0, "topics": []}]

    monkeypatch.setattr(product_hunt.requests, "post", fake_post)
    monkeypatch.setattr(product_hunt, "fetch_product_hunt_fallback", fake_fallback)

    results = product_hunt.fetch_product_hunt_trending(limit=5)

    assert results[0]["name"] == "fallback-product"


def test_product_hunt_uses_rss_when_token_missing(monkeypatch):
    monkeypatch.delenv("PRODUCT_HUNT_TOKEN", raising=False)

    def fake_fallback(limit):
        return [{"name": "rss-product", "tagline": "RSS 数据", "url": "https://example.com/rss", "votes": 0, "topics": []}]

    monkeypatch.setattr(product_hunt, "fetch_product_hunt_fallback", fake_fallback)

    results = product_hunt.fetch_product_hunt_trending(limit=3)

    assert results[0]["name"] == "rss-product"
