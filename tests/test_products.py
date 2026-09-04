"""Product registry loader tests."""
import yaml

from app.services.products import load_products


def test_example_config_loads():
    products = load_products("config/products.example.yaml")
    assert any(p["id"] == "training" for p in products)


def test_missing_config_falls_back():
    products = load_products("nonexistent-file.yaml")
    assert any(p["id"] == "training" for p in products)


def test_disabled_products_hidden(tmp_path):
    path = tmp_path / "products.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "products": [
                    {"id": "a", "name": "A", "url": "/a/", "enabled": False, "order": 1},
                    {"id": "b", "name": "B", "url": "/b/", "enabled": True, "order": 2},
                ]
            }
        ),
        encoding="utf-8",
    )
    products = load_products(str(path))
    assert [p["id"] for p in products] == ["b"]


def test_order_respected(tmp_path):
    path = tmp_path / "products.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "products": [
                    {"id": "z", "name": "Z", "url": "/z/", "order": 30},
                    {"id": "a", "name": "A", "url": "/a/", "order": 10},
                ]
            }
        ),
        encoding="utf-8",
    )
    products = load_products(str(path))
    assert [p["id"] for p in products] == ["a", "z"]


def test_invalid_config_handled(tmp_path):
    path = tmp_path / "products.yaml"
    path.write_text("::: not valid yaml [", encoding="utf-8")
    products = load_products(str(path))
    assert any(p["id"] == "training" for p in products)


def test_hub_renders(client):
    resp = client.get("/hub/")
    assert resp.status_code == 200
    assert "Training Tracker" in resp.text
