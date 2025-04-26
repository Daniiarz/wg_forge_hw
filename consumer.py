import asyncio
import uuid

import httpx

client = httpx.AsyncClient()


async def main():
    consumer_id = uuid.uuid4().hex
    print('started consumer:', consumer_id)
    m_count = 0
    async with client.stream('GET', 'http://localhost:8000/pull?queue=main', timeout=100) as response:
        async for chunk in response.aiter_bytes():
            m_count += 1
            print(f'consumer_id: {consumer_id} content: {chunk}, m_count: {m_count}')


async def runner():
    await asyncio.gather(*[main() for _ in range(3)])


if __name__ == "__main__":
    asyncio.run(runner())
