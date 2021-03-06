# Copyright 2021 - Guillaume Charbonnier
# Licensed under the Apache License, Version 2.0 (the "License");
# http://www.apache.org/licenses/LICENSE-2.0
from _nats.aio.errors import NatsError


class ErrSubscriptionNotStarted(NatsError):
    def __str__(self) -> str:
        return "nats: Subscription is not started yet"


class JetStreamError(NatsError):
    def __init__(self, description: str, code: int, type: str) -> None:
        super().__init__(description)
        self.code = code
        self.description = description
        self.type = type

    def __str__(self) -> str:
        return f"{self.type}: {self.description} (status_code={self.code})"
