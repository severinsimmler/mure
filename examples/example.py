import mure
from mure.iterator import LOGGER
from mure.models import Resource

LOGGER.set_level("DEBUG")

resources: list[Resource] = [
    {"url": "https://google.com"},
    {"url": "https://youtube.com"},
    {"url": "https://facebook.com"},
    {"url": "https://instagram.com"},
    {"url": "https://twitter.com"},
    {"url": "https://baidu.com"},
    {"url": "https://wikipedia.org"},
    {"url": "https://yahoo.com"},
    {"url": "https://yandex.ru"},
    {"url": "https://whatsapp.com"},
]


for i, _ in enumerate(mure.get(resources, batch_size=5)):
    print(f"Received response {i}")
