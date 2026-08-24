from typing import Literal
from pydantic import BaseModel, Field, field_validator

Sort = Literal["best","price-asc","price-desc","miles","newest","oldest"]

class Filters(BaseModel):
    vehicleTypes:list[str]=[]; makes:list[str]=[]; excludedMakes:list[str]=[]; models:list[str]=[]
    series:list[str]=[]; bodies:list[str]=[]; vehicleClasses:list[str]=[]
    minYear:int|None=None; maxYear:int|None=None; minPrice:int|None=None; maxPrice:int|None=None
    minMiles:int|None=None; maxMiles:int|None=None; states:list[str]=[]; fuels:list[str]=[]
    transmissions:list[str]=[]; drives:list[str]=[]; titles:list[str]=[]; damages:list[str]=[]
    excludedDamages:list[str]=[]; colors:list[str]=[]; engines:list[str]=[]; cylinders:list[int]=[]
    restraintSystems:list[str]=[]; manufacturedIn:list[str]=[]; sort:Sort="best"

    @field_validator("minYear","maxYear")
    @classmethod
    def valid_year(cls,value:int|None):
        if value is not None and not 1900 <= value <= 2035: raise ValueError("year out of range")
        return value

    @field_validator("minPrice","maxPrice","minMiles","maxMiles")
    @classmethod
    def non_negative(cls,value:int|None):
        if value is not None and value < 0: raise ValueError("value must be non-negative")
        return value

class RefineRequest(BaseModel):
    query:str=Field(min_length=1,max_length=500)
    current_filters:Filters=Field(default_factory=Filters)
    session_id:str|None=Field(default=None,max_length=128)

class RefineResponse(BaseModel):
    filters:Filters
    source:Literal["rules","nvidia"]

class SearchRequest(BaseModel):
    filters:Filters=Field(default_factory=Filters)
    limit:int=Field(default=50,ge=1,le=100)
