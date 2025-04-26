import uuid

import httpx


params = {
    'queue': 'main',
    'qtype': 'exactly_once'
}
for i in range(9):
    payload = {
        'msg': 'test_msg',
        'any': 'key',
    }
    headers = {
        'X-MESSAGE-ID': str(uuid.uuid4()),
    }
    r = httpx.post(
        'http://localhost:8000/push?queue=main&qtype=exactly_once',
        data=payload,
        headers=headers,
    )
    print(r.json())
