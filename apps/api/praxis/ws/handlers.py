"""WebSocket handlers."""

from fastapi import WebSocket


async def session_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.close()
