
from cachetools import TTLCache

app_cache = TTLCache(maxsize=10, ttl=600)
