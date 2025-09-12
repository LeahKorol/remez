from fastapi import FastAPI
from routers import pipeline

app = FastAPI(
    title="Pipeline API",
    description="Runs Dr. Gorelik's pipeline via FastAPI",
    version="0.1.0",
)

# Include the pipeline router
app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
