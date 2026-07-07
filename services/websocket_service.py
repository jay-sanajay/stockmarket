"""WebSocket service for real-time price updates and strategy notifications."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import SessionLocal
from models.db_models import BreakoutSignal, BreakoutTrade, User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # user_id -> WebSocket
        self.strategy_subscriptions: Dict[int, Set[int]] = {}  # user_id -> set of strategy_ids
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection and register user."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.strategy_subscriptions[user_id] = set()
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: int):
        """Remove WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.strategy_subscriptions:
            del self.strategy_subscriptions[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_subscribers(self, message: dict, strategy_id: int):
        """Broadcast message to all users subscribed to a strategy."""
        for user_id, websocket in self.active_connections.items():
            if strategy_id in self.strategy_subscriptions.get(user_id, set()):
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    self.disconnect(user_id)
    
    def subscribe_to_strategy(self, user_id: int, strategy_id: int):
        """Subscribe user to strategy updates."""
        if user_id not in self.strategy_subscriptions:
            self.strategy_subscriptions[user_id] = set()
        self.strategy_subscriptions[user_id].add(strategy_id)
    
    def unsubscribe_from_strategy(self, user_id: int, strategy_id: int):
        """Unsubscribe user from strategy updates."""
        if user_id in self.strategy_subscriptions:
            self.strategy_subscriptions[user_id].discard(strategy_id)


# Global connection manager
manager = ConnectionManager()


async def handle_websocket_connection(websocket: WebSocket, user_id: int):
    """Handle WebSocket connection for a user."""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get('type')
            
            if message_type == 'subscribe':
                # Subscribe to strategy updates
                strategy_id = message.get('strategy_id')
                if strategy_id:
                    manager.subscribe_to_strategy(user_id, strategy_id)
                    await websocket.send_text(json.dumps({
                        'type': 'subscription_confirmed',
                        'strategy_id': strategy_id
                    }))
            
            elif message_type == 'unsubscribe':
                # Unsubscribe from strategy updates
                strategy_id = message.get('strategy_id')
                if strategy_id:
                    manager.unsubscribe_from_strategy(user_id, strategy_id)
                    await websocket.send_text(json.dumps({
                        'type': 'unsubscription_confirmed',
                        'strategy_id': strategy_id
                    }))
            
            elif message_type == 'ping':
                # Keep-alive ping
                await websocket.send_text(json.dumps({'type': 'pong'}))
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)


async def notify_signal_created(signal: BreakoutSignal):
    """Notify subscribers when a new signal is created."""
    message = {
        'type': 'signal_created',
        'data': {
            'id': signal.id,
            'strategy_id': signal.strategy_id,
            'symbol': signal.symbol,
            'signal_type': signal.signal_type,
            'signal_time': signal.signal_time.isoformat(),
            'price': signal.price,
            'pdh': signal.pdh,
            'pdl': signal.pdl,
            'body_percentage': signal.body_percentage,
            'volume_ratio': signal.volume_ratio,
            'confirmed': signal.confirmed
        }
    }
    
    await manager.broadcast_to_subscribers(message, signal.strategy_id)


async def notify_trade_created(trade: BreakoutTrade):
    """Notify subscribers when a new trade is created."""
    message = {
        'type': 'trade_created',
        'data': {
            'id': trade.id,
            'strategy_id': trade.strategy_id,
            'symbol': trade.symbol,
            'trade_type': trade.trade_type,
            'entry_price': trade.entry_price,
            'stop_loss': trade.stop_loss,
            'target_price': trade.target_price,
            'quantity': trade.quantity,
            'entry_time': trade.entry_time.isoformat(),
            'status': trade.status
        }
    }
    
    await manager.broadcast_to_subscribers(message, trade.strategy_id)


async def notify_trade_closed(trade: BreakoutTrade):
    """Notify subscribers when a trade is closed."""
    message = {
        'type': 'trade_closed',
        'data': {
            'id': trade.id,
            'strategy_id': trade.strategy_id,
            'symbol': trade.symbol,
            'exit_price': trade.exit_price,
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
            'exit_reason': trade.exit_reason,
            'pnl': trade.pnl,
            'pnl_percentage': trade.pnl_percentage,
            'status': trade.status
        }
    }
    
    await manager.broadcast_to_subscribers(message, trade.strategy_id)


async def notify_price_update(strategy_id: int, symbol: str, price: float, pdh: float, pdl: float):
    """Notify subscribers of price updates."""
    message = {
        'type': 'price_update',
        'data': {
            'strategy_id': strategy_id,
            'symbol': symbol,
            'price': price,
            'pdh': pdh,
            'pdl': pdl,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    await manager.broadcast_to_subscribers(message, strategy_id)


class RealTimePriceMonitor:
    """Monitors real-time prices and sends updates via WebSocket."""
    
    def __init__(self):
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}
    
    async def start_monitoring(self, strategy_id: int, symbols: List[str]):
        """Start monitoring prices for a strategy."""
        if strategy_id in self.monitoring_tasks:
            return
        
        task = asyncio.create_task(self._monitor_strategy(strategy_id, symbols))
        self.monitoring_tasks[strategy_id] = task
    
    def stop_monitoring(self, strategy_id: int):
        """Stop monitoring prices for a strategy."""
        if strategy_id in self.monitoring_tasks:
            self.monitoring_tasks[strategy_id].cancel()
            del self.monitoring_tasks[strategy_id]
    
    async def _monitor_strategy(self, strategy_id: int, symbols: List[str]):
        """Monitor prices for symbols in a strategy."""
        from services.breakout_strategy_service import DataFetcher
        
        async with DataFetcher() as fetcher:
            while True:
                try:
                    for symbol in symbols:
                        # Get current price and PDH/PDL
                        current_price = await fetcher.get_current_price(symbol)
                        pdh, pdl = await fetcher.get_previous_day_high_low(symbol)
                        
                        if current_price > 0:
                            await notify_price_update(strategy_id, symbol, current_price, pdh, pdl)
                    
                    # Wait before next update (30 seconds)
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error monitoring strategy {strategy_id}: {e}")
                    await asyncio.sleep(60)


# Global price monitor
price_monitor = RealTimePriceMonitor()
