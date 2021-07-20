# type: ignore[misc]
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, TYPE_CHECKING, Optional, Union

from nats.aio.client import Msg

from jsm.models.v1.api.consumer_create_request import (
    AckPolicy,
    Config,
    IoNatsJetstreamApiV1ConsumerCreateRequest,
    ReplayPolicy,
)
from jsm.models.v1.api.consumer_create_response import (
    IoNatsJetstreamApiV1ConsumerCreateResponse,
)
from jsm.models.v1.api.consumer_info_response import (
    IoNatsJetstreamApiV1ConsumerInfoResponse,
)
from jsm.models.v1.api.consumer_list_request import (
    IoNatsJetstreamApiV1ConsumerListRequest,
)
from jsm.models.v1.api.consumer_list_response import (
    IoNatsJetstreamApiV1ConsumerListResponse,
)
from jsm.models.v1.api.consumer_names_request import (
    IoNatsJetstreamApiV1ConsumerNamesRequest,
)
from jsm.models.v1.api.consumer_names_response import (
    IoNatsJetstreamApiV1ConsumerNamesResponse,
)


if TYPE_CHECKING:
    from .client import Client


class ConsumersMixin:
    async def consumer_info(
        self: Client,
        stream: str,
        name: str,
        /,
        timeout: float = 0.5,
    ) -> IoNatsJetstreamApiV1ConsumerInfoResponse:
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.INFO.{stream}.{name}", b"{}", timeout=timeout
        )
        return IoNatsJetstreamApiV1ConsumerInfoResponse.parse_raw(msg.data).__root__

    async def consumer_list(
        self: Client, stream: str, /, offset: int = 0, timeout: float = 0.5
    ) -> IoNatsJetstreamApiV1ConsumerListResponse:
        options = IoNatsJetstreamApiV1ConsumerListRequest(offset=offset)
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.LIST.{stream}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1ConsumerListResponse.parse_raw(msg.data)

    async def consumer_names(
        self: Client, stream: str, /, offset: int = 0, timeout: float = 0.5
    ) -> IoNatsJetstreamApiV1ConsumerNamesResponse:
        options = IoNatsJetstreamApiV1ConsumerNamesRequest(offset=offset)
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.NAMES.{stream}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1ConsumerNamesResponse.parse_raw(msg.data)

    async def consumer_create(
        self: Client,
        stream: str,
        name: str,
        /,
        deliver_subject: Optional[str] = None,
        deliver_policy: Optional[Union[str, int]] = None,
        ack_policy: AckPolicy = "explicit",
        ack_wait: Optional[int] = None,
        max_deliver: Optional[int] = None,
        filter_subject: Optional[str] = None,
        replay_policy: ReplayPolicy = "original",
        sample_freq: Optional[str] = None,
        rate_limit_bps: Optional[int] = None,
        max_ack_pending: Optional[int] = None,
        idle_heartbeat: Optional[int] = None,
        flow_control: Optional[bool] = None,
        max_waiting: int = 512,
        timeout: float = 0.5,
    ) -> IoNatsJetstreamApiV1ConsumerCreateResponse:
        config = Config(
            name=name,
            deliver_subject=deliver_subject,
            deliver_policy=deliver_policy,
            ack_policy=ack_policy,
            ack_wait=ack_wait,
            max_deliver=max_deliver,
            filter_subject=filter_subject,
            replay_policy=replay_policy,
            sample_freq=sample_freq,
            rate_limit_bps=rate_limit_bps,
            max_ack_pending=max_ack_pending,
            idle_heartbeat=idle_heartbeat,
            flow_control=flow_control,
            max_waiting=max_waiting,
        )
        options = IoNatsJetstreamApiV1ConsumerCreateRequest(
            stream_name=stream, config=config
        )
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.CREATE.{stream}.{name}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1ConsumerCreateResponse.parse_raw(msg.data).__root__

    async def consumer_durable_create(
        self: Client,
        stream: str,
        name: str,
        /,
        deliver_subject: Optional[str] = None,
        deliver_policy: Optional[Union[str, int]] = None,
        ack_policy: AckPolicy = "explicit",
        ack_wait: Optional[int] = None,
        max_deliver: Optional[int] = None,
        filter_subject: Optional[str] = None,
        replay_policy: ReplayPolicy = "original",
        sample_freq: Optional[str] = None,
        rate_limit_bps: Optional[int] = None,
        max_ack_pending: Optional[int] = None,
        idle_heartbeat: Optional[int] = None,
        flow_control: Optional[bool] = None,
        max_waiting: int = 512,
        timeout: float = 0.5,
    ) -> IoNatsJetstreamApiV1ConsumerCreateResponse:
        config = Config(
            name=name,
            durable_name=name,
            deliver_subject=deliver_subject,
            deliver_policy=deliver_policy,
            ack_policy=ack_policy,
            ack_wait=ack_wait,
            max_deliver=max_deliver,
            filter_subject=filter_subject,
            replay_policy=replay_policy,
            sample_freq=sample_freq,
            rate_limit_bps=rate_limit_bps,
            max_ack_pending=max_ack_pending,
            idle_heartbeat=idle_heartbeat,
            flow_control=flow_control,
            max_waiting=max_waiting,
        )
        options = IoNatsJetstreamApiV1ConsumerCreateRequest(
            stream_name=stream, config=config
        )
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.DURABLE.CREATE.{stream}.{name}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1ConsumerCreateResponse.parse_raw(msg.data).__root__

    async def consumer_pull_next(
        self: Client,
        stream: str,
        name: str,
        /,
        queue: str = "",
        auto_ack: bool = True,
    ) -> Msg:
        async for msg in self.consumer_pull_msgs(
            stream, name, queue=queue, auto_ack=auto_ack
        ):
            return msg

    async def consumer_pull_msgs(
        self: Client, stream: str, name: str, /, queue: str = "", auto_ack: bool = True
    ) -> AsyncGenerator[Msg, None]:
        _inbox = self._nuid.next().decode("utf-8")
        _inbox_queue: asyncio.Queue[Msg] = asyncio.Queue()

        async def cb(msg: Msg) -> None:
            await _inbox_queue.put(msg)

        sid = await self.subscribe(_inbox, queue=queue, cb=cb)

        try:
            while True:
                await self.publish_request(
                    f"$JS.API.CONSUMER.MSG.NEXT.{stream}.{name}",
                    reply=_inbox,
                    payload=b"1",
                )
                msg = await _inbox_queue.get()
                if auto_ack:
                    await self.publish(msg.reply, b"")
                yield msg
        finally:
            await self.unsubscribe(sid)
