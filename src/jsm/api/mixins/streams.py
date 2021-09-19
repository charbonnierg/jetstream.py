from __future__ import annotations

from base64 import b64decode
from typing import Any, Dict, List, Optional, Union

from jsm.models.errors import IoNatsJetstreamApiV1ErrorResponse
from jsm.models.messages import Message
from jsm.models.streams import (
    Discard,
    IoNatsJetstreamApiV1StreamCreateRequest,
    IoNatsJetstreamApiV1StreamCreateResponse,
    IoNatsJetstreamApiV1StreamDeleteResponse,
    IoNatsJetstreamApiV1StreamInfoRequest,
    IoNatsJetstreamApiV1StreamInfoResponse,
    IoNatsJetstreamApiV1StreamListRequest,
    IoNatsJetstreamApiV1StreamListResponse,
    IoNatsJetstreamApiV1StreamMsgDeleteRequest,
    IoNatsJetstreamApiV1StreamMsgDeleteResponse,
    IoNatsJetstreamApiV1StreamMsgGetRequest,
    IoNatsJetstreamApiV1StreamMsgGetResponse,
    IoNatsJetstreamApiV1StreamNamesRequest,
    IoNatsJetstreamApiV1StreamNamesResponse,
    IoNatsJetstreamApiV1StreamPurgeRequest,
    IoNatsJetstreamApiV1StreamPurgeResponse,
    IoNatsJetstreamApiV1StreamUpdateRequest,
    IoNatsJetstreamApiV1StreamUpdateResponse,
    Mirror,
    PubAck,
    Retention,
    Storage,
)

from .request_reply import BaseJetStreamRequestReplyMixin, JetStreamResponse


