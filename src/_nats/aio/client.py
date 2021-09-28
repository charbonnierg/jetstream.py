# Copyright 2016-2021 The NATS Authors
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import asyncio
from asyncio.futures import Future
from asyncio.streams import StreamReader, StreamWriter
from asyncio.tasks import Task
import json
import time
import ssl
import ipaddress
import base64
import warnings
from random import shuffle
from urllib.parse import ParseResult, urlparse
import sys
import logging
from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Union,
    Tuple,
)
from email.parser import BytesParser

from _nats.aio.errors import *
from _nats.aio.nuid import NUID
from _nats.aio.types import ClientStats, ServerInfos
from _nats.protocol.parser import *
from _nats.protocol import command as prot_command

__version__ = "2.0.0-dev"
__lang__ = "python3"
_logger = logging.getLogger(__name__)
PROTOCOL = 1

INFO_OP = b"INFO"
CONNECT_OP = b"CONNECT"
PING_OP = b"PING"
PONG_OP = b"PONG"
OK_OP = b"+OK"
ERR_OP = b"-ERR"
_CRLF_ = b"\r\n"
_SPC_ = b" "
_EMPTY_ = b""
EMPTY = ""

PING_PROTO = PING_OP + _CRLF_
PONG_PROTO = PONG_OP + _CRLF_
INBOX_PREFIX = bytearray(b"_INBOX.")
INBOX_PREFIX_LEN = len(INBOX_PREFIX) + 22 + 1

DEFAULT_PENDING_SIZE = 1024 * 1024
DEFAULT_BUFFER_SIZE = 32768
DEFAULT_RECONNECT_TIME_WAIT = 2  # in seconds
DEFAULT_MAX_RECONNECT_ATTEMPTS = 60
DEFAULT_PING_INTERVAL = 120  # in seconds
DEFAULT_MAX_OUTSTANDING_PINGS = 2
DEFAULT_MAX_PAYLOAD_SIZE = 1048576
DEFAULT_MAX_FLUSHER_QUEUE_SIZE = 1024
DEFAULT_CONNECT_TIMEOUT = 2  # in seconds
DEFAULT_DRAIN_TIMEOUT = 30  # in seconds
MAX_CONTROL_LINE_SIZE = 1024

# Default Pending Limits of Subscriptions
DEFAULT_SUB_PENDING_MSGS_LIMIT = 65536
DEFAULT_SUB_PENDING_BYTES_LIMIT = 65536 * 1024

NATS_HDR_LINE = bytearray(b"NATS/1.0\r\n")
NO_RESPONDERS_STATUS = "503"
STATUS_MSG_LEN = 3  # e.g. 20x, 40x, 50x
CTRL_LEN = len(_CRLF_)
STATUS_HDR = "Status"
DESC_HDR = "Description"


class Subscription:
    """
    A subscription represents interest in a particular subject.

    A subscription should not be constructed directly, rather
    `connection.subscribe()` should be used to get a subscription.
    """

    def __init__(
        self,
        conn: "Client",
        id: int = 0,
        subject: str = "",
        queue: str = "",
        cb: Optional[Callable[["Msg"], Awaitable[None]]] = None,
        future: Optional['asyncio.Future["Msg"]'] = None,
        max_msgs: int = 0,
        pending_msgs_limit: int = DEFAULT_SUB_PENDING_MSGS_LIMIT,
        pending_bytes_limit: int = DEFAULT_SUB_PENDING_BYTES_LIMIT,
    ) -> None:
        self._conn = conn
        self._id = id
        self._subject = subject
        self._queue = queue
        self._max_msgs = max_msgs
        self._received = 0
        self._cb = cb
        self._future = future

        # Per subscription message processor.
        self._pending_msgs_limit = pending_msgs_limit
        self._pending_bytes_limit = pending_bytes_limit
        self._pending_queue: asyncio.Queue[Msg] = asyncio.Queue(
            maxsize=pending_msgs_limit
        )
        self._pending_size = 0
        self._wait_for_msgs_task: Optional[Task[None]] = None
        self._message_iterator: Optional[_SubscriptionMessageIterator] = None

    @property
    def messages(self) -> AsyncIterator["Msg"]:
        """
        Retrieves an async iterator for the messages from the subscription.

        This is only available if a callback isn't provided when creating a
        subscription.
        """
        if not self._message_iterator:
            raise NatsError(
                "cannot iterate over messages with a non iteration subscription type"
            )

        return self._message_iterator

    async def next_msg(self, timeout: Optional[float] = 1.0) -> "Msg":
        """
        next_msg can be used to retrieve the next message
        from a stream of messages using await syntax.
        """
        future: Future[Msg] = asyncio.Future()

        async def _next_msg() -> None:
            msg = await self._pending_queue.get()
            future.set_result(msg)

        task = asyncio.create_task(_next_msg())
        try:
            msg = await asyncio.wait_for(future, timeout)
            return msg
        except asyncio.TimeoutError:
            future.cancel()
            task.cancel()
            raise ErrTimeout

    def _start(self, error_cb: Callable[[Exception], Awaitable[None]]) -> None:
        """
        Creates the resources for the subscription to start processing messages.
        """
        if self._cb:
            if not asyncio.iscoroutinefunction(self._cb) and not (
                hasattr(self._cb, "func") and asyncio.iscoroutinefunction(self._cb.func)
            ):  # type: ignore[attr-defined]
                raise NatsError("nats: must use coroutine for subscriptions")

            self._wait_for_msgs_task = asyncio.create_task(
                self._wait_for_msgs(error_cb)
            )

        elif self._future:
            # Used to handle the single response from a request.
            pass
        else:
            self._message_iterator = _SubscriptionMessageIterator(self._pending_queue)

    async def drain(self) -> None:
        """
        Removes interest in a subject, but will process remaining messages.
        """
        try:
            # Announce server that no longer want to receive more
            # messages in this sub and just process the ones remaining.
            await self._conn._send_unsubscribe(self._id)

            # Roundtrip to ensure that the server has sent all messages.
            await self._conn.flush()

            if self._pending_queue:
                # Wait until no more messages are left,
                # then cancel the subscription task.
                await self._pending_queue.join()

            # stop waiting for messages
            self._stop_processing()

            # Subscription is done and won't be receiving further
            # messages so can throw it away now.
            self._conn._remove_sub(self._id)
        except asyncio.CancelledError:
            # In case draining of a connection times out then
            # the sub per task will be canceled as well.
            pass

    async def unsubscribe(self, limit: int = 0) -> None:
        """
        Removes interest in a subject, remaining messages will be discarded.

        If `limit` is greater than zero, interest is not immediately removed,
        rather, interest will be automatically removed after `limit` messages
        are received.
        """
        if self._conn.is_closed:
            raise ErrConnectionClosed
        if self._conn.is_draining:
            raise ErrConnectionDraining

        self._max_msgs = limit
        if limit == 0 or self._received >= limit:
            self._stop_processing()
            self._conn._remove_sub(self._id)

        if not self._conn.is_reconnecting:
            await self._conn._send_unsubscribe(self._id, limit=limit)

    def _stop_processing(self):
        """
        Stops the subscription from processing new messages.
        """
        if self._wait_for_msgs_task and not self._wait_for_msgs_task.done():
            self._wait_for_msgs_task.cancel()
        if self._message_iterator:
            self._message_iterator._cancel()

    async def _wait_for_msgs(self, error_cb: Callable[[Exception], Awaitable[None]]):
        """
        A coroutine to read and process messages if a callback is provided.

        Should be called as a task.
        """
        while True:
            try:
                msg = await self._pending_queue.get()
                self._pending_size -= len(msg.data)

                try:
                    # Invoke depending of type of handler.
                    await self._cb(msg)  # type: ignore[misc]
                except asyncio.CancelledError:
                    # In case the coroutine handler gets cancelled
                    # then stop task loop and return.
                    break
                except Exception as e:
                    # All errors from calling a handler
                    # are async errors.
                    if error_cb:
                        await error_cb(e)
                finally:
                    # indicate the message finished processing so drain can continue
                    self._pending_queue.task_done()

            except asyncio.CancelledError:
                break


