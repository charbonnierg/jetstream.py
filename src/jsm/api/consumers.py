from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Optional, Union

from nats.aio.client import Msg

from jsm.models.base import IoNatsJetstreamApiV1Response
from jsm.models.consumers import (
    AckPolicy,
    Config,
    IoNatsJetstreamApiV1ConsumerCreateRequest,
    IoNatsJetstreamApiV1ConsumerCreateResponse,
    IoNatsJetstreamApiV1ConsumerDeleteResponse,
    IoNatsJetstreamApiV1ConsumerInfoResponse,
    IoNatsJetstreamApiV1ConsumerListRequest,
    IoNatsJetstreamApiV1ConsumerListResponse,
    IoNatsJetstreamApiV1ConsumerNamesRequest,
    IoNatsJetstreamApiV1ConsumerNamesResponse,
    ReplayPolicy,
)

if TYPE_CHECKING:
    from .client import Client


class ConsumersMixin:
    async def consumer_info(  # type: ignore[misc]
        self: Client,
        stream: str,
        name: str,
        /,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> IoNatsJetstreamApiV1ConsumerInfoResponse:
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.INFO.{stream}.{name}", b"{}", timeout=timeout
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1ConsumerInfoResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def consumer_list(  # type: ignore[misc]
        self: Client,
        stream: str,
        /,
        offset: int = 0,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> IoNatsJetstreamApiV1ConsumerListResponse:
        options = IoNatsJetstreamApiV1ConsumerListRequest(offset=offset)
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.LIST.{stream}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1ConsumerListResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def consumer_names(  # type: ignore[misc]
        self: Client,
        stream: str,
        /,
        offset: int = 0,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> IoNatsJetstreamApiV1ConsumerNamesResponse:
        options = IoNatsJetstreamApiV1ConsumerNamesRequest(offset=offset)
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.NAMES.{stream}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1ConsumerNamesResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def consumer_create(  # type: ignore[misc]
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
        raise_on_error: bool = False,
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
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1ConsumerCreateResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def consumer_durable_create(  # type: ignore[misc]
        self: Client,
        stream: str,
        name: str,
        /,
        durable_name: Optional[str] = None,
        deliver_subject: Optional[str] = None,
        deliver_policy: Union[str, int] = "last",
        replay_policy: ReplayPolicy = "instant",
        ack_policy: AckPolicy = "explicit",
        ack_wait: Optional[int] = None,
        max_deliver: int = -1,
        filter_subject: Optional[str] = None,
        sample_freq: Optional[str] = None,
        rate_limit_bps: Optional[int] = None,
        max_ack_pending: Optional[int] = None,
        idle_heartbeat: Optional[int] = None,
        flow_control: Optional[bool] = None,
        max_waiting: Optional[int] = None,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> IoNatsJetstreamApiV1ConsumerCreateResponse:
        config = Config(
            name=name,
            durable_name=durable_name or name,
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
            payload=options.json(exclude_none=True).encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1ConsumerCreateResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def consumer_pull_next(  # type: ignore[misc]
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

    async def consumer_pull_msgs(  # type: ignore[misc]
        self: Client,
        stream: str,
        name: str,
        /,
        queue: str = "",
        auto_ack: bool = True,
        max_msgs: Optional[int] = None,
    ) -> AsyncGenerator[Msg, None]:
        _inbox = self._nuid.next().decode("utf-8")
        subscription = self.create_subscribtion(_inbox, queue=queue)
        total = 0
        await subscription.start()
        try:
            while True:
                if max_msgs and max_msgs <= total:
                    break
                await self.publish_request(
                    f"$JS.API.CONSUMER.MSG.NEXT.{stream}.{name}",
                    reply=_inbox,
                    payload=b"1",
                )
                msg = await subscription.next_message()
                total += 1
                if auto_ack:
                    await self.publish(msg.reply, b"")
                yield msg
        finally:
            await subscription.stop()

    async def consumer_delete(  # type: ignore[misc]
        self: Client,
        stream: str,
        name: str,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> IoNatsJetstreamApiV1ConsumerDeleteResponse:
        msg: Msg = await self.request(
            f"$JS.API.CONSUMER.DELETE.{stream}.{name}", b"", timeout=timeout
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1ConsumerDeleteResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__
