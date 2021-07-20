from __future__ import annotations

from typing import TYPE_CHECKING, Union

from nats.aio.client import Msg

from jsm.models.v1.api.account_info_response import (
    IoNatsJetstreamApiV1AccountInfoResponse,
    IoNatsJetstreamApiV1AccountInfoResponse1,
    IoNatsJetstreamApiV1AccountInfoResponseItem,
    IoNatsJetstreamApiV1AccountInfoResponseItem1,
)

if TYPE_CHECKING:
    from .client import JetstreamClient


class AccountInfosMixin:
    async def account_infos(
        self: JetstreamClient, timeout: float = 0.5
    ) -> Union[
        IoNatsJetstreamApiV1AccountInfoResponse1,
        IoNatsJetstreamApiV1AccountInfoResponseItem,
        IoNatsJetstreamApiV1AccountInfoResponseItem1,
    ]:
        msg: Msg = await self.request("$JS.API.INFO", payload=b"", timeout=timeout)
        return IoNatsJetstreamApiV1AccountInfoResponse.parse_raw(msg.data).__root__
