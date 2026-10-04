from fastapi import FastAPI

from app.modules.identity.api.authentication import router as authentication_router


app = FastAPI(
    title="Beauty SaaS API",
    version="0.1.0",
)


app.include_router(authentication_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}