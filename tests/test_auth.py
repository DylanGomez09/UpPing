from tests.helpers import login, register_user


async def test_register_success(client):
    data = await register_user(client, "alice@example.com", display_name="Alice")
    assert data["email"] == "alice@example.com"
    assert data["display_name"] == "Alice"
    assert data["license_tier"] == "standard"
    assert "password_hash" not in data


async def test_register_duplicate_email_409(client):
    await register_user(client, "bob@example.com")
    resp = await client.post(
        "/auth/register",
        json={
            "email": "bob@example.com",
            "password": "supersecret1",
            "display_name": "Bob",
        },
    )
    assert resp.status_code == 409
    assert "detail" in resp.json()


async def test_register_short_password_422(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "x@example.com", "password": "short", "display_name": "X"},
    )
    assert resp.status_code == 422


async def test_login_success_returns_tokens(client):
    await register_user(client, "carol@example.com")
    data = await login(client, "carol@example.com")
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["expires_in"] > 0


async def test_login_wrong_password_401(client):
    await register_user(client, "dave@example.com")
    resp = await client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "wrongpass1"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


async def test_login_rate_limited(client):
    email = "erin@example.com"
    for _ in range(5):
        resp = await client.post(
            "/auth/login",
            json={"email": email, "password": "wrongpass1"},
        )
        assert resp.status_code == 401
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "wrongpass1"},
    )
    assert resp.status_code == 429


async def test_refresh_rotates_token(client):
    await register_user(client, "frank@example.com")
    tokens = await login(client, "frank@example.com")

    resp = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    new = resp.json()
    assert new["access_token"]
    assert new["refresh_token"] != tokens["refresh_token"]

    resp2 = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp2.status_code == 401


async def test_logout_revokes_refresh_token(client):
    await register_user(client, "grace@example.com")
    tokens = await login(client, "grace@example.com")

    resp = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 204

    resp2 = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp2.status_code == 401
