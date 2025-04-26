import asyncio
import json
import uuid

import httpx
import pytest


@pytest.fixture
def client():
    return httpx.AsyncClient(
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-MESSAGE-ID': uuid.uuid4().hex,
        },
        timeout=3,
    )


async def drain_messages(client, queue_name, expected_amount):
    r_messages = []
    headers = {
        'X-CONSUMER-ID': uuid.uuid4().hex,
    }
    try:
        async with client.stream(
            'GET',
            f'http://localhost:8000/pull?queue={queue_name}',
            timeout=3,
            headers=headers
        ) as response:
            async for chunk in response.aiter_bytes():
                if chunk == b'ping':
                    continue
                r_messages.append(json.loads(chunk))
                if r_messages.__len__() >= expected_amount:
                    break
    except httpx.ReadTimeout as _:
        raise ValueError('Timed out while pulling message!')
    except json.decoder.JSONDecodeError as _:
        raise ValueError('Message cant be decoded!')

    return r_messages


@pytest.mark.asyncio
async def test_push_message(client):
    r = await client.post(
        f'http://localhost:8000/push?queue={uuid.uuid4().hex}',
        json={'message': 'Hello'},
    )

    assert r.status_code == 200


@pytest.mark.asyncio
async def test_pull_message(client):
    payload = {'message': 'Hello'}
    await client.post(
        'http://localhost:8000/push?queue=test123',
        json=payload,
    )

    r_m = await drain_messages(client, 'test123', 1)

    assert r_m == [payload]


@pytest.mark.asyncio
async def test_push_pull_multiple_message(client):
    expected = []
    queue_name = uuid.uuid4().hex
    for i in range(300):
        headers = {
            'X-MESSAGE-ID': uuid.uuid4().hex,
        }
        payload = {'message': 'Hello {}'.format(uuid.uuid4().hex)}
        await client.post(
            f'http://localhost:8000/push?queue={queue_name}',
            json=payload,
            headers=headers,
        )
        expected.append(payload)

    r_m = await drain_messages(client, queue_name, 300)

    assert r_m == expected


@pytest.mark.asyncio
async def test_pull_with_ping(client):
    payload = {'message': 'Hello'}
    queue_name = uuid.uuid4().hex
    await client.post(
        f'http://localhost:8000/push?queue={queue_name}',
        json=payload,
    )

    pings_c = 3
    try:
        async with client.stream('GET', f'http://localhost:8000/pull?queue={queue_name}', timeout=4) as response:
            async for chunk in response.aiter_bytes():
                if chunk == b'ping':
                    pings_c -= 1

                if pings_c <= 0:
                    break

    except httpx.ReadTimeout as _:
        raise ValueError('No pings received while waiting for message!')


@pytest.mark.asyncio
async def test_multiple_consumer(client):
    queue_name = uuid.uuid4().hex
    expected = {}

    payload = {'message': 'Test'}
    await client.post(
        f'http://localhost:8000/push?queue={queue_name}',
        json=payload,
    )

    await drain_messages(client, queue_name, 1)

    async def mass_producer():
        for i in range(300):
            message_id = uuid.uuid4().hex
            headers = {
                'X-MESSAGE-ID': message_id,
            }
            payload = {'message': 'Hello {}'.format(uuid.uuid4().hex), 'id': message_id}

            await client.post(
                f'http://localhost:8000/push?queue={queue_name}',
                json=payload,
                headers=headers,
            )
            expected[message_id] = payload

    await asyncio.sleep(0)
    r = await asyncio.gather(
        *[*(drain_messages(client, queue_name, 50) for _ in range(6)), mass_producer()],
        return_exceptions=True
    )
    total_messages = 0

    for i in range(6):
        total_messages += len(r[i])
        for j in r[i]:
            expected.pop(j['id'], None)

    assert total_messages == 300
    assert expected == {} # Received all required messages
