"""Authentication tests."""
import re


def test_training_requires_login(client):
    resp = client.get("/training/", follow_redirects=False)
    assert resp.status_code == 303
    assert "/training/login" in resp.headers["location"]


def test_login_success_and_logout(client, admin_user, csrf_token):
    resp = client.post(
        "/training/login",
        data={"username": "test", "password": "password123", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers["location"] == "/training/"

    dashboard = client.get("/training/")
    assert dashboard.status_code == 200

    # Settings page always contains a CSRF-token form field.
    settings_page = client.get("/training/settings")
    token = re.search(r'name="csrf_token" value="([^"]+)"', settings_page.text).group(1)
    logout = client.post("/training/logout", data={"csrf_token": token}, follow_redirects=False)
    assert logout.status_code == 303


def test_login_wrong_password(client, admin_user, csrf_token):
    resp = client.post(
        "/training/login",
        data={"username": "test", "password": "wrong", "csrf_token": csrf_token},
    )
    assert resp.status_code == 401


def test_csrf_rejected(client, admin_user):
    resp = client.post(
        "/training/login",
        data={"username": "test", "password": "password123", "csrf_token": "bad"},
    )
    assert resp.status_code == 403
