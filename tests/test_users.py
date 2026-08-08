from tests.helpers import auth_headers, ping_payload, register_user


async def test_get_me(client):
    await register_user(client, "me@example.com", display_name="Carol")
    headers = await auth_headers(client, "me@example.com")

    resp = await client.get("/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@example.com"
    assert body["display_name"] == "Carol"
    assert body["license_tier"] == "standard"
    assert body["total_tests"] == 0
    assert "created_at" in body


async def test_me_total_tests_counts(client):
    await register_user(client, "me@example.com")
    headers = await auth_headers(client, "me@example.com")
    await client.post("/tests", json=ping_payload(), headers=headers)
    await client.post("/tests", json=ping_payload(), headers=headers)

    body = (await client.get("/me", headers=headers)).json()
    assert body["total_tests"] == 2


async def test_update_display_name(client):
    await register_user(client, "me@example.com", display_name="Antes")
    headers = await auth_headers(client, "me@example.com")

    resp = await client.patch(
        "/me", json={"display_name": "Despues"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Despues"

    body = (await client.get("/me", headers=headers)).json()
    assert body["display_name"] == "Despues"


async def test_patch_me_invalid_422(client):
    await register_user(client, "me@example.com")
    headers = await auth_headers(client, "me@example.com")

    resp = await client.patch("/me", json={"display_name": ""}, headers=headers)
    assert resp.status_code == 422


async def test_me_requires_auth(client):
    assert (await client.get("/me")).status_code == 401
