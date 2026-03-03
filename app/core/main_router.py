from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "Healthy yayy!"}
