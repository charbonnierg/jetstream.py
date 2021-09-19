from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from pydantic.generics import GenericModel

from jsm.models.base import BaseResponse
from jsm.models.errors import IoNatsJetstreamApiV1ErrorResponse
from nats.aio.client import Msg

ResponseItemT = TypeVar("ResponseItemT", bound=BaseResponse)


class JetStreamResponse(GenericModel, Generic[ResponseItemT]):
    __root__: Union[IoNatsJetstreamApiV1ErrorResponse, ResponseItemT]

    def raise_on_error(self) -> None:
        """Raise an error if the response if a JetstreamApiError."""
        self.__root__.raise_on_error()


ResponseT = TypeVar("ResponseT", bound=JetStreamResponse[BaseModel])


class BaseJetStreamRequestReplyMixin:

    _prefix: str
    _raise_on_error: bool
    _timeout: float

    async def _jetstream_request(
        self,
        subject: str,
        model: Optional[BaseModel],
        response: Type[JetStreamResponse[ResponseT]],
        raise_on_error: Optional[bool] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> ResponseT:
        # First encode payload if necessary
        if model:
            payload = model.json().encode("utf-8")
        # Or create empty payload
        else:
            payload = b""
        # Use default timeout value
        if timeout is None:
            timeout = self._timeout
        # Send message to jetstream
        # msg: Msg = await self._nc.request(
        msg: Msg = await self.request(  # type: ignore[attr-defined]
            f"{self._prefix}.{subject}", payload=payload, timeout=timeout, **kwargs
        )
        # Parse message from bytes
        js_response: ResponseT = response.parse_raw(msg.data).__root__
        # Optionally raise on error because keyword argument "raise_on_error" is True
        if raise_on_error:
            js_response.raise_on_error()
        # Or because "self._raise_on_error" is True and "raise_on_error" is not False
        elif raise_on_error is None:
            if self._raise_on_error:
                js_response.raise_on_error()
        # Return the response
        return js_response
