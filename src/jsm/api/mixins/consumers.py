from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator, List, Optional, Union

from jsm.api.subscription import Msg, Subscription
from jsm.models.consumers import (
    AckPolicy,
    Config,
    DeliverPolicy,
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
from jsm.models.errors import IoNatsJetstreamApiV1ErrorResponse
from jsm.models.messages import Message

from .request_reply import BaseJetStreamRequestReplyMixin, JetStreamResponse


class ConsumersMixin(BaseJetStreamRequestReplyMixin):
    async def consumer_info(
        self,
        stream: str,
        name: str,
        /,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1ConsumerInfoResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        return await self._jetstream_request(
            f"CONSUMER.INFO.{stream}.{name}",
            None,
            JetStreamResponse[IoNatsJetstreamApiV1ConsumerInfoResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def consumer_list(
        self,
        stream: str,
        /,
        offset: int = 0,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1ConsumerListResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        options = IoNatsJetstreamApiV1ConsumerListRequest(offset=offset)
        return await self._jetstream_request(
            f"CONSUMER.LIST.{stream}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1ConsumerListResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def consumer_names(
        self,
        stream: str,
        /,
        offset: int = 0,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> IoNatsJetstreamApiV1ConsumerNamesResponse:
        options = IoNatsJetstreamApiV1ConsumerNamesRequest(offset=offset)
        return await self._jetstream_request(
            f"CONSUMER.NAMES.{stream}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1ConsumerNamesResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def consumer_create(
        self,
        stream: str,
        /,
        deliver_subject: Optional[str] = None,
        deliver_group: Optional[str] = None,
        deliver_policy: DeliverPolicy = "last",
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
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1ConsumerCreateResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        config = Config(
            deliver_subject=deliver_subject,
            deliver_policy=deliver_policy,
            deliver_group=deliver_group,
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
        return await self._jetstream_request(
            f"CONSUMER.CREATE.{stream}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1ConsumerCreateResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def consumer_durable_create(
        self,
        stream: str,
        name: str,
        /,
        durable_name: Optional[str] = None,
        deliver_subject: Optional[str] = None,
        deliver_group: Optional[str] = None,
        deliver_policy: DeliverPolicy = "last",
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
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1ConsumerCreateResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        config = Config(
            name=name,
            durable_name=durable_name or name,
            deliver_subject=deliver_subject,
            deliver_group=deliver_group,
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
        return await self._jetstream_request(
            f"CONSUMER.DURABLE.CREATE.{stream}.{name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1ConsumerCreateResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def consumer_pull_next(
        self,
        stream: str,
        name: str,
        /,
        auto_ack: bool = True,
    ) -> Message:
        # Wait for consumer next message
        async for msg in self.consumer_pull_msgs(stream, name, auto_ack=auto_ack):
            # Return on first message
            return msg

    async def consumer_pull_msgs(
        self,
        stream: str,
        name: str,
        /,
        auto_ack: bool = True,
        max_msgs: Optional[int] = None,
    ) -> AsyncGenerator[Message, None]:
        # inbox: str = self._nc._nuid.next().decode("utf-8")
        inbox: str = self._nuid.next().decode("utf-8")  # type: ignore[attr-defined]
        # subscription = Subscription(self._nc, inbox)
        subscription = Subscription(self, inbox)
        total: int = 0
        # Start the subscription
        await subscription.start()
        # Stop subscription on error
        try:
            while True:
                # Stop subscription if maximum number of message has been received
                if max_msgs and (max_msgs <= total):
                    break
                # Request next message to be published on inbox subject
                # await self._nc.publish_request(
                await self.publish_request(  # type: ignore[attr-defined]
                    f"$JS.API.CONSUMER.MSG.NEXT.{stream}.{name}",
                    reply=inbox,
                    payload=b"1",
                )
                # Wait for next message on inbox subscription
                msg = await subscription.next_msg()
                # Increment message counter
                total += 1
                # Optionally acknowledge the message
                if auto_ack:
                    await msg.ack()
                # Yield the message
                yield Message.from_msg(msg)
        # Always stop the subscription on exit
        finally:
            await subscription.stop()

    async def consumer_delete(
        self,
        stream: str,
        name: str,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> IoNatsJetstreamApiV1ConsumerDeleteResponse:
        return await self._jetstream_request(
            f"CONSUMER.DELETE.{stream}.{name}",
            None,
            JetStreamResponse[IoNatsJetstreamApiV1ConsumerDeleteResponse],
            timeout=timeout,
            raise_on_error=raise_on_error,
        )

    async def kv_history(
        self,
        name: str,
        key: str,
        timeout: Optional[float] = None,
    ) -> List[Msg]:
        """This is not efficient, I think it should NOT use a durable consumer, but I don't know how to use non durable consumers."""
        # Create a consumer without durable name
        _now = int(datetime.utcnow().timestamp() * 1000)
        _stream = f"KV_{name}"
        _subject = f"$KV.{name}.{key}"
        _consumer = f"{_stream}_HISTORY_{_now}"
        consumer: IoNatsJetstreamApiV1ConsumerCreateResponse = (
            await self.consumer_durable_create(
                _stream,
                _consumer,
                deliver_group=_consumer,
                deliver_subject=None,
                deliver_policy=DeliverPolicy.all,
                replay_policy=ReplayPolicy.instant,
                filter_subject=_subject,
                raise_on_error=True,
                timeout=timeout,
            )
        )
        history_size = consumer.num_pending
        versions = []
        async for msg in self.consumer_pull_msgs(
            _stream, _consumer, max_msgs=history_size, auto_ack=True
        ):
            versions.append(msg)
        await self.consumer_delete(_stream, _consumer)
        return versions
