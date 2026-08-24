from fastapi import Depends,FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .ai import refine_with_ai
from .auth import optional_identity
from .config import settings
from .infrastructure import infra
from .models import RefineRequest,RefineResponse,SearchRequest
from .parser import refine_with_rules

app=FastAPI(title="Copart Conversational Search API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["GET","POST"],allow_headers=["Authorization","Content-Type"])

@app.get("/health")
async def health():return {"status":"ok"}

@app.post("/v1/search/refine",response_model=RefineResponse)
async def refine(request:RefineRequest,_identity:str|None=Depends(optional_identity)):
    current=await infra.load_session(request.session_id) if request.session_id else None
    parsed=await refine_with_ai(request.query,current or request.current_filters)
    filters=parsed or refine_with_rules(request.query,current or request.current_filters)
    if request.session_id:await infra.save_session(request.session_id,filters)
    return RefineResponse(filters=filters,source="nvidia" if parsed else "rules")

@app.post("/v1/vehicles/search")
async def search(request:SearchRequest,_identity:str|None=Depends(optional_identity)):
    return {"vehicles":await infra.search_inventory(request.filters,request.limit)}
