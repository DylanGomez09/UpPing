from httpx import AsyncClient

DEFAULT_PASSWORD = "supersecret1"


async def register_user(
    client: AsyncClient,
    email: str,
    password: str = DEFAULT_PASSWORD,
    display_name: str = "User",
) -> dict:
    resp = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(
    client: AsyncClient,
    email: str,
    password: str = DEFAULT_PASSWORD,
) -> dict:
    resp = await client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def auth_headers(
    client: AsyncClient,
    email: str,
    password: str = DEFAULT_PASSWORD,
) -> dict[str, str]:
    tokens = await login(client, email, password)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def ping_payload(**overrides) -> dict:
    payload = {
        "target_ip": "8.8.8.8",
        "avg_latency_ms": 12.5,
        "packets_sent": 10,
        "packets_received": 10,
        "loss_percent": 0.0,
        "ran_at": "2026-08-08T10:00:00Z",
    }
    payload.update(overrides)
    return payload
