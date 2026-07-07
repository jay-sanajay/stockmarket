"""WebSocket routes for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from services.auth_service import get_current_user_ws
from services.websocket_service import handle_websocket_connection

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for real-time updates."""
    # Authenticate user
    try:
        if not token:
            await websocket.close(code=4001, reason="Token required")
            return
        
        user = await get_current_user_ws(token)
        if not user:
            await websocket.close(code=4003, reason="Invalid token")
            return
        
        await handle_websocket_connection(websocket, user.id)
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
