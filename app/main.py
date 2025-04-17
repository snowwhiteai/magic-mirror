from fastapi import FastAPI
import uvicorn
from app.core.logging import setup_logging
from app.api import health

setup_logging()

app = FastAPI(title="Magic Mirror Service")

# Health check endpoint
app.include_router(health.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
