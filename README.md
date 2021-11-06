----
**NOTICE**

There is alpha JetStream support in latest [nats.py](https://github.com/nats-io/nats.py). The package is now called `nats-py`: `pip install nats-py`.
This library won't be maintained in the future.

If you still wish to use this library, beware that it will break with `nats-server>=2.6`
-----------------

# `jetstream.py` - Jetstream Client for Asyncio

An asyncio Python3 client for [Jetstream enabled NATS servers](https://docs.nats.io/jetstream/jetstream).

## Supported platforms

Should be compatible with at least Python >= 3.8.

This library also tries to be friendly with `mypy` and `vscode` python extension.

## Installing

At the moment, only installation from source or wheel is supported. This can easily be done using `pip`:

- Install using `pip` and git repo URL

```bash
pip install git+https://github.com/charbonnierg/jetstream.py.git@next
```

- Or you can add `jetstream.py` as a project dependency using `poetry`:

```bash
poetry add git+https://github.com/charbonnierg/jetstream.py@next
```

> Note: In both cases, you can specify a different branch or tag name in the git URL after the `@` character instead of default `next`

- Or install a release directly from wheel archive:

```bash
pip install "https://github.com/charbonnierg/jetstream.py/releases/download/v0.1.0/jetstream_python-0.1.0-py3-none-any.whl"
```

## Basic usage

```python
from jsm.api.client import Client as JS


async def run():
    # You can optionally specify a js domain using "domain" keyword argument
    js = JS(domain=None)

    # This is the connect method from _nats.aio.client.Client class
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

    # Publish a message that will be routed to the consumer, string headers are supported
    await js.publish("test.demo", b"hola", headers={"foo": "bar"})

    # Publish a message and wait for acknowledgement
    # Returns a PubAck instance: PubAck(stream='TEST', seq=2, domain=None, duplicate=None)
    ack = await js.stream_publish("test.demo", b"hello")
    # You can access each field as an attribute
    assert ack.stream == "TEST"

    # Fetch the next message from the consumer and automatically acknowledge it
    msg = await js.consumer_msg_next("TEST", "test-app-01", auto_ack=True)
    assert msg.data == b"hola"

    # Iterate over messages and acknowledge them automatically
    async for msg in js.consumer_pull_msgs("TEST", "test-app-01", max_msgs=1):
        print(msg.data)
```

## Example Notebooks

Two examples notebooks are available:

- [01-streams.ipynb](https://github.com/charbonnierg/jetstream.py/blob/next/examples/01-streams.ipynb): Demonstrate how to work with streams

- [02-consumers.ipynb](https://github.com/charbonnierg/jetstream.py/blob/next/examples/02-consumers.ipynb): Demonstrate how to work with consumers

## Features

### Misc

- Use a custom domain
- Allow default timeout configuration
- Allow default error handling configuration (raise error or return error response)

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

### Key/Value Store

- Create a bucket
- Put key value in bucket
- Read key value from bucket
- Read whole key history from bucket
- Delete a bucket

## Client implementation

JetStream API methods are implemented under several mixins located in [jsm.api](./src/jsm/api) submodule.

- a JetStream API method often has an associated `request` pydantic model
- a JetStream API method always has an associated `response` pydantic model
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
        offset: int = 0,
        timeout: float = 0.5,
        # By default error are never raised
        raise_on_error: bool = False,
        # Both return types inherit at some point from pydantic.BaseModel
    ) -> Union[
        # Method can either return a StreamListResponse
        IoNatsJetstreamApiV1StreamListResponse,
        # Or an error
        IoNatsJetstreamApiV1ErrorResponse
    ]:
        # First gather options as an instance of pydantic.BaseModel child class
        options = IoNatsJetstreamApiV1StreamListRequest(offset=offset)
        # Send a request using helper method
        return await self._jetstream_request(
            # Specify subject without prefix
            "STREAM.LIST",
            # Specify options
            options,
            # Specify response validator using generic JetstreamResponse can custom model
            JetStreamResponse[IoNatsJetstreamApiV1StreamListResponse],
            # Optionally raise on error
            raise_on_error=raise_on_error,
            timeout=timeout,
        )
```

[`JetStreamResponse`](https://github.com/charbonnierg/jetstream.py/blob/next/src/jsm/api/mixins/request_reply.py#L15) is a `pydantic.generics.GenericModel` used to either parse an error, or a response according to the type given as argument.

## References

- Jetstream NATS API Reference: <https://docs.nats.io/jetstream/nats_api_reference>

## About model generation

A first attempt was made to generate `pydantic` models from [`JSON Schemas` files](https://github.com/nats-io/jsm.go/tree/v0.0.25/schemas/jetstream) using [`datamodel-code-generator`](https://github.com/koxudaxi/datamodel-code-generator), sadly the generated files were not valid or complete.

A script is available in `build-tools/` repository to generate models automatically. Run the following command to generate the files:

```bash
python build-tools/generate_models.py
```

Files in [`jsm.models`](./src/jsm/models) were first generated using `datamodel-code-generator` but several manual modidications were required.

## Tools & Libraries

Thanks to all maintainers and contributors of the following projects:

- [nats.py](https://github.com/nats-io/nats.py) provides the client to interact with NATS servers.

- [pydantic](https://pydantic-docs.helpmanual.io/) is used for data validation, serizalization and deserialization.

- [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) was used to generate `pydantic` models.

- [poetry](https://python-poetry.org/) is used to manage the project as a python package.

- [flake8](https://github.com/PyCQA/flake8) is used to lint the code.

- [black](https://github.com/psf/black) is used to format the code.

- [isort](https://github.com/PyCQA/isort) is used to format and sort imports.