class StreamsMixin(BaseJetStreamRequestReplyMixin):
    """This mixin implements methods used to manipulate Jetstream Streams.

    Notes:
        * This is meant to be used by classes which inherit nats.aio.client.Client and not by end user directly

    Docs:
        * Jetstream NATS API Reference: <https://docs.nats.io/jetstream/nats_api_reference#streams>
    """

    async def stream_list(
        self,
        offset: int = 0,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamListResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """List existing streams.

        Args:
            offset: number of streams to skip

        Returns:
            An IoNatsJetstreamApiV1StreamListResponse which holds a list of streams as `streams` attribute.

        Examples:
            >>> stream_list_res = await js.stream_list()
            >>> # Access the results using the `.streams` attribute
            >>> for stream in stream_list_res.streams:
            >>>     print(stream.name)
        """
        options = IoNatsJetstreamApiV1StreamListRequest(offset=offset)
        return await self._jetstream_request(
            "STREAM.LIST",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamListResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_names(
        self,
        offset: int = 0,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamNamesResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """List existing stream names.

        Args:
            offset:

        Returns:
            An IoNatsJetstreamApiV1StreamListResponse instance which holds a list of streams as `streams` attribute.

        Examples:
            >>> stream_list_res = await js.stream_list()
            >>> # Access the results using the `.streams` attribute
            >>> for stream in stream_list_res.streams:
            >>>     # Note: stream is a string here (I.E, the name of the actual stream)
            >>>     print(stream)
        """
        options = IoNatsJetstreamApiV1StreamNamesRequest(offset=offset)
        return await self._jetstream_request(
            "STREAM.NAMES",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamNamesResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_create(
        self,
        name: str,
        /,
        subjects: Optional[List[str]] = None,
        retention: Retention = "limits",
        max_consumers: int = -1,
        max_msgs: int = -1,
        max_msgs_per_subject: int = -1,
        max_bytes: int = -1,
        max_age: int = 0,
        max_msg_size: int = -1,
        storage: Storage = "file",
        num_replicas: int = 1,
        duplicate_window: Optional[int] = 0,
        no_ack: Optional[bool] = False,
        mirror: Optional[Mirror] = None,
        sources: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
        **kwargs: Any,
    ) -> Union[
        IoNatsJetstreamApiV1StreamCreateResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Create a new stream.

        Args:
            * `subjects`: A list of subjects to consume, supports wildcards. Must be empty when a mirror is configured. May be empty when sources are configured.
            * `retention`: How messages are retained in the Stream, once this is exceeded old messages are removed.
            * `max_consumers`: How many Consumers can be defined for a given Stream. -1 for unlimited.
            * `max_msgs`: How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.
            * `max_msgs_per_subject`: For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit
            * `max_bytes`: How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.
            * `max_age`: Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.
            * `max_msg_size`: The largest message that will be accepted by the Stream. -1 for unlimited.
            * `storage`: The storage backend to use for the Stream ('file' or 'memory').
            * `num_replicas`: How many replicas to keep for each message.
            * `mirror`: Maintains a 1:1 mirror of another stream with name matching this argument.  When a mirror is configured subjects and sources must be empty.
            * `sources`: List of Stream names to replicate into this Stream.
            * `timeout`: timeout to wait before raising a TimeoutError.

        Returns:
            An IoNatsJetstreamApiV1StreamCreateResponse instance which holds either an error or stream infos and state.

        References:
            * Streams - [NATS Docs](https://docs.nats.io/jetstream/concepts/streams)
            * Stream, NATS API Reference - [NATS Docs](https://docs.nats.io/jetstream/nats_api_reference#streams)
            * `io.nats.jetstream.api.v1.stream_create_response` (JSON Schema): <https://github.com/nats-io/jsm.go/blob/v0.0.24/schemas/jetstream/api/v1/stream_create_request.json>
            * `io.nats.jetstream.api.v1.stream_create_request` (JSON Schema): <https://github.com/nats-io/jsm.go/blob/v0.0.24/schemas/jetstream/api/v1/stream_create_response.json>
        """
        options = IoNatsJetstreamApiV1StreamCreateRequest(
            name=name,
            subjects=subjects,
            retention=retention,
            max_consumers=max_consumers,
            max_msgs=max_msgs,
            max_msgs_per_subject=max_msgs_per_subject,
            max_bytes=max_bytes,
            max_msg_size=max_msg_size,
            max_age=max_age,
            storage=storage,
            num_replicas=num_replicas,
            mirror=mirror,
            sources=sources,
            duplicate_window=duplicate_window,
            no_ack=no_ack,
            **kwargs,
        )
        return await self._jetstream_request(
            f"STREAM.CREATE.{name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamCreateResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_info(
        self,
        name: str,
        /,
        deleted_details: bool = False,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamInfoResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Get info about a specific stream.

        Args:
            name: stream name. Argument is positional only.
            deleted_details: When set to True, response will include details about deleted messages.
            timeout: seconds to wait before raising a TimeoutError.

        Returns:
            An IoNatsJetstreamApiV1StreamInfoResponse instance which holds info about the stream.
        """
        options = IoNatsJetstreamApiV1StreamInfoRequest(deleted_details=deleted_details)
        return await self._jetstream_request(
            f"STREAM.INFO.{name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamInfoResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_update(
        self,
        _name: str,
        /,
        name: Optional[str] = None,
        subjects: Optional[List[str]] = None,
        retention: Optional[Retention] = None,
        discard: Optional[Discard] = None,
        max_consumers: Optional[int] = None,
        max_msgs: Optional[int] = None,
        max_bytes: Optional[int] = None,
        max_age: Optional[int] = None,
        storage: Optional[Storage] = None,
        num_replicas: Optional[int] = None,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
        **kwargs: Any,
    ) -> Union[
        IoNatsJetstreamApiV1StreamUpdateResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Update an existing stream by its name.

        Args:
            * `subjects`: A list of subjects to consume, supports wildcards. Must be empty when a mirror is configured. May be empty when sources are configured.
            * `retention`: How messages are retained in the Stream, once this is exceeded old messages are removed.
            * `max_consumers`: How many Consumers can be defined for a given Stream. -1 for unlimited.
            * `max_msgs`: How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.
            * `max_msgs_per_subject`: For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit
            * `max_bytes`: How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.
            * `max_age`: Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.
            * `max_msg_size`: The largest message that will be accepted by the Stream. -1 for unlimited.
            * `storage`: The storage backend to use for the Stream ('file' or 'memory').
            * `num_replicas`: How many replicas to keep for each message.
            * `timeout`: timeout to wait before raising a TimeoutError.
            * `raise_on_error`: raise a JetstreamException instead of returning an error response when set to True.

        Returns:
            An IoNatsJetstreamApiV1StreamCreateResponse instance which holds either an error or stream infos and state.

        References:
            * Streams - [NATS Docs](https://docs.nats.io/jetstream/concepts/streams)
            * Stream, NATS API Reference - [NATS Docs](https://docs.nats.io/jetstream/nats_api_reference#streams)
            * `io.nats.jetstream.api.v1.stream_update_response` (JSON Schema): <https://github.com/nats-io/jsm.go/blob/v0.0.24/schemas/jetstream/api/v1/stream_update_response.json>
            * `io.nats.jetstream.api.v1.stream_update_request` (JSON Schema): <https://github.com/nats-io/jsm.go/blob/v0.0.24/schemas/jetstream/api/v1/stream_update_request.json>
        """
        current_config = (await self.stream_info(_name, False)).config.dict(
            exclude_unset=True,
            exclude_none=True,
        )
        new_config: Dict[str, Any] = {}
        if name is not None:
            new_config["name"] = name
        else:
            kwargs.pop("names", None)
            new_config["name"] = _name
        if subjects is not None:
            new_config["subjects"] = subjects
        if retention is not None:
            new_config["retention"] = retention
        else:
            new_config["retention"] = current_config["retention"].value
        if discard is not None:
            new_config["discard"] = discard
        else:
            kwargs.pop("discard", None)
            new_config["discard"] = current_config["discard"].value
        if max_consumers is not None:
            new_config["max_consumers"] = max_consumers
        if max_msgs is not None:
            new_config["max_msgs"] = max_msgs
        if max_bytes is not None:
            new_config["max_bytes"] = max_bytes
        if max_age is not None:
            new_config["max_age"] = max_age
        if storage is not None:
            new_config["storage"] = storage
        else:
            kwargs.pop("storage", None)
            new_config["storage"] = current_config["storage"].value
        if num_replicas is not None:
            new_config["num_replicas"] = num_replicas
        options = IoNatsJetstreamApiV1StreamUpdateRequest(
            **{**current_config, **kwargs, **new_config}
        )
        return await self._jetstream_request(
            f"STREAM.UPDATE.{_name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamUpdateResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_delete(
        self,
        name: str,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamDeleteResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Delete a stream by its name.

        Args:
            * `name`: Name of the stream
            * `timeout`: timeout to wait before raising a TimeoutError.
            * `raise_on_error`: raise a JetstreamException instead of returning an error response when set to True.

        Returns:
            An IoNatsJetstreamApiV1StreamDeleteResponse or an IoNatsJetstreamApiV1ErrorResponse
        """
        return await self._jetstream_request(
            f"STREAM.DELETE.{name}",
            None,
            JetStreamResponse[IoNatsJetstreamApiV1StreamDeleteResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_purge(
        self,
        name: str,
        filter: Optional[str] = None,
        seq: Optional[int] = None,
        keep: Optional[int] = None,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamPurgeResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Purge messages from a stream.

        Args:
            * `name`: Name of the stream
            * `filter`: Restrict purging to messages that match this subject.
            * `seq`: Purge all messages up to but not including the message with this sequence. Can be combined with subject filter but not the keep option.
            * `keep`: Ensures this many messages are present after the purge. Can be combined with the subject filter but not the sequence.
            * `timeout`: timeout to wait before raising a TimeoutError.
            * `raise_on_error`: raise a JetstreamException instead of returning an error response when set to True.

        Returns:
            An IoNatsJetstreamApiV1StreamPurgeResponse or an IoNatsJetstreamApiV1ErrorResponse
        """
        options = IoNatsJetstreamApiV1StreamPurgeRequest(
            filter=filter, seq=seq, keep=keep
        )
        return await self._jetstream_request(
            f"STREAM.PURGE.{name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamPurgeResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_msg_get(
        self,
        name: str,
        /,
        seq: Optional[int] = None,
        last_by_subj: Optional[str] = None,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamMsgGetResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Get a message from a stream by sequence.

        Args:
            * `name`: Name of the stream.
            * `seq`: Stream sequence number of the message to get.
            * `timeout`: timeout to wait before raising a TimeoutError.
            * `raise_on_error`: raise a JetstreamException instead of returning an error response when set to True.

        Returns:
               An IoNatsJetstreamApiV1StreamMsgGetResponse or an IoNatsJetstreamApiV1ErrorResponse.
        """
        options = IoNatsJetstreamApiV1StreamMsgGetRequest(
            seq=seq, last_by_subj=last_by_subj
        )
        res = await self._jetstream_request(
            f"STREAM.MSG.GET.{name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamMsgGetResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )
        if isinstance(res, IoNatsJetstreamApiV1StreamMsgGetResponse):
            res.message.data = b64decode(res.message.data)
        return res

    async def stream_msg_delete(
        self,
        name: str,
        /,
        seq: int,
        no_erase: Optional[bool] = None,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1StreamMsgDeleteResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """Delete a message from a stream.

        Args:
            * `name`: Name of the stream
            * `seq`: Stream sequence number of the message to delete.
            * `no_erase`: Default will securely remove a message and rewrite the data with random data, set this to true to only remove the message
            * `timeout`: timeout to wait before raising a TimeoutError.
            * `raise_on_error`: raise a JetstreamException instead of returning an error response when set to True.

        Returns:
            An IoNatsJetstreamApiV1StreamMsgDeleteResponse or an IoNatsJetstreamApiV1ErrorResponse.
        """
        options = IoNatsJetstreamApiV1StreamMsgDeleteRequest(seq=seq, no_erase=no_erase)
        return await self._jetstream_request(
            f"STREAM.MSG.DELETE.{name}",
            options,
            JetStreamResponse[IoNatsJetstreamApiV1StreamMsgDeleteResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )

    async def stream_publish(
        self,
        subject: str,
        /,
        payload: bytes,
        timeout: Optional[float] = None,
    ) -> PubAck:
        """Publish a message to an NATS subject and wait for stream acknowledgement.

        Args:
            * `subject`: subject to publish message to
            * `payload`: content of the message in bytes
            * `timeout`: optional timeout in seconds
        """
        options = {"timeout": timeout} if timeout else {}
        res = await self.request(subject, payload, **options)  # type: ignore[attr-defined]
        return PubAck.parse_raw(res.data)

    async def kv_add(
        self,
        name: str,
        history: int = -1,
        ttl: int = 0,
        max_bucket_size: int = -1,
        max_value_size: int = -1,
        duplicate_window: int = 0,
        replicas: int = 1,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> IoNatsJetstreamApiV1StreamCreateResponse:
        """Add a new KV store (bucket).

        Args:
            name: Name of the bucket.
            history: How many historic values to keep per key.
            ttl: How long to keep values for, expressed in nanoseconds.
            max_bucket_size: Maximum size for the bucket in bytes.
            max_value_size: Maximum size for any single value in bytes.
            duplicate_window: The time window to track duplicate messages for, expressed in nanoseconds.
            replicas: How many replicas of the data to store.
            timeout: timeout to wait before raising a TimeoutError.
            raise_on_error: Raise an Exception if response from JetStream is not a successfull response.
        """
        result = await self.stream_create(
            # The main write bucket must be called KV_<Bucket Name>
            f"KV_{name}",
            # The ingest subjects must be $KV.<Bucket Name>.>
            subjects=[f"$KV.{name}.>"],
            # Ack is always enabled
            no_ack=False,
            # Number of consumers is always illimited
            max_consumers=-1,
            # Limit is always "limits"
            retention=Retention.limits,
            # Storage is always "file"
            storage=Storage.file,
            # User can still configure replicas
            num_replicas=replicas,
            # Duplicate window must be same as max_age when max_age is less than 2 minutes
            duplicate_window=ttl if ttl < 60 * 5 * 1e9 else duplicate_window,
            # Key TTL is managed using the max_age key
            max_age=ttl,
            # Maximum value sizes can be capped using max_msg_size,
            max_msg_size=max_value_size,
            # Overall bucket size can be limited using max_bytes
            max_bytes=max_bucket_size,
            # The bucket history is achieved by setting max_msgs_per_subject to the desired history level
            max_msgs_per_subject=history,
            timeout=timeout,
        )
        return result

    async def kv_rm(
        self,
        name: str,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> IoNatsJetstreamApiV1StreamDeleteResponse:
        """Delete a KV store.

        Be careful, this will permanently delete a whole KV store.

        Args:
            name: Name of the KV store (bucket) to remove
            timeout: timeout to wait before raising a TimeoutError.
            raise_on_error: Raise an Exception if response from JetStream is not a successfull response.
        """
        res = await self.stream_delete(
            f"KV_{name}", timeout=timeout, raise_on_error=raise_on_error
        )
        return res

    async def kv_get(
        self,
        name: str,
        key: str,
    ) -> Message:
        """Fetch a key from a KV store bucket"""
        result: IoNatsJetstreamApiV1StreamMsgGetResponse = await self.stream_msg_get(
            f"KV_{name}", last_by_subj=f"$KV.{name}.{key}", raise_on_error=True
        )
        return result.message

    async def kv_put(
        self,
        name: str,
        key: str,
        value: bytes,
        timeout: Optional[float] = None,
    ) -> PubAck:
        """Put a new value in a KV Store (bucket) under given key.

        This method can be used to both add a new key/value pair or update an existing key value
        """
        # Publish the message and return an acknowledgement
        return await self.stream_publish(
            f"$KV.{name}.{key}", payload=value, timeout=timeout
        )
