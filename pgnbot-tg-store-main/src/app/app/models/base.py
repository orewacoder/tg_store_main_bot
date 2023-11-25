from pydantic import BaseModel
from app.db.mongodb import engine


class DBModel(BaseModel):

    _collection = None

    async def save(self):
        await engine[self._collection].find_one_and_update(
            {"_id": self.id},
            {"$set": self.model_dump()},
            upsert=True
        )
