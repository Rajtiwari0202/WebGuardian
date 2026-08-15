import asyncio
import logging
from typing import Dict, List, Any

logger = logging.getLogger("webguardian")

class EventBroker:
    def __init__(self):
        # Maps run_id to lists of asyncio.Queue listeners
        self.listeners: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, run_id: str) -> asyncio.Queue:
        if run_id not in self.listeners:
            self.listeners[run_id] = []
        queue = asyncio.Queue()
        self.listeners[run_id].append(queue)
        logger.debug(f"EventBroker: Client subscribed to run {run_id}")
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue):
        if run_id in self.listeners:
            if queue in self.listeners[run_id]:
                self.listeners[run_id].remove(queue)
            if not self.listeners[run_id]:
                del self.listeners[run_id]
        logger.debug(f"EventBroker: Client unsubscribed from run {run_id}")

    def publish(self, run_id: str, event: Dict[str, Any]):
        if run_id in self.listeners:
            logger.info(f"EventBroker: Publishing event to run {run_id}: {event.get('node')} - {event.get('message')}")
            for queue in self.listeners[run_id]:
                queue.put_nowait(event)

# Global singleton event broker
event_broker = EventBroker()
