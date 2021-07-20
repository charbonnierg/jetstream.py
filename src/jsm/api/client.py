from nats.aio.client import Client as NC

from .consumers import ConsumersMixin
from .infos import AccountInfosMixin
from .streams import StreamsMixin


class Client(NC, AccountInfosMixin, ConsumersMixin, StreamsMixin):
    pass
