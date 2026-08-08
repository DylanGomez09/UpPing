from tests.helpers import auth_headers, register_user


async def test_get_default_settings(client):
    await register_user(client, "settings@example.com")
    headers = await auth_headers(client, "settings@example.com")

    resp = await client.get("/settings", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {
        "ping_interval_ms": 1000,
        "timeout_ms": 1500,
        "auto_save_csv": True,
        "performance_mode": False,
    }


async def test_patch_settings_partial(client):
    await register_user(client, "settings@example.com")
    headers = await auth_headers(client, "settings@example.com")

    resp = await client.patch(
        "/settings", json={"ping_interval_ms": 2000}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ping_interval_ms"] == 2000
    assert body["timeout_ms"] == 1500
    assert body["auto_save_csv"] is True


async def test_patch_settings_invalid_422(client):
    await register_user(client, "settings@example.com")
    headers = await auth_headers(client, "settings@example.com")

    resp = await client.patch(
        "/settings", json={"ping_interval_ms": 1}, headers=headers
    )
    assert resp.status_code == 422


async def test_settings_require_auth(client):
    assert (await client.get("/settings")).status_code == 401
