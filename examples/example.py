import mure
from mure.cache import Cache
from mure.iterator import LOGGER
from mure.models import Resource

LOGGER.set_level("DEBUG")


resources: list[Resource] = [
    {"url": "https://google.com"},
    {"url": "https://youtube.com"},
    {"url": "https://facebook.com"},
    {"url": "https://instagram.com"},
    {"url": "https://wikipedia.org"},
    {"url": "https://wikidata.org"},
    {"url": "https://whatsapp.com"},
]

print("START FIRST RUN")
for i, response in enumerate(mure.get(resources, batch_size=5, cache=Cache.FILE)):
    LOGGER.info(f"Received response {i} from {response.url}: {response.status}")

print("\nSTART SECOND RUN")
# super fast, because responses are cached
for i, response in enumerate(mure.get(resources, batch_size=5, cache=Cache.FILE)):
    LOGGER.info(f"Received response {i} from {response.url}: {response.status}")
