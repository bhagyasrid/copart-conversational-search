from opensearchpy._async.client import AsyncOpenSearch
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine,create_async_engine
from .config import settings
from .models import Filters

class Infrastructure:
    """Lazy production clients; startup remains healthy when optional services are absent."""
    def __init__(self):
        self.database:AsyncEngine=create_async_engine(settings.database_url,pool_pre_ping=True)
        self.redis=Redis.from_url(settings.redis_url,decode_responses=True)
        self.search=AsyncOpenSearch(hosts=[settings.opensearch_url])

    async def load_session(self,session_id:str)->Filters|None:
        try:
            value=await self.redis.get(f"conversation:{session_id}")
            return Filters.model_validate_json(value) if value else None
        except Exception:return None

    async def save_session(self,session_id:str,filters:Filters)->None:
        try:await self.redis.setex(f"conversation:{session_id}",3600,filters.model_dump_json())
        except Exception:pass

    async def search_inventory(self,filters:Filters,limit:int=50)->list[dict]:
        clauses=[]
        for field,values in (("make.keyword",filters.makes),("body.keyword",filters.bodies),("state.keyword",filters.states),("fuel.keyword",filters.fuels),("drive.keyword",filters.drives)):
            if values:clauses.append({"terms":{field:values}})
        ranges={"year":(filters.minYear,filters.maxYear),"price":(filters.minPrice,filters.maxPrice),"miles":(filters.minMiles,filters.maxMiles)}
        for field,(minimum,maximum) in ranges.items():
            bounds={**({"gte":minimum} if minimum is not None else {}),**({"lte":maximum} if maximum is not None else {})}
            if bounds:clauses.append({"range":{field:bounds}})
        response=await self.search.search(index="vehicles",body={"size":limit,"query":{"bool":{"filter":clauses}}})
        return [hit["_source"] for hit in response["hits"]["hits"]]

infra=Infrastructure()