class _SubscriptionMessageIterator:
    def __init__(self, queue) -> None:
        self._queue: asyncio.Queue["Msg"] = queue
        self._unsubscribed_future: Future[bool] = asyncio.Future()

    def _cancel(self) -> None:
        if not self._unsubscribed_future.done():
            self._unsubscribed_future.set_result(True)

    def __aiter__(self) -> "_SubscriptionMessageIterator":
        return self

    async def __anext__(self) -> "Msg":
        get_task = asyncio.create_task(self._queue.get())
        finished, _ = await asyncio.wait(
            [get_task, self._unsubscribed_future],  # type: ignore[type-var]
            return_when=asyncio.FIRST_COMPLETED,
        )
        if get_task in finished:
            self._queue.task_done()
            return get_task.result()
        elif self._unsubscribed_future.done():
            get_task.cancel()

        raise StopAsyncIteration


class Msg:
    """
    Msg represents a message delivered by NATS.
    """

    __slots__ = ("subject", "reply", "data", "sid", "_client", "headers")

    def __init__(
        self,
        subject: str = "",
        reply: str = "",
        data: bytes = b"",
        sid: int = 0,
        client: Optional["Client"] = None,
        headers: Dict[str, str] = None,
    ) -> None:
        self.subject = subject
        self.reply = reply
        self.data = data
        self.sid = sid
        self._client = client
        self.headers = headers

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: subject='{self.subject}' reply='{self.reply}' data='{self.data[:10].decode()}...'>"

    async def respond(self, data: bytes) -> None:
        if not self.reply:
            raise NatsError("no reply subject available")
        if not self._client:
            raise NatsError("client not set")

        await self._client.publish(self.reply, data, headers=self.headers)


class Srv:
    """
    Srv is a helper data structure to hold state of a server.
    """

    def __init__(self, uri: ParseResult) -> None:
        self.uri = uri
        self.reconnects = 0
        self.did_connect = False
        self.discovered = False
        self.last_attempt: Optional[float] = None
        self.tls_name: Optional[str] = None


async def _default_error_callback(ex: BaseException) -> None:
    """
    Provides a default way to handle async errors if the user
    does not provide one.
    """
    _logger.error("nats: encountered error", exc_info=ex)


