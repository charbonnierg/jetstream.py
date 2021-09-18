from __future__ import annotations

from asyncio import Future, Queue, TimeoutError, create_task, wait_for
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional

from nats.aio.client import Client as NC
from nats.aio.client import Msg as _Msg
from nats.aio.errors import ErrTimeout, NatsError

from .errors import ErrSubscriptionNotStarted


class Msg:
    __slots__ = ("subject", "reply", "data", "sid", "_client", "headers")

    def __init__(
        self,
        subject: str = "",
        reply: str = "",
        data: bytes = b"",
        sid: int = 0,
        client: Optional[NC] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.subject = subject
        self.reply = reply
        self.data = data
        self.sid = sid
        self._client = client
        self.headers = headers

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: subject='{self.subject}' reply='{self.reply}' data='{self.data[:10].decode()}...'>"

    async def respond(self, data: bytes) -> None:
        """Respond to message using message reply field as subject"""
        if not self.reply:
            raise NatsError("no reply subject available")
        if not self._client:
            raise NatsError("client not set")

        await self._client.publish(self.reply, data)

    async def ack(self) -> None:
        """Acknowledge a JetStream message"""
        await self.respond(b"")

    @classmethod
    def _from_msg(self, msg: _Msg, nc: Optional[NC] = None) -> Msg:
        return Msg(
            msg.subject,
            msg.reply,
            msg.data,
            msg.sid,
            nc or getattr(msg, "_client", nc),
            getattr(msg, "headers", None),
        )


class Subscription:
    def __init__(
        self,
        client: NC,
        subject: str,
        /,
        *,
        queue: str = "",
        cb: Optional[Callable[..., Awaitable[Any]]] = None,
        **kwargs: Any,
    ) -> None:
        self._nc = client
        self.subject = subject
        self.queue = queue
        self.cb = cb
        self._inbox_queue: Queue[Msg] = Queue()
        self._delivery_queues: Dict[str, Queue[Msg]] = {}
        self.options = kwargs

    @property
    def sid(self) -> int:
        try:
            return self._sid  # type: ignore[no-any-return]
        except AttributeError:
            raise ErrSubscriptionNotStarted

    async def start(self) -> None:
        """Start a subscrpition."""
        if self.cb:
            self._sid = await self._nc.subscribe(
                self.subject, queue=self.queue, cb=self.cb, **self.options
            )
        else:
            self._sid = await self._nc.subscribe(
                self.subject, queue=self.queue, cb=self._listener, **self.options
            )

    async def drain(self, join: bool = False) -> None:
        """Removes interest in a subject, but will process remaining messages."""
        await self._nc.drain(sid=self.sid)
        # Optionaly wait for inbox queue and delivery queues to be processed
        if join and self.cb is None:
            await self._inbox_queue.join()
            while True:
                try:
                    _, queue = self._delivery_queues.popitem()
                except KeyError:
                    break
                else:
                    await queue.join()
        # Remove self._sid now that subscription is no longer active
        del self._sid

    async def stop(self) -> None:
        """Stop a subscription."""
        try:
            await self._nc.unsubscribe(self.sid)
        except ErrSubscriptionNotStarted:
            pass

    async def next_msg(self, timeout: Optional[int] = None) -> Msg:
        """Wait for next message on subscription.

        Note that this function does not
        """
        if self.cb:
            raise Exception(
                "next_msg() cannot be used when subscription uses a custom callback"
            )

        future: Future[Msg] = Future()

        # Create a coroutine function that wait for message
        async def _next_msg() -> None:
            msg = await self._inbox_queue.get()
            future.set_result(msg)

        # Create a task that wraps the coroutine
        task = create_task(_next_msg())

        try:
            # Wait for the task using a timeout
            msg = await wait_for(future, timeout)
            # Notify task done for inbox queue
            self._inbox_queue.task_done()
            # Return the message
            return msg
        except TimeoutError:
            future.cancel()
            task.cancel()
            raise ErrTimeout

    async def _listener(self, _msg: _Msg) -> None:
        """Listenner that store messages in queues."""
        msg = Msg._from_msg(_msg, self._nc)
        # Add message to inbox queue
        await self._inbox_queue.put(msg)
        # Also forward message to additional delivery queues
        for _, queue in self._delivery_queues.items():
            await queue.put(msg)

    def create_delivery_queue(self, name: str) -> Queue[Msg]:
        """Add a new queue to the subscription."""
        # Queues must have a unique name
        if name in self._delivery_queues:
            raise ValueError(f"Queue {name} already exists.")
        # Store the queue so that we can distribute messages later
        queue = self._delivery_queues[name] = Queue()
        return queue

    async def __aiter__(self) -> AsyncIterator[Msg]:
        """Iterate over subscription messages."""
        while True:
            yield await self.next_msg()

    async def __aenter__(self) -> Subscription:
        await self.start()
        return self

    async def __aexit__(self, *_: Any, **__: Any) -> None:
        # Be default stop is used instead of drain.
        # User can still call drain() within a context manager if it's a requirement
        await self.stop()


__all__ = ["Subscription"]
