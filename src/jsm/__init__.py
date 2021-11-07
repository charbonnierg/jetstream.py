# Copyright 2021 - Guillaume Charbonnier
# Licensed under the Apache License, Version 2.0 (the "License");
# http://www.apache.org/licenses/LICENSE-2.0
#
from typing import Any, List, Optional, Union

from jsm.api.client import Client as JS


async def connect(
    servers: Union[str, List[str]] = ["nats://localhost:4222"],
    domain: Optional[str] = None,
    default_timeout: float = 1.0,
    raise_on_error: bool = False,
    **options: Any
) -> JS:
    if isinstance(servers, str):
        servers = [servers]
    js = JS(domain, default_timeout, raise_on_error)
    await js.connect(**options)
    return js
