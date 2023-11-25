from redis.asyncio.client import Redis as aioredis

redis = aioredis(host='redis', port=6379, db=0, decode_responses=True)
