from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from nats.aio.client import Msg

from jsm.models.v1.api.stream_create_request import (
    IoNatsJetstreamApiV1StreamCreateRequest,
    Retention,
    Storage,
)
from jsm.models.v1.api.stream_create_response import (
    IoNatsJetstreamApiV1StreamCreateResponse,
)
from jsm.models.v1.api.stream_delete_response import (
    IoNatsJetstreamApiV1StreamDeleteResponse,
)
from jsm.models.v1.api.stream_info_request import IoNatsJetstreamApiV1StreamInfoRequest
from jsm.models.v1.api.stream_info_response import (
    IoNatsJetstreamApiV1StreamInfoResponse,
)
from jsm.models.v1.api.stream_list_request import IoNatsJetstreamApiV1StreamListRequest
from jsm.models.v1.api.stream_list_response import (
    IoNatsJetstreamApiV1StreamListResponse,
)
from jsm.models.v1.api.stream_names_request import (
    IoNatsJetstreamApiV1StreamNamesRequest,
)
from jsm.models.v1.api.stream_names_response import (
    IoNatsJetstreamApiV1StreamNamesResponse,
)
from jsm.models.v1.api.stream_update_request import (
    IoNatsJetstreamApiV1StreamUpdateRequest,
)
from jsm.models.v1.api.stream_update_response import (
    Discard,
    IoNatsJetstreamApiV1StreamUpdateResponse,
)

if TYPE_CHECKING:
    from .client import JetstreamClient


class StreamsMixin:
    async def stream_list(
        self: JetstreamClient,
        timeout: float = 0.5,
        offset: int = 0,
    ) -> IoNatsJetstreamApiV1StreamListResponse:
        options = IoNatsJetstreamApiV1StreamListRequest(offset=offset)
        msg: Msg = await self.request(
            "$JS.API.STREAM.LIST",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1StreamListResponse.parse_raw(msg.data)

    async def stream_names(
        self: JetstreamClient,
        timeout: float = 0.5,
        offset: int = 0,
    ) -> IoNatsJetstreamApiV1StreamNamesResponse:
        options = IoNatsJetstreamApiV1StreamNamesRequest(offset=offset)
        msg: Msg = await self.request(
            "$JS.API.STREAM.NAMES",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1StreamNamesResponse.parse_raw(msg.data)

    async def stream_create(
        self: JetstreamClient,
        name: str,
        /,
        subjects: List[str],
        retention: Retention = "limits",
        max_consumers: int = -1,
        max_msgs: int = -1,
        max_bytes: int = -1,
        max_age: int = 0,
        storage: Storage = "file",
        num_replicas: int = 1,
        timeout: int = 0.5,
        **kwargs: Any,
    ) -> IoNatsJetstreamApiV1StreamCreateResponse:
        options = IoNatsJetstreamApiV1StreamCreateRequest(
            name=name,
            subjects=subjects,
            retention=retention,
            max_consumers=max_consumers,
            max_msgs=max_msgs,
            max_bytes=max_bytes,
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
        return IoNatsJetstreamApiV1StreamCreateResponse.parse_raw(msg.data).__root__

    async def stream_info(
        self: JetstreamClient,
        name: str,
        /,
        deleted_details: bool = False,
        timeout: float = 0.5,
    ) -> IoNatsJetstreamApiV1StreamInfoResponse:
        options = IoNatsJetstreamApiV1StreamInfoRequest(deleted_details=deleted_details)
        msg: Msg = await self.request(
            f"$JS.API.STREAM.INFO.{name}",
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        return IoNatsJetstreamApiV1StreamInfoResponse.parse_raw(msg.data).__root__

    async def stream_update(
        self: JetstreamClient,
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
        **kwargs: Any,
    ) -> IoNatsJetstreamApiV1StreamUpdateResponse:
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
        return IoNatsJetstreamApiV1StreamUpdateResponse.parse_raw(msg.data).__root__

    async def stream_delete(
        self: JetstreamClient, name: str, timeout: float = 0.5
    ) -> IoNatsJetstreamApiV1StreamDeleteResponse:
        msg: Msg = await self.request(
            f"$JS.API.STREAM.DELETE.{name}", b"", timeout=timeout
        )
        return IoNatsJetstreamApiV1StreamDeleteResponse.parse_raw(msg.data).__root__
