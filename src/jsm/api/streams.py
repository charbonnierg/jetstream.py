from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from nats.aio.client import Msg

from jsm.models.base import IoNatsJetstreamApiV1Response
from jsm.models.errors import IoNatsJetstreamApiV1ErrorResponse
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
    Retention,
    Storage,
)

if TYPE_CHECKING:
    from .client import Client


class StreamsMixin:
    """This mixin implements methods used to manipulate Jetstream Streams.

    Notes:
        * This is meant to be used by classes which inherit nats.aio.client.Client and not by end user directly

    Docs:
        * Jetstream NATS API Reference: <https://docs.nats.io/jetstream/nats_api_reference#streams>
    """

    async def stream_list(  # type: ignore[misc]
        self: Client,
        timeout: float = 0.5,
        offset: int = 0,
        raise_on_error: bool = False,
    ) -> Union[
        IoNatsJetstreamApiV1StreamListResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        """List existing streams.

        Args:
            offset:

        Returns:
            An IoNatsJetstreamApiV1StreamListResponse which holds a list of streams as `streams` attribute.

        Examples:
            >>> stream_list_res = await js.stream_list()
            >>> # Access the results using the `.streams` attribute
            >>> for stream in stream_list_res.streams:
            >>>     print(stream.name)
        """
        options = IoNatsJetstreamApiV1StreamListRequest(offset=offset)
        msg: Msg = await self.request(
            "$JS.API.STREAM.LIST",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamListResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_names(  # type: ignore[misc]
        self: Client,
        timeout: float = 0.5,
        offset: int = 0,
        raise_on_error: bool = False,
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
        msg: Msg = await self.request(
            "$JS.API.STREAM.NAMES",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamNamesResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_create(  # type: ignore[misc]
        self: Client,
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
        timeout: float = 0.5,
        raise_on_error: bool = False,
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
            * `timeout`: timeout to wait before raising a TimeoutError.

        Returns:
            An IoNatsJetstreamApiV1StreamCreateResponse instance which holds either an error or stream infos and state.

        References:
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
            **kwargs,
        )
        msg: Msg = await self.request(
            f"$JS.API.STREAM.CREATE.{name}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamCreateResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_info(  # type: ignore[misc]
        self: Client,
        name: str,
        /,
        deleted_details: bool = False,
        timeout: float = 0.5,
        raise_on_error: bool = False,
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
        msg: Msg = await self.request(
            f"$JS.API.STREAM.INFO.{name}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamInfoResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_update(  # type: ignore[misc]
        self: Client,
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
        timeout: float = 0.5,
        raise_on_error: bool = False,
        **kwargs: Any,
    ) -> Union[
        IoNatsJetstreamApiV1StreamUpdateResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
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
        # return options
        msg: Msg = await self.request(
            f"$JS.API.STREAM.UPDATE.{_name}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamUpdateResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_delete(  # type: ignore[misc]
        self: Client,
        name: str,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> Union[
        IoNatsJetstreamApiV1StreamDeleteResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        msg: Msg = await self.request(
            f"$JS.API.STREAM.DELETE.{name}", b"", timeout=timeout
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamDeleteResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_purge(  # type: ignore[misc]
        self: Client,
        name: str,
        filter: Optional[str] = None,
        seq: Optional[int] = None,
        keep: Optional[int] = None,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> Union[
        IoNatsJetstreamApiV1StreamPurgeResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        options = IoNatsJetstreamApiV1StreamPurgeRequest(
            filter=filter, seq=seq, keep=keep
        )
        msg: Msg = await self.request(
            f"$JS.API.STREAM.PURGE.{name}",
            options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamPurgeResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_msg_get(  # type: ignore[misc]
        self: Client,
        name: str,
        /,
        seq: int,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> Union[
        IoNatsJetstreamApiV1StreamMsgGetResponse, IoNatsJetstreamApiV1ErrorResponse
    ]:
        options = IoNatsJetstreamApiV1StreamMsgGetRequest(seq=seq)
        msg: Msg = await self.request(
            f"$JS.API.STREAM.MSG.GET.{name}",
            options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamMsgGetResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    async def stream_msg_delete(  # type: ignore[misc]
        self: Client,
        name: str,
        /,
        seq: int,
        no_erase: Optional[bool] = None,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> IoNatsJetstreamApiV1StreamMsgDeleteResponse:
        options = IoNatsJetstreamApiV1StreamMsgDeleteRequest(seq=seq, no_erase=no_erase)
        msg: Msg = await self.request(
            f"$JS.API.STREAM.MSG.DELETE.{name}",
            options.json().encode("utf-8"),
            timeout=timeout,
        )
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamMsgDeleteResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__

    # async def stream_snapshot(  # type: ignore[misc]
    #     self: Client,
    #     name: str,
    #     /,
    #     no_consumers: Optional[bool] = None,
    #     chunk_size: Optional[int] = None,
    #     jsck: Optional[bool] = False,
    #     timeout: float = 0.5,
    #     raise_on_error: bool = False,
    # ) -> IoNatsJetstreamApiV1StreamSnapshotResponse:
    #     backup: Optional[bytes] = None
    #     deliver_subject = self._nuid.next().decode("utf-8")
    #     backup_queue: Queue[bytes] = asyncio.Queue(maxsize=1)

    #     async def handle_backup(msg: Msg) -> None:
    #         await backup_queue.put(msg)

    #     sid = await self.subscribe(deliver_subject, cb=handle_backup)
    #     options = IoNatsJetstreamApiV1StreamSnapshotRequest(
    #         deliver_subject=deliver_subject,
    #         no_consumers=no_consumers,
    #         chunk_size=chunk_size,
    #         jsck=jsck,
    #     )
    #     msg: Msg = await self.request(
    #         f"$JS.API.STREAM.SNAPSHOT.{name}",
    #         options.json().encode("utf-8"),
    #         timeout=timeout,
    #     )
    #     response = IoNatsJetstreamApiV1Response[
    #         IoNatsJetstreamApiV1StreamSnapshotResponse
    #     ].parse_raw(msg.data)
    #     if not isinstance(response.__root__, IoNatsJetstreamApiV1ErrorResponse):
    #         backup = await backup_queue.get()
    #         backup_queue.task_done()
    #         # TODO: What do we do with the backup ? We should certainly not
    #         # handle it in such manner that it blocks this function call
    #     await self.unsubscribe(sid)
    #     if raise_on_error:
    #         response.raise_on_error()
    #     return response.__root__, backup
