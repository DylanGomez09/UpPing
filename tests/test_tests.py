from uuid import uuid4

from tests.helpers import auth_headers, ping_payload, register_user


async def test_create_test_201(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")

    resp = await client.post("/tests", json=ping_payload(), headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["target_ip"] == "8.8.8.8"
    assert body["avg_latency_ms"] == 12.5
    assert body["loss_percent"] == 0.0


async def test_create_test_validation_422(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")

    resp = await client.post(
        "/tests",
        json=ping_payload(packets_received=15, packets_sent=10),
        headers=headers,
    )
    assert resp.status_code == 422


async def test_list_tests_returns_own_tests(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")
    await client.post(
        "/tests", json=ping_payload(target_ip="1.1.1.1"), headers=headers
    )
    await client.post(
        "/tests",
        json=ping_payload(target_ip="8.8.4.4", avg_latency_ms=22.0),
        headers=headers,
    )

    resp = await client.get("/tests", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["limit"] == 20
    assert body["offset"] == 0


async def test_list_tests_filter_by_target_ip(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")
    await client.post(
        "/tests", json=ping_payload(target_ip="1.1.1.1"), headers=headers
    )
    await client.post(
        "/tests", json=ping_payload(target_ip="8.8.4.4"), headers=headers
    )

    resp = await client.get(
        "/tests", headers=headers, params={"target_ip": "1.1.1.1"}
    )
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["target_ip"] == "1.1.1.1"


async def test_list_tests_pagination(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")
    for i in range(5):
        await client.post(
            "/tests",
            json=ping_payload(target_ip=f"10.0.0.{i + 1}"),
            headers=headers,
        )

    first = await client.get(
        "/tests", headers=headers, params={"limit": 2, "offset": 0}
    )
    first_body = first.json()
    assert len(first_body["items"]) == 2
    assert first_body["total"] == 5

    second = await client.get(
        "/tests", headers=headers, params={"limit": 2, "offset": 2}
    )
    assert len(second.json()["items"]) == 2

    ids = {item["id"] for item in first_body["items"]} | {
        item["id"] for item in second.json()["items"]
    }
    assert len(ids) == 4


async def test_get_test_detail(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")
    created = (
        await client.post(
            "/tests", json=ping_payload(target_ip="9.9.9.9"), headers=headers
        )
    ).json()

    resp = await client.get(f"/tests/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["target_ip"] == "9.9.9.9"


async def test_get_test_404_for_unknown_id(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")

    resp = await client.get(f"/tests/{uuid4()}", headers=headers)
    assert resp.status_code == 404


async def test_delete_test(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")
    created = (
        await client.post("/tests", json=ping_payload(), headers=headers)
    ).json()

    resp = await client.delete(f"/tests/{created['id']}", headers=headers)
    assert resp.status_code == 204

    resp = await client.get(f"/tests/{created['id']}", headers=headers)
    assert resp.status_code == 404


async def test_export_csv(client):
    await register_user(client, "tests@example.com")
    headers = await auth_headers(client, "tests@example.com")
    await client.post(
        "/tests", json=ping_payload(target_ip="1.1.1.1"), headers=headers
    )
    await client.post(
        "/tests", json=ping_payload(target_ip="8.8.4.4"), headers=headers
    )

    resp = await client.get("/tests/export", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    content = resp.text
    assert content.splitlines()[0] == (
        "id,target_ip,avg_latency_ms,packets_sent,"
        "packets_received,loss_percent,ran_at,created_at"
    )
    assert "1.1.1.1" in content
    assert "8.8.4.4" in content


async def test_cannot_access_other_users_test(client):
    await register_user(client, "alice@example.com")
    headers_a = await auth_headers(client, "alice@example.com")
    created = (
        await client.post(
            "/tests", json=ping_payload(target_ip="5.5.5.5"), headers=headers_a
        )
    ).json()

    await register_user(client, "bob@example.com")
    headers_b = await auth_headers(client, "bob@example.com")

    resp = await client.get(f"/tests/{created['id']}", headers=headers_b)
    assert resp.status_code == 404

    resp = await client.delete(f"/tests/{created['id']}", headers=headers_b)
    assert resp.status_code == 404

    resp = await client.get("/tests", headers=headers_b)
    assert resp.json()["total"] == 0


async def test_tests_require_auth(client):
    assert (await client.get("/tests")).status_code == 401
    assert (
        await client.post("/tests", json=ping_payload())
    ).status_code == 401
