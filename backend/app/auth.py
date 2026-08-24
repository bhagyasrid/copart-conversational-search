from fastapi import Header,HTTPException
from jose import JWTError,jwt
from .config import settings

async def optional_identity(authorization:str|None=Header(default=None))->str|None:
    if not authorization:return None
    if not authorization.startswith("Bearer "):raise HTTPException(401,"Invalid authorization scheme")
    try:
        claims=jwt.decode(authorization[7:],settings.jwt_secret,algorithms=["HS256"],audience=settings.jwt_audience,issuer=settings.jwt_issuer)
        return str(claims["sub"])
    except (JWTError,KeyError) as exc: raise HTTPException(401,"Invalid access token") from exc
