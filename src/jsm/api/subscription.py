from __future__ import annotations

from asyncio import Queue, wait_for
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Optional,
)

from loguru import logger
from nats.aio.client import Msg

if TYPE_CHECKING:  # pragma: no cover
    from .client import Client


class Subscription:
    def __init__(
        self,
        client: Client,
        subject: str,
        /,
        *,
        cb: Optional[Callable[..., Awaitable[Any]]] = None,
        **kwargs: Any,
    ) -> None:
        self._client = client
        self._subscription: Optional[int] = None
        self._delivery_queues: Dict[str, Queue[Msg]] = {}
        self.subject = subject
        if cb:
            self.cb = cb
            self._queue: Optional[Queue[Msg]] = None
        else:
            self.cb = self.listener
            self._queue = Queue()
        self.options = kwargs

    async def start(self) -> None:
        """Start a subscrpition."""
        self._subscription = await self._client.subscribe(
            self.subject, cb=self.cb, **self.options
        )

    async def stop(self) -> None:
        """Stop a subscription."""
        if not self._subscription:
            await self._client.unsubscribe(self._subscription)

    async def listener(self, msg: Msg) -> None:
        """Listenner that store messages in queues."""
        if self._queue is None:
            raise Exception("Listenner cannot be used with custom callback.")
        logger.trace(f"received new message on subject {msg.subject}")
        await self._queue.put(msg)
        for _, queue in self._delivery_queues.items():
            await queue.put(msg)

    async def next_message(self, timeout: Optional[int] = None) -> Msg:
        """Wait for next message on subscription."""
        if self._queue is None:
            raise Exception("next_message() cannot be used with custom callback.")
        if timeout:
            return await wait_for(self._queue.get(), timeout=timeout)
        else:
            return await self._queue.get()

    def add_queue(self, name: str) -> Queue[Msg]:
        """Add a new queue to the subscription."""
        if self._queue is None:
            raise Exception("Add queue cannot be used with custom callback.")
        if name in self._delivery_queues:
            raise ValueError(f"Queue {name} already exists.")
        queue = self._delivery_queues[name] = Queue()
        return queue

    async def __aiter__(self) -> AsyncIterator[Msg]:
        """Iterate over subscription messages."""
        while True:
            yield await self.next_message()

    async def __aenter__(self) -> Subscription:
        await self.start()
        return self

    async def __aexit__(self, *_: Any, **__: Any) -> None:
        await self.stop()


__all__ = ["Subscription"]