class Client:
    """
    Asyncio based client for NATS.
    """

    msg_class = Msg

    DISCONNECTED = 0
    CONNECTED = 1
    CLOSED = 2
    RECONNECTING = 3
    CONNECTING = 4
    DRAINING_SUBS = 5
    DRAINING_PUBS = 6

    def __repr__(self) -> str:
        return f"<nats client v{__version__}>"

    def __init__(self) -> None:
        self._current_server: Optional[Srv] = None
        self._server_info: ServerInfos = {}
        self._server_pool: List[Srv] = []
        self._reading_task: Optional[Task[None]] = None
        self._ping_interval_task: Optional[Task[None]] = None
        self._pings_outstanding = 0
        self._pongs_received = 0
        self._pongs: List[Future[bool]] = []
        self._bare_io_reader: Optional[StreamReader] = None
        self._io_reader: Optional[StreamReader] = None
        self._bare_io_writer: Optional[StreamWriter] = None
        self._io_writer: Optional[StreamWriter] = None
        self._err: Optional[Exception] = None
        self._error_cb: Optional[Callable[[Exception], Awaitable[None]]] = None
        self._disconnected_cb: Optional[Callable[[], Awaitable[None]]] = None
        self._closed_cb: Optional[Callable[[], Awaitable[None]]] = None
        self._discovered_server_cb: Optional[Callable[[], None]] = None
        self._reconnected_cb: Optional[Callable[[], Awaitable[None]]] = None
        self._reconnection_task: Optional[Task[None]] = None
        self._reconnection_task_future: Optional[Future[bool]] = None
        self._max_payload = DEFAULT_MAX_PAYLOAD_SIZE
        # This is the client id that the NATS server knows
        # about. Useful in debugging application errors
        # when logged with this identifier along
        # with nats server log.
        # This would make more sense if we log the server
        # connected to as well in case of cluster setup.
        self._client_id: Optional[int] = None
        self._sid = 0
        self._subs: Dict[int, Subscription] = {}
        self._status = Client.DISCONNECTED
        self._ps = Parser(self)
        self._pending: List[bytes] = []
        self._pending_data_size = 0
        self._flush_queue: Optional[asyncio.Queue[None]] = None
        self._flusher_task: Optional[Task[None]] = None
        self._hdr_parser = BytesParser()

        # New style request/response
        self._resp_map: Dict[str, Future[Msg]] = {}
        self._resp_sub_prefix: Optional[bytearray] = None
        self._nuid = NUID()

        # NKEYS support
        #
        # user_jwt_cb is used to fetch and return the account
        # signed JWT for this user.
        self._user_jwt_cb: Optional[Callable[[], bytes]] = None

        # signature_cb is used to sign a nonce from the server while
        # authenticating with nkeys. The user should sign the nonce and
        # return the base64 encoded signature.
        self._signature_cb: Optional[Callable[[str], bytes]] = None

        # user credentials file can be a tuple or single file.
        self._user_credentials: Union[None, str, Tuple[str, str]] = None

        # file that contains the nkeys seed and its public key as a string.
        self._nkeys_seed: Optional[str] = None
        self._public_nkey: Optional[str] = None

        self.options: Dict[str, Any] = {}
        self.stats: ClientStats = {
            "in_msgs": 0,
            "out_msgs": 0,
            "in_bytes": 0,
            "out_bytes": 0,
            "reconnects": 0,
            "errors_received": 0,
        }

    async def connect(
        self,
        servers: List[str] = ["nats://127.0.0.1:4222"],
        error_cb: Optional[Callable[[Exception], Awaitable[None]]] = None,
        disconnected_cb: Optional[Callable[[], Awaitable[None]]] = None,
        closed_cb: Optional[Callable[[], Awaitable[None]]] = None,
        discovered_server_cb: Optional[Callable[[], None]] = None,
        reconnected_cb: Optional[Callable[[], Awaitable[None]]] = None,
        name: Optional[str] = None,
        pedantic: bool = False,
        verbose: bool = False,
        allow_reconnect: bool = True,
        connect_timeout: int = DEFAULT_CONNECT_TIMEOUT,
        reconnect_time_wait: int = DEFAULT_RECONNECT_TIME_WAIT,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        ping_interval: int = DEFAULT_PING_INTERVAL,
        max_outstanding_pings: int = DEFAULT_MAX_OUTSTANDING_PINGS,
        dont_randomize: bool = False,
        flusher_queue_size: int = DEFAULT_MAX_FLUSHER_QUEUE_SIZE,
        pending_size: int = DEFAULT_PENDING_SIZE,
        no_echo: bool = False,
        tls: Optional[ssl.SSLContext] = None,
        tls_hostname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        drain_timeout: int = DEFAULT_DRAIN_TIMEOUT,
        signature_cb=None,
        user_jwt_cb: Optional[Callable[[], bytes]] = None,
        user_credentials: Optional[Union[str, Tuple[str, str]]] = None,
        nkeys_seed: Optional[str] = None,
    ) -> None:
        for cb in [
            error_cb,
            disconnected_cb,
            closed_cb,
            reconnected_cb,
            discovered_server_cb,
        ]:
            if cb and not asyncio.iscoroutinefunction(cb):
                raise ErrInvalidCallbackType()

        self._setup_server_pool(servers)
        self._error_cb = error_cb or _default_error_callback
        self._closed_cb = closed_cb
        self._discovered_server_cb = discovered_server_cb
        self._reconnected_cb = reconnected_cb
        self._disconnected_cb = disconnected_cb

        # NKEYS support
        self._signature_cb = signature_cb
        self._user_jwt_cb = user_jwt_cb
        self._user_credentials = user_credentials
        self._nkeys_seed = nkeys_seed

        # Customizable options
        self.options["verbose"] = verbose
        self.options["pedantic"] = pedantic
        self.options["name"] = name
        self.options["allow_reconnect"] = allow_reconnect
        self.options["dont_randomize"] = dont_randomize
        self.options["reconnect_time_wait"] = reconnect_time_wait
        self.options["max_reconnect_attempts"] = max_reconnect_attempts
        self.options["ping_interval"] = ping_interval
        self.options["max_outstanding_pings"] = max_outstanding_pings
        self.options["no_echo"] = no_echo
        self.options["user"] = user
        self.options["password"] = password
        self.options["token"] = token
        self.options["connect_timeout"] = connect_timeout
        self.options["drain_timeout"] = drain_timeout
        self.options["pending_size"] = pending_size

        if tls:
            self.options["tls"] = tls
        if tls_hostname:
            self.options["tls_hostname"] = tls_hostname

        if self._user_credentials is not None or self._nkeys_seed is not None:
            self._setup_nkeys_connect()

        # Queue used to trigger flushes to the socket
        self._flush_queue = asyncio.Queue(maxsize=flusher_queue_size)

        if self.options["dont_randomize"] is False:
            shuffle(self._server_pool)

        while True:
            try:
                await self._select_next_server()
                await self._process_connect_init()
                self._current_server.reconnects = 0  # type: ignore[union-attr]
                break
            except ErrNoServers as e:
                if self.options["max_reconnect_attempts"] < 0:
                    # Never stop reconnecting
                    continue
                self._err = e
                raise e
            except (OSError, NatsError, asyncio.TimeoutError) as e:
                self._err = e
                await self._error_cb(e)

                # Bail on first attempt if reconnecting is disallowed.
                if not self.options["allow_reconnect"]:
                    raise e

                await self._close(Client.DISCONNECTED, False)
                self._current_server.last_attempt = (
                    time.monotonic()  # type: ignore[union-attr]
                )
                self._current_server.reconnects += 1  # type: ignore[union-attr]

    async def close(self) -> None:
        """
        Closes the socket to which we are connected and
        sets the client to be in the CLOSED state.
        No further reconnections occur once reaching this point.
        """
        await self._close(Client.CLOSED)

    async def drain(self) -> None:
        """
        Drain will put a connection into a drain state. All subscriptions will
        immediately be put into a drain state. Upon completion, the publishers
        will be drained and can not publish any additional messages. Upon draining
        of the publishers, the connection will be closed. Use the `closed_cb'
        option to know when the connection has moved from draining to closed.
        """
        if self.is_draining:
            return
        if self.is_closed:
            raise ErrConnectionClosed
        if self.is_connecting or self.is_reconnecting:
            raise ErrConnectionReconnecting

        # Start draining the subscriptions
        self._status = Client.DRAINING_SUBS

        drain_tasks = []
        for sub in self._subs.values():
            coro = sub.drain()
            task = asyncio.create_task(coro)
            drain_tasks.append(task)

        drain_is_done = asyncio.gather(*drain_tasks)
        try:
            await asyncio.wait_for(drain_is_done, self.options["drain_timeout"])
        except asyncio.TimeoutError:
            drain_is_done.exception()
            drain_is_done.cancel()
            await self._error_cb(ErrDrainTimeout)  # type: ignore[arg-type, misc]
        except asyncio.CancelledError:
            pass
        finally:
            self._status = Client.DRAINING_PUBS
            await self.flush()
            await self._close(Client.CLOSED)

    async def flush(self, timeout: float = 60) -> None:
        """
        Sends a ping to the server expecting a pong back ensuring
        what we have written so far has made it to the server and
        also enabling measuring of roundtrip time.
        In case a pong is not returned within the allowed timeout,
        then it will raise ErrTimeout.
        """
        if timeout <= 0:
            raise ErrBadTimeout

        if self.is_closed:
            raise ErrConnectionClosed

        future: Future[bool] = asyncio.Future()
        try:
            await self._send_ping(future)
            await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            future.cancel()
            raise ErrTimeout

    async def publish(
        self,
        subject: str,
        payload: bytes = b"",
        reply: str = "",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Sends a PUB command to the server on the specified subject.
        A reply can be used by the recipient to respond to the message.

          ->> PUB hello <reply> 5
          ->> MSG_PAYLOAD: world
          <<- MSG hello 2 5

        """
        if self.is_closed:
            raise ErrConnectionClosed
        if self.is_draining_pubs:
            raise ErrConnectionDraining

        payload_size = len(payload)
        if payload_size > self._max_payload:
            raise ErrMaxPayload
        await self._send_publish(subject, reply, payload, payload_size, headers)

    async def publish_request(
        self,
        subject: str,
        reply: str,
        payload: bytes,
    ) -> None:
        """Deprecated. Will be removed in incoming versions.

        Use Client.publish if you want to use headers parameter.
        """
        warnings.warn(
            "publish_request method from _nats.aio.client.Client is deprecated. "
            "Use Client.publish(subject, payload, reply, headers) instead."
        )
        await self.publish(subject, payload, reply, None)

    async def request(
        self,
        subject: str,
        payload: bytes = b"",
        timeout: float = 0.5,
        old_style: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> Msg:
        """
        Implements the request/response pattern via pub/sub
        using a single wildcard subscription that handles
        the responses.

        """
        if old_style:
            return await self._request_old_style(subject, payload, timeout=timeout)
        return await self._request_new_style(
            subject, payload, timeout=timeout, headers=headers
        )

    async def subscribe(
        self,
        subject: str,
        queue: str = "",
        cb: Optional[Callable[[Msg], Awaitable[None]]] = None,
        future: Optional[asyncio.Future] = None,
        max_msgs: int = 0,
        pending_msgs_limit: int = DEFAULT_SUB_PENDING_MSGS_LIMIT,
        pending_bytes_limit: int = DEFAULT_SUB_PENDING_BYTES_LIMIT,
    ) -> Subscription:
        """
        Expresses interest in a given subject.

        A `Subscription` object will be returned.
        If a callback is provided, messages will be processed asychronously.
        If a callback isn't provided, messages can be retrieved via an
        asynchronous iterator on the returned subscription object.
        """
        if not subject:
            raise ErrBadSubject

        if self.is_closed:
            raise ErrConnectionClosed

        if self.is_draining:
            raise ErrConnectionDraining

        self._sid += 1
        sid = self._sid

        sub = Subscription(
            self,
            sid,
            subject,
            queue=queue,
            cb=cb,
            future=future,
            max_msgs=max_msgs,
            pending_msgs_limit=pending_msgs_limit,
            pending_bytes_limit=pending_bytes_limit,
        )

        sub._start(self._error_cb)  # type: ignore[arg-type]
        self._subs[sid] = sub
        await self._send_subscribe(sub)
        return sub

    @property
    def connected_url(self) -> Optional[str]:
        if self.is_connected:
            return str(self._current_server.uri)  # type: ignore[union-attr]
        else:
            return None

    @property
    def servers(self) -> List[Srv]:
        servers = []
        for srv in self._server_pool:
            servers.append(srv)
        return servers

    @property
    def discovered_servers(self) -> List[Srv]:
        servers = []
        for srv in self._server_pool:
            if srv.discovered:
                servers.append(srv)
        return servers

    @property
    def max_payload(self) -> Optional[int]:
        """
        Returns the max payload which we received from the servers INFO
        """
        return self._max_payload  # type: ignore[no-any-return]

    @property
    def client_id(self) -> Optional[int]:
        """
        Returns the client id which we received from the servers INFO
        """
        return self._client_id  # type: ignore[no-any-return]

    @property
    def last_error(self) -> Optional[Exception]:
        """
        Returns the last error which may have occured.
        """
        return self._err  # type: ignore[no-any-return]

    @property
    def pending_data_size(self) -> int:
        return self._pending_data_size  # type: ignore[no-any-return]

    @property
    def is_closed(self) -> bool:
        return self._status == Client.CLOSED  # type: ignore[no-any-return]

    @property
    def is_reconnecting(self) -> bool:
        return self._status == Client.RECONNECTING  # type: ignore[no-any-return]

    @property
    def is_connected(self) -> bool:
        return (self._status == Client.CONNECTED) or self.is_draining

    @property
    def is_connecting(self) -> bool:
        return self._status == Client.CONNECTING  # type: ignore[no-any-return]

    @property
    def is_draining(self) -> bool:
        return (  # type: ignore[no-any-return]
            self._status == Client.DRAINING_SUBS or self._status == Client.DRAINING_PUBS
        )

    @property
    def is_draining_pubs(self) -> bool:
        return self._status == Client.DRAINING_PUBS  # type: ignore[no-any-return]

    def _build_message(
        self,
        subject: bytes,
        reply: bytes,
        data: bytes,
        headers: Optional[Dict[str, str]],
    ) -> "Msg":
        return self.msg_class(
            subject=subject.decode(),
            reply=reply.decode(),
            data=data,
            headers=headers,
            client=self,
        )

    def _connect_command(self) -> bytes:
        """
        Generates a JSON string with the params to be used
        when sending CONNECT to the server.

          ->> CONNECT {"lang": "python3"}

        """
        options = {
            "verbose": self.options["verbose"],
            "pedantic": self.options["pedantic"],
            "lang": __lang__,
            "version": __version__,
            "protocol": PROTOCOL,
        }
        if "headers" in self._server_info:
            options["headers"] = self._server_info["headers"]
            options["no_responders"] = self._server_info["headers"]

        if "auth_required" in self._server_info:
            if self._server_info["auth_required"]:
                if "nonce" in self._server_info and self._signature_cb is not None:
                    sig = self._signature_cb(self._server_info["nonce"])
                    options["sig"] = sig.decode()

                    if self._user_jwt_cb is not None:
                        jwt = self._user_jwt_cb()
                        options["jwt"] = jwt.decode()
                    elif self._public_nkey is not None:
                        options["nkey"] = self._public_nkey
                # In case there is no password, then consider handle
                # sending a token instead.
                elif (
                    self.options["user"] is not None
                    and self.options["password"] is not None
                ):
                    options["user"] = self.options["user"]
                    options["pass"] = self.options["password"]
                elif self.options["token"] is not None:
                    options["auth_token"] = self.options["token"]
                elif self._current_server.uri.username is not None:  # type: ignore[union-attr]
                    if self._current_server.uri.password is None:  # type: ignore[union-attr]
                        options[
                            "auth_token"
                        ] = self._current_server.uri.username  # type: ignore[union-attr]
                    else:
                        options[
                            "user"
                        ] = self._current_server.uri.username  # type: ignore[union-attr]
                        options[
                            "pass"
                        ] = self._current_server.uri.password  # type: ignore[union-attr]

        if self.options["name"] is not None:
            options["name"] = self.options["name"]
        if self.options["no_echo"] is not None:
            options["echo"] = not self.options["no_echo"]

        connect_opts = json.dumps(options, sort_keys=True)
        return b"".join([CONNECT_OP + _SPC_ + connect_opts.encode() + _CRLF_])

    def _host_is_ip(self, connect_url: Optional[str]) -> bool:
        try:
            ipaddress.ip_address(connect_url)
            return True
        except:
            return False

    def _parse_headers(self, headers: Optional[bytes]) -> Dict[str, str]:
        hdrs: Dict[str, str] = {}
        if headers is None:
            return hdrs
        raw_headers = headers[len(NATS_HDR_LINE) :]
        parsed_hdrs = self._hdr_parser.parsebytes(raw_headers)
        # Check if it is an inline status message like:
        #
        # NATS/1.0 404 No Messages
        #
        if len(parsed_hdrs.items()) == 0:
            l = headers[len(NATS_HDR_LINE) - 1 :]
            status = l[:STATUS_MSG_LEN]
            desc = l[STATUS_MSG_LEN + 1 : len(l) - CTRL_LEN - CTRL_LEN]
            hdrs[STATUS_HDR] = status.decode()
            hdrs[DESC_HDR] = desc.decode()
        else:
            for k, v in parsed_hdrs.items():
                hdrs[k] = v

        return hdrs

    def _process_disconnect(self) -> None:
        """
        Process disconnection from the server and set client status
        to DISCONNECTED.
        """
        self._status = Client.DISCONNECTED

    def _process_info(
        self, info: ServerInfos, initial_connection: bool = False
    ) -> None:
        """
        Process INFO lines sent by the server to reconfigure client
        with latest updates from cluster to enable server discovery.
        """
        if "connect_urls" in info:
            if info["connect_urls"]:
                connect_urls = []
                for connect_url in info["connect_urls"]:
                    scheme = ""
                    if self._current_server.uri.scheme == "tls":  # type: ignore[union-attr]
                        scheme = "tls"
                    else:
                        scheme = "nats"

                    uri = urlparse(f"{scheme}://{connect_url}")
                    srv = Srv(uri)
                    srv.discovered = True

                    # Check whether we should reuse the original hostname.
                    if (
                        "tls_required" in self._server_info
                        and self._server_info["tls_required"]
                        and self._host_is_ip(uri.hostname)
                    ):
                        srv.tls_name = self._current_server.uri.hostname  # type: ignore[union-attr]

                    # Filter for any similar server in the server pool already.
                    should_add = True
                    for s in self._server_pool:
                        if uri.netloc == s.uri.netloc:
                            should_add = False
                    if should_add:
                        connect_urls.append(srv)

                if self.options["dont_randomize"] is not True:
                    shuffle(connect_urls)
                for srv in connect_urls:
                    self._server_pool.append(srv)

                if (
                    not initial_connection
                    and connect_urls
                    and self._discovered_server_cb
                ):
                    self._discovered_server_cb()

    def _remove_sub(self, sid: int) -> None:
        self._subs.pop(sid, None)

    def _setup_nkeys_connect(self) -> None:
        if self._user_credentials is not None:
            self._setup_nkeys_jwt_connect()
        else:
            self._setup_nkeys_seed_connect()

    def _setup_nkeys_jwt_connect(self) -> None:
        import nkeys
        import os

        creds = self._user_credentials
        if isinstance(creds, tuple) and len(creds) > 1:

            def user_cb():
                contents = None
                with open(creds[0], "rb") as f:
                    contents = bytearray(os.fstat(f.fileno()).st_size)
                    f.readinto(contents)
                return contents

            self._user_jwt_cb = user_cb

            def sig_cb(nonce):
                seed = None
                with open(creds[1], "rb") as f:
                    seed = bytearray(os.fstat(f.fileno()).st_size)
                    f.readinto(seed)
                kp = nkeys.from_seed(seed)
                raw_signed = kp.sign(nonce.encode())
                sig = base64.b64encode(raw_signed)

                # Best effort attempt to clear from memory.
                kp.wipe()
                del kp
                del seed
                return sig

            self._signature_cb = sig_cb
        else:
            # Define the functions to be able to sign things using nkeys.
            def user_cb():
                user_jwt = None
                with open(creds, "rb") as f:
                    while True:
                        line = bytearray(f.readline())
                        if b"BEGIN NATS USER JWT" in line:
                            user_jwt = bytearray(f.readline())
                            break
                # Remove trailing line break but reusing same memory view.
                return user_jwt[: len(user_jwt) - 1]

            self._user_jwt_cb = user_cb

            def sig_cb(nonce):
                user_seed = None
                with open(creds, "rb", buffering=0) as f:
                    for line in f:
                        # Detect line where the NKEY would start and end,
                        # then seek and read into a fixed bytearray that
                        # can be wiped.
                        if b"BEGIN USER NKEY SEED" in line:
                            nkey_start_pos = f.tell()
                            try:
                                next(f)
                            except StopIteration:
                                raise ErrInvalidUserCredentials()
                            nkey_end_pos = f.tell()
                            nkey_size = nkey_end_pos - nkey_start_pos - 1
                            f.seek(nkey_start_pos)

                            # Only gather enough bytes for the user seed
                            # into the pre allocated bytearray.
                            user_seed = bytearray(nkey_size)
                            f.readinto(user_seed)
                kp = nkeys.from_seed(user_seed)
                raw_signed = kp.sign(nonce.encode())
                sig = base64.b64encode(raw_signed)

                # Delete all state related to the keys.
                kp.wipe()
                del user_seed
                del kp
                return sig

            self._signature_cb = sig_cb

    def _setup_nkeys_seed_connect(self) -> None:
        import nkeys
        import os

        seed = None
        creds: str = self._nkeys_seed  # type: ignore[assignment]
        with open(creds, "rb") as f:
            seed = bytearray(os.fstat(f.fileno()).st_size)
            f.readinto(seed)  # type: ignore[attr-defined]
        kp = nkeys.from_seed(seed)
        self._public_nkey = kp.public_key.decode()
        kp.wipe()
        del kp
        del seed

        def sig_cb(nonce: str) -> bytes:
            seed = None
            with open(creds, "rb") as f:
                seed = bytearray(os.fstat(f.fileno()).st_size)
                f.readinto(seed)  # type: ignore[attr-defined]
            kp = nkeys.from_seed(seed)
            raw_signed = kp.sign(nonce.encode())
            sig = base64.b64encode(raw_signed)

            # Best effort attempt to clear from memory.
            kp.wipe()
            del kp
            del seed
            return sig

        self._signature_cb = sig_cb

    def _setup_server_pool(self, connect_url: Union[str, List[str]]) -> None:
        if type(connect_url) is str:
            try:
                if "nats://" in connect_url or "tls://" in connect_url:
                    # Closer to how the Go client handles this.
                    # e.g. nats://127.0.0.1:4222
                    uri = urlparse(connect_url)
                elif ":" in connect_url:
                    # Expand the scheme for the user
                    # e.g. 127.0.0.1:4222
                    uri = urlparse(f"nats://{connect_url}")
                else:
                    # Just use the endpoint with the default NATS port.
                    # e.g. demo.nats.io
                    uri = urlparse(f"nats://{connect_url}:4222")

                # In case only endpoint with scheme was set.
                # e.g. nats://demo.nats.io or localhost:
                if uri.port is None:
                    uri = urlparse(f"nats://{uri.hostname}:4222")
            except ValueError:
                raise NatsError("nats: invalid connect url option")

            if uri.hostname is None or uri.hostname == "none":
                raise NatsError("nats: invalid hostname in connect url")
            self._server_pool.append(Srv(uri))
        elif type(connect_url) is list:
            try:
                for server in connect_url:
                    uri = urlparse(server)
                    self._server_pool.append(Srv(uri))
            except ValueError:
                raise NatsError("nats: invalid connect url option")
        else:
            raise NatsError("nats: invalid connect url option")

    async def _attempt_reconnect(self) -> None:
        if self._reading_task is not None and not self._reading_task.cancelled():
            self._reading_task.cancel()

        if (
            self._ping_interval_task is not None
            and not self._ping_interval_task.cancelled()
        ):
            self._ping_interval_task.cancel()

        if self._flusher_task is not None and not self._flusher_task.cancelled():
            self._flusher_task.cancel()

        if self._io_writer is not None:
            self._io_writer.close()
            try:
                await self._io_writer.wait_closed()
            except Exception as e:
                await self._error_cb(e)  # type: ignore[misc]

        self._err = None
        if self._disconnected_cb is not None:
            await self._disconnected_cb()

        if self.is_closed:
            return

        if "dont_randomize" not in self.options or not self.options["dont_randomize"]:
            shuffle(self._server_pool)

        # Create a future that the client can use to control waiting
        # on the reconnection attempts.
        self._reconnection_task_future = asyncio.Future()
        while True:
            try:
                # Try to establish a TCP connection to a server in
                # the cluster then send CONNECT command to it.
                await self._select_next_server()
                await self._process_connect_init()

                # Consider a reconnect to be done once CONNECT was
                # processed by the server successfully.
                self.stats["reconnects"] += 1

                # Reset reconnect attempts for this server
                # since have successfully connected.
                self._current_server.did_connect = True  # type: ignore[union-attr]
                self._current_server.reconnects = 0  # type: ignore[union-attr]

                # Replay all the subscriptions in case there were some.
                subs_to_remove = []
                for sid, sub in self._subs.items():
                    max_msgs = 0
                    if sub._max_msgs > 0:
                        # If we already hit the message limit, remove the subscription and don't resubscribe
                        if sub._received >= sub._max_msgs:
                            subs_to_remove.append(sid)
                            continue
                        # auto unsubscribe the number of messages we have left
                        max_msgs = sub._max_msgs - sub._received

                    sub_cmd = prot_command.sub_cmd(sub._subject, sub._queue, sid)
                    self._io_writer.write(sub_cmd)  # type: ignore[union-attr]

                    if max_msgs > 0:
                        unsub_cmd = prot_command.unsub_cmd(sid, max_msgs)
                        self._io_writer.write(unsub_cmd)  # type: ignore[union-attr]

                for sid in subs_to_remove:
                    self._subs.pop(sid)

                await self._io_writer.drain()  # type: ignore[union-attr]

                # Flush pending data before continuing in connected status.
                # FIXME: Could use future here and wait for an error result
                # to bail earlier in case there are errors in the connection.
                await self._flush_pending()
                self._status = Client.CONNECTED
                await self.flush()
                if self._reconnected_cb is not None:
                    await self._reconnected_cb()
                self._reconnection_task_future = None
                break
            except ErrNoServers as e:
                self._err = e
                await self.close()
                break
            except (OSError, NatsError, asyncio.TimeoutError) as e:
                self._err = e
                await self._error_cb(e)  # type: ignore[misc]
                self._status = Client.RECONNECTING
                self._current_server.last_attempt = (
                    time.monotonic()  # type: ignore[union-attr]
                )
                self._current_server.reconnects += 1  # type: ignore[union-attr]
            except asyncio.CancelledError:
                break

        if (
            self._reconnection_task_future is not None
            and not self._reconnection_task_future.cancelled()
        ):
            self._reconnection_task_future.set_result(True)

    async def _close(self, status: int, do_cbs: bool = True) -> None:
        if self.is_closed:
            self._status = status
            return
        self._status = Client.CLOSED

        # Kick the flusher once again so it breaks
        # and avoid pending futures.
        await self._flush_pending()

        if self._reading_task is not None and not self._reading_task.cancelled():
            self._reading_task.cancel()

        if (
            self._ping_interval_task is not None
            and not self._ping_interval_task.cancelled()
        ):
            self._ping_interval_task.cancel()

        if self._flusher_task is not None and not self._flusher_task.cancelled():
            self._flusher_task.cancel()

        if self._reconnection_task is not None and not self._reconnection_task.done():
            self._reconnection_task.cancel()

            # Wait for the reconection task to be done which should be soon.
            try:
                if (
                    self._reconnection_task_future is not None
                    and not self._reconnection_task_future.cancelled()
                ):
                    await asyncio.wait_for(
                        self._reconnection_task_future,
                        self.options["reconnect_time_wait"],
                    )
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        # Relinquish control to allow background tasks to wrap up.
        await asyncio.sleep(0)

        if self._current_server is not None:
            # In case there is any pending data at this point, flush before disconnecting.
            if self._pending_data_size > 0:
                self._io_writer.writelines(self._pending[:])  # type: ignore[union-attr]
                self._pending = []
                self._pending_data_size = 0
                await self._io_writer.drain()  # type: ignore[union-attr]

        # Cleanup subscriptions since not reconnecting so no need
        # to replay the subscriptions anymore.
        for sub in self._subs.values():
            # FIXME: Should we clear the pending queue here?
            if sub._wait_for_msgs_task and not sub._wait_for_msgs_task.done():
                sub._wait_for_msgs_task.cancel()
        self._subs.clear()

        if self._io_writer is not None:
            self._io_writer.close()
            try:
                await self._io_writer.wait_closed()
            except Exception as e:
                await self._error_cb(e)  # type: ignore[misc]

        if do_cbs:
            if self._disconnected_cb is not None:
                await self._disconnected_cb()
            if self._closed_cb is not None:
                await self._closed_cb()

        # Set the client_id back to None
        self._client_id = None

    async def _flusher(self) -> None:
        """
        Coroutine which continuously tries to consume pending commands
        and then flushes them to the socket.
        """
        while True:
            if not self.is_connected or self.is_connecting:
                break

            try:
                await self._flush_queue.get()  # type: ignore[union-attr]

                if self._pending_data_size > 0:
                    self._io_writer.writelines(  # type: ignore[union-attr]
                        self._pending[:]
                    )
                    self._pending = []
                    self._pending_data_size = 0
                    await self._io_writer.drain()  # type: ignore[union-attr]
            except OSError as e:
                await self._error_cb(e)  # type: ignore[misc]
                await self._process_op_err(e)
                break
            except asyncio.CancelledError:
                break

    async def _flush_pending(self) -> None:
        try:
            # kick the flusher!
            await self._flush_queue.put(None)  # type: ignore[union-attr]

            if not self.is_connected:
                return

        except asyncio.CancelledError:
            pass

    async def _init_request_sub(self) -> None:
        # TODO just initialize it this way
        self._resp_map = {}

        self._resp_sub_prefix = INBOX_PREFIX[:]
        self._resp_sub_prefix.extend(self._nuid.next())
        self._resp_sub_prefix.extend(b".")
        resp_mux_subject = self._resp_sub_prefix[:]
        resp_mux_subject.extend(b"*")
        await self.subscribe(resp_mux_subject.decode(), cb=self._request_sub_callback)

    async def _ping_interval(self) -> None:
        while True:
            await asyncio.sleep(self.options["ping_interval"])
            if not self.is_connected:
                continue
            try:
                self._pings_outstanding += 1
                if self._pings_outstanding > self.options["max_outstanding_pings"]:
                    await self._process_op_err(
                        ErrStaleConnection  # type: ignore[arg-type]
                    )
                    return
                await self._send_ping()
            except asyncio.CancelledError:
                break
            # except asyncio.InvalidStateError:
            #     pass

    async def _process_connect_init(self) -> None:
        """
        Process INFO received from the server and CONNECT to the server
        with authentication.  It is also responsible of setting up the
        reading and ping interval tasks from the client.
        """
        self._status = Client.CONNECTING

        connection_completed = self._io_reader.readline()  # type: ignore[union-attr]
        info_line = await asyncio.wait_for(
            connection_completed, self.options["connect_timeout"]
        )
        if INFO_OP not in info_line:
            raise NatsError(
                "nats: empty response from server when expecting INFO message"
            )

        _, info = info_line.split(INFO_OP + _SPC_, 1)

        try:
            srv_info: ServerInfos = json.loads(info.decode())
        except:
            raise NatsError("nats: info message, json parse error")

        self._server_info = srv_info
        self._process_info(srv_info, initial_connection=True)

        if "max_payload" in self._server_info:
            self._max_payload = self._server_info["max_payload"]

        if "client_id" in self._server_info:
            self._client_id = self._server_info["client_id"]

        if "tls_required" in self._server_info and self._server_info["tls_required"]:
            ssl_context = None
            if "tls" in self.options:
                ssl_context = self.options.get("tls")
            elif self._current_server.uri.scheme == "tls":  # type: ignore[union-attr]
                ssl_context = ssl.create_default_context()
            else:
                raise NatsError("nats: no ssl context provided")

            # Check whether to reuse the original hostname for an implicit route.
            hostname = None
            if "tls_hostname" in self.options:
                hostname = self.options["tls_hostname"]
            elif self._current_server.tls_name is not None:  # type: ignore[union-attr]
                hostname = self._current_server.tls_name  # type: ignore[union-attr]
            else:
                hostname = self._current_server.uri.hostname  # type: ignore[union-attr]

            # just in case something is left
            await self._io_writer.drain()  # type: ignore[union-attr]

            # loop.start_tls was introduced in python 3.7
            # the previous method is removed in 3.9
            if sys.version_info.minor >= 7:
                # manually recreate the stream reader/writer with a tls upgraded transport
                reader = asyncio.StreamReader()
                protocol = asyncio.StreamReaderProtocol(reader)
                transport_future = asyncio.get_event_loop().start_tls(
                    self._io_writer.transport,  # type: ignore[union-attr]
                    protocol,
                    ssl_context,  # type: ignore[arg-type]
                    server_hostname=hostname,
                )
                transport = await asyncio.wait_for(
                    transport_future, self.options["connect_timeout"]
                )
                writer = asyncio.StreamWriter(
                    transport, protocol, reader, asyncio.get_event_loop()
                )
                self._io_reader, self._io_writer = reader, writer
            else:
                transport = self._io_writer.transport  # type: ignore[union-attr]
                sock = transport.get_extra_info("socket")
                if not sock:
                    # This shouldn't happen
                    raise NatsError("nats: unable to get socket")

                connection_future = asyncio.open_connection(
                    limit=DEFAULT_BUFFER_SIZE,
                    sock=sock,
                    ssl=ssl_context,
                    server_hostname=hostname,
                )
                self._io_reader, self._io_writer = await asyncio.wait_for(
                    connection_future, self.options["connect_timeout"]
                )

        # Refresh state of parser upon reconnect.
        if self.is_reconnecting:
            self._ps.reset()

        connect_cmd = self._connect_command()
        self._io_writer.write(connect_cmd)  # type: ignore[union-attr]
        await self._io_writer.drain()  # type: ignore[union-attr]
        if self.options["verbose"]:
            future = self._io_reader.readline()  # type: ignore[union-attr]
            next_op = await asyncio.wait_for(future, self.options["connect_timeout"])
            if OK_OP in next_op:
                # Do nothing
                pass
            elif ERR_OP in next_op:
                err_line = next_op.decode()
                _, err_msg = err_line.split(" ", 1)

                # FIXME: Maybe handling could be more special here,
                # checking for ErrAuthorization for example.
                # await self._process_err(err_msg)
                raise NatsError("nats: " + err_msg.rstrip("\r\n"))

        self._io_writer.write(PING_PROTO)  # type: ignore[union-attr]
        await self._io_writer.drain()  # type: ignore[union-attr]

        future = self._io_reader.readline()  # type: ignore[union-attr]
        next_op = await asyncio.wait_for(future, self.options["connect_timeout"])

        if PONG_PROTO in next_op:
            self._status = Client.CONNECTED
        elif ERR_OP in next_op:
            err_line = next_op.decode()
            _, err_msg = err_line.split(" ", 1)

            # FIXME: Maybe handling could be more special here,
            # checking for ErrAuthorization for example.
            # await self._process_err(err_msg)
            raise NatsError("nats: " + err_msg.rstrip("\r\n"))

        if PONG_PROTO in next_op:
            self._status = Client.CONNECTED

        self._reading_task = asyncio.get_event_loop().create_task(self._read_loop())
        self._pongs = []
        self._pings_outstanding = 0
        self._ping_interval_task = asyncio.get_event_loop().create_task(
            self._ping_interval()
        )

        # Task for kicking the flusher queue
        self._flusher_task = asyncio.get_event_loop().create_task(self._flusher())

    async def _process_err(self, err_msg: Sequence[bytes]) -> None:
        """
        Processes the raw error message sent by the server
        and close connection with current server.
        """
        if STALE_CONNECTION in err_msg:
            await self._process_op_err(ErrStaleConnection)  # type: ignore[arg-type]
            return

        if AUTHORIZATION_VIOLATION in err_msg:
            self._err = ErrAuthorization  # type: ignore[assignment]
        else:
            m = b"nats: " + err_msg[0]
            err = NatsError(m.decode())
            self._err = err

            if PERMISSIONS_ERR in m:
                await self._error_cb(err)  # type: ignore[misc]
                return

        do_cbs = False
        if not self.is_connecting:
            do_cbs = True

        # FIXME: Some errors such as 'Invalid Subscription'
        # do not cause the server to close the connection.
        # For now we handle similar as other clients and close.
        asyncio.get_event_loop().create_task(self._close(Client.CLOSED, do_cbs))

    async def _process_msg(
        self,
        sid: int,
        subject: bytes,
        reply: bytes,
        data: bytes,
        headers: Optional[bytes],
    ) -> None:
        """
        Process MSG sent by server.
        """
        payload_size = len(data)
        self.stats["in_msgs"] += 1
        self.stats["in_bytes"] += payload_size

        sub = self._subs.get(sid)
        if not sub:
            # Skip in case no subscription present.
            return

        sub._received += 1
        if sub._max_msgs > 0 and sub._received >= sub._max_msgs:
            # Enough messages so can throwaway subscription now.
            self._subs.pop(sid, None)
            sub._stop_processing()

        try:
            hdrs = self._parse_headers(headers)
        except Exception as e:
            await self._error_cb(e)  # type: ignore[misc]
            return

        msg = self._build_message(subject, reply, data, hdrs)

        # Check if it is an old style request.
        if sub._future:
            if sub._future.cancelled():
                # Already gave up, nothing to do.
                return
            sub._future.set_result(msg)
            return

        # Let subscription wait_for_msgs coroutine process the messages,
        # but in case sending to the subscription task would block,
        # then consider it to be an slow consumer and drop the message.
        try:
            sub._pending_size += payload_size
            # allow setting pending_bytes_limit to 0 to disable
            if (
                sub._pending_bytes_limit > 0
                and sub._pending_size >= sub._pending_bytes_limit
            ):
                # Subtract the bytes since the message will be thrown away
                # so it would not be pending data.
                sub._pending_size -= payload_size

                await self._error_cb(
                    ErrSlowConsumer(subject=subject, sid=sid)
                )  # type: ignore[misc]
                return
            sub._pending_queue.put_nowait(msg)
        except asyncio.QueueFull:
            await self._error_cb(
                ErrSlowConsumer(subject=subject, sid=sid)
            )  # type: ignore[misc]

    async def _process_op_err(self, e: Exception) -> None:
        """
        Process errors which occured while reading or parsing
        the protocol. If allow_reconnect is enabled it will
        try to switch the server to which it is currently connected
        otherwise it will disconnect.
        """
        if self.is_connecting or self.is_closed or self.is_reconnecting:
            return

        if self.options["allow_reconnect"] and self.is_connected:
            self._status = Client.RECONNECTING
            self._ps.reset()

            if (
                self._reconnection_task is not None
                and not self._reconnection_task.cancelled()
            ):
                # Cancel the previous task in case it may still be running.
                self._reconnection_task.cancel()

            self._reconnection_task = asyncio.get_event_loop().create_task(
                self._attempt_reconnect()
            )
        else:
            self._process_disconnect()
            self._err = e
            await self._close(Client.CLOSED, True)

    async def _process_ping(self) -> None:
        """
        Process PING sent by server.
        """
        await self._send_command(PONG)
        await self._flush_pending()

    async def _process_pong(self) -> None:
        """
        Process PONG sent by server.
        """
        if len(self._pongs) > 0:
            future = self._pongs.pop(0)
            future.set_result(True)
            self._pongs_received += 1
            self._pings_outstanding = 0

    async def _read_loop(self) -> None:
        """
        Coroutine which gathers bytes sent by the server
        and feeds them to the protocol parser.
        In case of error while reading, it will stop running
        and its task has to be rescheduled.
        """
        while True:
            try:
                should_bail = self.is_closed or self.is_reconnecting
                if should_bail or self._io_reader is None:
                    break
                if self.is_connected and self._io_reader.at_eof():
                    await self._error_cb(
                        ErrStaleConnection  # type: ignore[misc, arg-type]
                    )
                    await self._process_op_err(
                        ErrStaleConnection  # type: ignore[arg-type]
                    )
                    break

                b = await self._io_reader.read(DEFAULT_BUFFER_SIZE)
                await self._ps.parse(b)
            except ErrProtocol:
                await self._process_op_err(ErrProtocol)  # type: ignore[arg-type]
                break
            except OSError as e:
                await self._process_op_err(e)
                break
            except asyncio.CancelledError:
                break
            # except asyncio.InvalidStateError:
            #     pass

    async def _request_new_style(
        self,
        subject: str,
        payload: bytes,
        timeout: float = 0.5,
        headers: Optional[Dict[str, str]] = None,
    ) -> Msg:
        if self.is_draining_pubs:
            raise ErrConnectionDraining

        if not self._resp_sub_prefix:
            await self._init_request_sub()

        # Use a new NUID for the token inbox and then use the future.
        token = self._nuid.next()
        inbox = self._resp_sub_prefix[:]  # type: ignore[index]
        inbox.extend(token)
        future: Future[Msg] = asyncio.Future()
        self._resp_map[token.decode()] = future
        await self.publish(subject, payload, reply=inbox.decode(), headers=headers)

        # Wait for the response or give up on timeout.
        try:
            msg = await asyncio.wait_for(future, timeout)
            return msg
        except asyncio.TimeoutError:
            self._resp_map.pop(token.decode())
            future.cancel()
            raise ErrTimeout

    async def _request_old_style(
        self, subject: str, payload: bytes, timeout: float = 0.5
    ) -> Msg:
        """
        Implements the request/response pattern via pub/sub
        using an ephemeral subscription which will be published
        with a limited interest of 1 reply returning the response
        or raising a Timeout error.
        """
        next_inbox = INBOX_PREFIX[:]
        next_inbox.extend(self._nuid.next())
        inbox = next_inbox.decode()

        future: Future[Msg] = asyncio.Future()
        sub = await self.subscribe(inbox, future=future, max_msgs=1)
        await sub.unsubscribe(limit=1)
        await self.publish(subject, payload, reply=inbox)

        try:
            msg = await asyncio.wait_for(future, timeout)
            return msg
        except asyncio.TimeoutError:
            await sub.unsubscribe()
            future.cancel()
            raise ErrTimeout

    async def _request_sub_callback(self, msg: Msg) -> None:
        token = msg.subject[INBOX_PREFIX_LEN:]
        try:
            fut = self._resp_map.get(token)
            if not fut:
                return
            fut.set_result(msg)
            self._resp_map.pop(token, None)
        except (asyncio.CancelledError, asyncio.InvalidStateError):
            # Request may have timed out already so remove the entry
            self._resp_map.pop(token, None)

    async def _select_next_server(self) -> None:
        """
        Looks up in the server pool for an available server
        and attempts to connect.
        """

        while True:
            if len(self._server_pool) == 0:
                self._current_server = None
                raise ErrNoServers

            now = time.monotonic()
            s = self._server_pool.pop(0)
            if self.options["max_reconnect_attempts"] > 0:
                if s.reconnects > self.options["max_reconnect_attempts"]:
                    # Discard server since already tried to reconnect too many times
                    continue

            # Not yet exceeded max_reconnect_attempts so can still use
            # this server in the future.
            self._server_pool.append(s)
            if (
                s.last_attempt is not None
                and now < s.last_attempt + self.options["reconnect_time_wait"]
            ):
                # Backoff connecting to server if we attempted recently.
                await asyncio.sleep(self.options["reconnect_time_wait"])
            try:
                s.last_attempt = time.monotonic()
                connection_future = asyncio.open_connection(
                    s.uri.hostname, s.uri.port, limit=DEFAULT_BUFFER_SIZE
                )
                r, w = await asyncio.wait_for(
                    connection_future, self.options["connect_timeout"]
                )
                self._current_server = s

                # We keep a reference to the initial transport we used when
                # establishing the connection in case we later upgrade to TLS
                # after getting the first INFO message. This is in order to
                # prevent the GC closing the socket after we send CONNECT
                # and replace the transport.
                #
                # See https://github.com/nats-io/asyncio-nats/issues/43
                self._bare_io_reader = self._io_reader = r
                self._bare_io_writer = self._io_writer = w
                break
            except Exception as e:
                s.last_attempt = time.monotonic()
                s.reconnects += 1

                self._err = e
                await self._error_cb(e)  # type: ignore[misc]
                continue

    async def _send_command(self, cmd: bytes, priority: bool = False) -> None:
        if priority:
            self._pending.insert(0, cmd)
        else:
            self._pending.append(cmd)
        self._pending_data_size += len(cmd)
        if self._pending_data_size > self.options["pending_size"]:
            await self._flush_pending()

    async def _send_ping(self, future: Optional["Future[bool]"] = None) -> None:
        if future is None:
            future = asyncio.Future()
        self._pongs.append(future)
        self._io_writer.write(PING_PROTO)  # type: ignore[union-attr]
        await self._flush_pending()

    async def _send_publish(
        self,
        subject: str,
        reply: str,
        payload: bytes,
        payload_size: int,
        headers: Optional[Dict[str, str]],
    ) -> None:
        """
        Sends PUB command to the NATS server.
        """
        if subject == "":
            # Avoid sending messages with empty replies.
            raise ErrBadSubject

        pub_cmd = None
        if headers is None:
            pub_cmd = prot_command.pub_cmd(subject, reply, payload)
        else:
            hdr = bytearray()
            hdr.extend(NATS_HDR_LINE)
            for k, v in headers.items():
                hdr.extend(k.encode())
                hdr.extend(b": ")
                hdr.extend(v.encode())
                hdr.extend(_CRLF_)
            hdr.extend(_CRLF_)
            pub_cmd = prot_command.hpub_cmd(subject, reply, hdr, payload)

        self.stats["out_msgs"] += 1
        self.stats["out_bytes"] += payload_size
        await self._send_command(pub_cmd)
        if self._flush_queue.empty():  # type: ignore[union-attr]
            await self._flush_pending()

    async def _send_subscribe(self, sub: Subscription) -> None:
        sub_cmd = prot_command.sub_cmd(sub._subject, sub._queue, sub._id)
        await self._send_command(sub_cmd)
        await self._flush_pending()

    async def _send_unsubscribe(self, sid: int, limit: int = 1) -> None:
        unsub_cmd = prot_command.unsub_cmd(sid, limit)
        await self._send_command(unsub_cmd)
        await self._flush_pending()

    async def __aenter__(self) -> "Client":
        """For when NATS client is used in a context manager"""
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        """Close connection to NATS when used in a context manager"""
        await self._close(Client.CLOSED, do_cbs=True)
