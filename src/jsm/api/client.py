from typing import Any, Callable, Optional

from nats.aio.client import Client as NC
from nats.aio.client import Msg

from .mixins.consumers import ConsumersMixin
from .mixins.infos import AccountInfosMixin
from .mixins.streams import StreamsMixin
from .subscription import Subscription


class Client(NC, AccountInfosMixin, ConsumersMixin, StreamsMixin):
    """Python client for JetStream NATS servers.

    The client exposes user friendly methods which in turn leverage NATS python client from `nats.py`
    and perform NATS requests according to Jetstream NATS API.

    Docs:
        * Jetstream NATS API Reference: <https://docs.nats.io/jetstream/nats_api_reference>

    Examples:

    - Create and connect a client:

    >>> from jsm.api import Client as JS

    >>> js = JS()

    >>> async def main():
    >>>     await js.connect()

    - Get account info

    >>> await.js.account_info()

    - List streams

    >>> await js.stream_list()

    - Create a new stream

    >>> await js.stream_create("DEMO", subjects="demo.>")

    - Check that the stream was created

    >>> stream_names_res = await js.stream_names()
    >>> assert "DEMO" in stream_names_res.streams

    - Get info about a stream

    >>> stream_info = await js.stream_info("DEMO")

    - Create a consumer

    >>> await js.consumer_durable_create("DEMO", "app-consumer-01")

    - Publish a message and fetch it using the consumer

    >>> await js.publish("demo.foo", b"bar")
    >>> msg = await js.consumer_msg_next("DEMO", "app-consumer-01")
    >>> assert msg.data == b"bar"

    - Delete a consumer

    >>> await js.consumer_delete("DEMO", "app-consumer-01")
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        default_timeout: float = 0.5,
        raise_on_error: bool = False,
    ):
        super().__init__()
        self._prefix = f"$JS.{domain}.API" if domain else "$JS.API"
        self._timeout = default_timeout
        self._raise_on_error = raise_on_error

    def create_subscribtion(
        self,
        subject: str,
        queue: str = "",
        cb: Optional[Callable[[Msg], Any]] = None,
        **kwargs: Any,
    ) -> Subscription:
        """Create a subscription but does not start it automatically."""
        return Subscription(self, subject, cb=cb, queue=queue, **kwargs)

    async def acknowledge(self, msg: Msg) -> None:
        """Acknoledge a message received by a consumer."""
        await self.publish(msg.reply, b"")
