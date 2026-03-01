from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.skillproof.database import init_db
from src.skillproof.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


Path("certificates").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)
Path("corrections").mkdir(exist_ok=True)

app = FastAPI(title="SkillProof", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/certificates", StaticFiles(directory="certificates"), name="certificates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/corrections", StaticFiles(directory="corrections"), name="corrections")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
