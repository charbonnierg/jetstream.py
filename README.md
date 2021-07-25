# `jetstream.py` -  Jetstream Client for Asyncio

An asyncio Python3 client for [Jetstream enabled NATS servers](https://docs.nats.io/jetstream/jetstream).

## Supported platforms

Should be compatible with at least Python >= 3.8.

This library also tries to be friendly with `mypy` and `vscode` python extension.

## Installing

At the moment, only installation from source is supported. This can easily be done using `pip`:


```bash
pip install git+https://github.com/charbonnierg/jetstream.py.git@next
```

Or you can add `jetstream.py` as a project dependency using `poetry`:

```bash
poetry add git+https://github.com/charbonnierg/jetstream.py@next
```

> Note: In both cases, you can specify a different branch or tag name in the git URL after the `@` character instead of default `next`

## Basic usage

```python
from jsm.api.client import Client as JS


async def run():
    js = JS()

    # This is the connect method from nats.aio.client.Client class
    await js.connect()

    # Request account info
    await js.account_info()

    # Request stream names
    await js.stream_names()

    # Request streams
    await js.stream_list()

    # Create a stream
    await js.stream_create("TEST", subjects=["test.>"])

    # Create a consumer
    await js.consumer_create("TEST", "test-app-01")

    # Publish a message that will be routed to the consumer
    await js.publish("test.demo", b"hola")

    # Fetch the next message from the consumer and automatically acknowledge it
    msg = await js.consumer_msg_next("TEST", "test-app-01", auto_ack=True)
    assert msg.data == b"hola"
```


## Features

### Account Info

- Get account info

### Streams

- List streams
- List stream names
- Create a stream
- Read stream info
- Update stream
- Delete stream
- Purge stream
- Get stream message
- Delete stream message

### Consumers

- Create a consumer
- Read consumer info
- Delete a consumer
- Get consumer next message
- Iterate over consumer messages


## Client implementation

JetStream API methods are implemented under several mixins located in [jsm.api](./src/jsm/api) submodule.

- a JetStream API method often has an associated `request` pydantic model
- a JetStream API method always has an associated  `response` pydantic model
- a JetStream API method is invoked by sending a request to a specific subject, as described in JetStream NATS API Reference.

Python methods implemented under each mixin roughly follow the same pattern:

1. Create a `request` pydantic model using the arguments given by user
2. Send an NATS request to the JetStream API on expected subject
3. Receive and parse the message received into a valid JetStream API `response`
4. Optionally check if the response is a JetStream error and raise a python exception accordingly
5. Return the parsed response

Take the `$JS.API.STREAMS.LIST` method for example:

```python
 async def stream_list(
        self,
        timeout: float = 0.5,
        offset: int = 0,
        # By default error are never raised
        raise_on_error: bool = False,
        # Both return types inherit at some point from pydantic.BaseModel
    ) -> Union[
        # Method can either return a StreamListResponse
        IoNatsJetstreamApiV1StreamListResponse, 
        # Or an error
        IoNatsJetstreamApiV1ErrorResponse
    ]:
        # First gather options
        options = IoNatsJetstreamApiV1StreamListRequest(offset=offset)
        # Send a request to expected subject
        msg: Msg = await self.request(
            "$JS.API.STREAM.LIST",
            # Send the request options as utf-8 encoded JSON
            payload=options.json().encode("utf-8"),
            timeout=timeout,
        )
        # Parse JetStream response
        response = IoNatsJetstreamApiV1Response[
            IoNatsJetstreamApiV1StreamListResponse
        ].parse_raw(msg.data)
        # Optionally check for error and raise error accordingly
        if raise_on_error:
            response.raise_on_error()
        # Return parsed response
        return response.__root__
```

[`IoNatsJetstreamApiV1Response`](https://github.com/charbonnierg/jetstream.py/blob/next/src/jsm/models/base.py#L28) is a `pydantic.generics.GenericModel` used to either parse an error, or a response according to the type given as argument.


## References

- Jetstream NATS API Reference: <https://docs.nats.io/jetstream/nats_api_reference>

## About model generation

A first attempt was made to generate `pydantic` models from [`JSON Schemas` files](https://github.com/nats-io/jsm.go/tree/v0.0.25/schemas/jetstream), sadly the generated files were not valid or complete.

A script is available in `build-tools/` repository to generate models automatically. Run the following command to generate the files:

```bash
python build-tools/generate_models.py
```


Files in [`jsm.models`](./src/jsm/models) submodule are mostly copy/pasted from automatically generated models with a few manual modifications.

## Tools & Libraries

Thanks to all maintainers and contributors of the following projects:

- [nats.py](https://github.com/nats-io/nats.py) provides the client to interact with NATS servers.

- [pydantic](https://pydantic-docs.helpmanual.io/) is used for data validation, serizalization and deserialization.

- [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) was used to generate `pydantic` models.

- [poetry](https://python-poetry.org/) is used to manage the project as a python package.

- [flake8](https://github.com/PyCQA/flake8) is used to lint the code.

- [black](https://github.com/psf/black) is used to format the code.

- [isort](https://github.com/PyCQA/isort) is used to format and sort imports.
