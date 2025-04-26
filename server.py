import asyncio
import json
import logging
import uuid
from asyncio import Queue
from typing import AsyncIterable

import uvicorn
from fastapi import FastAPI, HTTPException, Header
from fastapi.params import Query, Body
from starlette import status
from starlette.responses import StreamingResponse
from starlette.types import Send


class PingingStreamingResponse(StreamingResponse):

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        async def stream() -> None:
            async for chunk in self.body_iterator:
                if not isinstance(chunk, (bytes, memoryview)):
                    chunk = chunk.encode(self.charset)
                await send({"type": "http.response.body", "body": chunk, "more_body": True})

        async def ping():
            while True:
                await asyncio.gather(
                    send({"type": "http.response.body", "body": b"ping", "more_body": True}),
                    asyncio.sleep(1)
                )

        await asyncio.gather(ping(), stream())
        await send({"type": "http.response.body", "body": b"", "more_body": False})

app = FastAPI()

CONNECTIONS: dict[str, Queue] = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@app.post("/push")
async def push(
    queue: str = Query(...),
    x_message_id: str = Header(...),
    body: dict = Body(...),
):
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='queue is required',
        )

    if queue not in CONNECTIONS:
        CONNECTIONS[queue] = Queue()

    queue = CONNECTIONS[queue]
    queue.put_nowait((body, x_message_id))


async def queue_iterator(queue_path: str, producer_id: str) -> AsyncIterable[bytes]:
    queue = CONNECTIONS[queue_path]

    while 1:
        data, msg_id = await queue.get()
        yield json.dumps(data).encode()
        queue.task_done()
        logger.info(f'{producer_id} produced message')
        await asyncio.sleep(0)


@app.get("/pull")
async def pull(queue: str = Query(...), x_consumer_id: str = Header(...)):
    if queue not in CONNECTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='queue not found',
        )

    producer_id = uuid.uuid4().hex
    logger.info('Producer coroutine: %s', producer_id)
    return PingingStreamingResponse(queue_iterator(queue, producer_id), media_type='text/event-stream')


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
