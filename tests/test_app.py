"""
Integration tests for the Flask shopping app.

Each test runs against a fresh copy of the seeded database, so the
committed productdb.db is never modified.
"""

import os
import shutil
import sqlite3
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDED_DB = os.path.join(ROOT, "productdb.db")


@pytest.fixture()
def client(monkeypatch):
    tmp_dir = tempfile.mkdtemp()
    db_copy = os.path.join(tmp_dir, "test.db")
    shutil.copy(SEEDED_DB, db_copy)

    import app as shop
    monkeypatch.setattr(shop, "DB_PATH", db_copy)
    shop.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    with shop.app.test_client() as c:
        c.db_path = db_copy
        yield c

    shutil.rmtree(tmp_dir)


def csrf(client):
    """Load a page so a CSRF token is generated, then read it from the session."""
    client.get("/")
    with client.session_transaction() as sess:
        return sess["csrf_token"]


def register(client, username, email, password="Password123!"):
    token = csrf(client)
    return client.post("/register", data={
        "username": username, "email": email,
        "password": password, "confirm_password": password,
        "csrf_token": token,
    })


def login(client, username, password="Password123!"):
    token = csrf(client)
    return client.post("/login", data={"username": username, "password": password, "csrf_token": token})


def user_id(client):
    with client.session_transaction() as sess:
        return sess["user_id"]


def first_product_id(client):
    con = sqlite3.connect(client.db_path)
    try:
        return con.execute("SELECT id FROM products ORDER BY id LIMIT 1").fetchone()[0]
    finally:
        con.close()


# ── Public pages ─────────────────────────────────────────────

def test_home_and_products_load(client):
    assert client.get("/").status_code == 200
    assert client.get("/products").status_code == 200


def test_unknown_product_redirects_to_catalogue(client):
    response = client.get("/product/999999")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/products")


def test_unknown_page_returns_404(client):
    assert client.get("/no-such-page").status_code == 404


# ── Authentication ───────────────────────────────────────────

def test_register_then_login(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    with client.session_transaction() as sess:
        assert sess["logged_out"] is False
        assert sess["username"] == "alice"


def test_login_starts_a_fresh_session(client):
    register(client, "alice", "alice@example.com")
    with client.session_transaction() as sess:
        sess["planted"] = "value-set-before-login"
        old_token = sess.get("csrf_token")
    login(client, "alice")
    with client.session_transaction() as sess:
        assert "planted" not in sess
        assert sess.get("csrf_token") != old_token


def test_wrong_password_does_not_log_in(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice", "wrong-password")
    with client.session_transaction() as sess:
        assert sess.get("logged_out", True) is True


def test_password_is_hashed_in_database(client):
    register(client, "alice", "alice@example.com")
    con = sqlite3.connect(client.db_path)
    stored = con.execute("SELECT password FROM users WHERE username = 'alice'").fetchone()[0]
    con.close()
    assert stored.startswith("pbkdf2:sha256")
    assert "Password123!" not in stored


def test_sql_injection_in_login_is_harmless(client):
    login(client, "' OR '1'='1", "' OR '1'='1")
    with client.session_transaction() as sess:
        assert sess.get("logged_out", True) is True


# ── CSRF ─────────────────────────────────────────────────────

def test_login_without_csrf_token_is_rejected(client):
    register(client, "alice", "alice@example.com")
    client.post("/login", data={"username": "alice", "password": "Password123!"})
    with client.session_transaction() as sess:
        assert sess.get("logged_out", True) is True


def test_post_without_csrf_token_is_rejected(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    uid, pid = user_id(client), first_product_id(client)

    response = client.post(f"/products/{uid}/{pid}", data={"quantity": 1})
    assert response.status_code in (302, 400, 403)

    con = sqlite3.connect(client.db_path)
    count = con.execute("SELECT COUNT(*) FROM Basket WHERE user_id = ?", (uid,)).fetchone()[0]
    con.close()
    assert count == 0


def test_add_to_basket_with_csrf_token(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    uid, pid = user_id(client), first_product_id(client)

    client.post(f"/products/{uid}/{pid}", data={"quantity": 2, "csrf_token": csrf(client)})

    con = sqlite3.connect(client.db_path)
    qty = con.execute("SELECT quantity FROM Basket WHERE user_id = ? AND product_id = ?", (uid, pid)).fetchone()[0]
    con.close()
    assert qty == 2


def test_wishlist_toggle_rejects_get_requests(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    uid, pid = user_id(client), first_product_id(client)
    assert client.get(f"/favorite/{uid}/{pid}").status_code == 405


def test_wishlist_toggle_with_post_and_csrf(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    uid, pid = user_id(client), first_product_id(client)

    client.post(f"/favorite/{uid}/{pid}", data={"csrf_token": csrf(client)})

    con = sqlite3.connect(client.db_path)
    count = con.execute("SELECT COUNT(*) FROM Favorites WHERE user_id = ?", (uid,)).fetchone()[0]
    con.close()
    assert count == 1


# ── Authorisation: users cannot see each other's data ───────

def test_user_cannot_view_another_users_basket_or_wishlist(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    alice_id = user_id(client)
    pid = first_product_id(client)
    client.post(f"/products/{alice_id}/{pid}", data={"quantity": 1, "csrf_token": csrf(client)})
    client.get("/logout")

    register(client, "bob", "bob@example.com")
    login(client, "bob")

    basket = client.get(f"/basket/{alice_id}")
    wishlist = client.get(f"/favorite/{alice_id}")

    # The 403 handler redirects to the home page with an "Access denied" message
    assert basket.status_code == 302 and basket.headers["Location"].endswith("/")
    assert wishlist.status_code == 302 and wishlist.headers["Location"].endswith("/")


def test_user_cannot_add_to_another_users_basket(client):
    register(client, "alice", "alice@example.com")
    login(client, "alice")
    alice_id = user_id(client)
    client.get("/logout")

    register(client, "bob", "bob@example.com")
    login(client, "bob")
    pid = first_product_id(client)
    client.post(f"/products/{alice_id}/{pid}", data={"quantity": 1, "csrf_token": csrf(client)})

    con = sqlite3.connect(client.db_path)
    count = con.execute("SELECT COUNT(*) FROM Basket WHERE user_id = ?", (alice_id,)).fetchone()[0]
    con.close()
    assert count == 0


def test_checkout_requires_login(client):
    response = client.get("/checkout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
