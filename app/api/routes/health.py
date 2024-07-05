import fastapi

router = fastapi.APIRouter()


@router.get("/health")
def health_check():
    return {"status": "App is healthy"}
