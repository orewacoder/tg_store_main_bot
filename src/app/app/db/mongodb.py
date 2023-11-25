from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
# from odmantic import AIOEngine, SyncEngine
from app.core.config import settings

# Sync Engine
# engine = SyncEngine(settings.MONGO_URI, database=settings.MONGO_DB)
# aioengine = AIOEngine(settings.MONGO_URI, database=settings.MONGO_DB)

client = AsyncIOMotorClient(settings.MONGO_URI)
engine = client[settings.MONGO_DB]

sync_client = MongoClient(settings.MONGO_URI)
sync_engine = sync_client[settings.MONGO_DB]
