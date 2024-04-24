import mure
from mure.cache import MemoryCache
from mure.iterator import LOGGER
from mure.models import Resource

LOGGER.set_level("DEBUG")

cache = MemoryCache()

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


for i, _ in enumerate(mure.get(resources, batch_size=5, cache=cache)):
    print(f"Received response {i}")

# super fast, because responses are cached
for i, _ in enumerate(mure.get(resources, batch_size=5, cache=cache)):
    print(f"Received response {i}")
