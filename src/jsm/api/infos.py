from __future__ import annotations

from typing import TYPE_CHECKING, Union

from nats.aio.client import Msg

from jsm.models.account_info import IoNatsJetstreamApiV1AccountInfoResponse
from jsm.models.base import IoNatsJetstreamApiV1Response
from jsm.models.errors import IoNatsJetstreamApiV1ErrorResponse

if TYPE_CHECKING:
    from .client import Client


class AccountInfosMixin:
    async def account_info(  # type: ignore[misc]
        self: Client,
        timeout: float = 0.5,
        raise_on_error: bool = False,
    ) -> Union[
        IoNatsJetstreamApiV1AccountInfoResponse,
        IoNatsJetstreamApiV1ErrorResponse,
    ]:
        msg: Msg = await self.request("$JS.API.INFO", payload=b"", timeout=timeout)
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1AccountInfoResponse
        ].parse_raw(msg.data)
        if raise_on_error:
            response.raise_on_error()
        return response.__root__
