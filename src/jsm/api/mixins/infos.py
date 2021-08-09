from __future__ import annotations

from typing import Optional, Union

from jsm.models.account_info import IoNatsJetstreamApiV1AccountInfoResponse
from jsm.models.errors import IoNatsJetstreamApiV1ErrorResponse

from .request_reply import BaseJetStreamRequestReplyMixin, JetStreamResponse


class AccountInfosMixin(BaseJetStreamRequestReplyMixin):
    async def account_info(
        self,
        timeout: Optional[float] = None,
        raise_on_error: Optional[bool] = None,
    ) -> Union[
        IoNatsJetstreamApiV1AccountInfoResponse,
        IoNatsJetstreamApiV1ErrorResponse,
    ]:
        return await self._jetstream_request(
            "INFO",
            None,
            JetStreamResponse[IoNatsJetstreamApiV1AccountInfoResponse],
            raise_on_error=raise_on_error,
            timeout=timeout,
        )
