from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.donors import router as donors_router

app = FastAPI(title="Donor Finder API")

# Allow local Next.js and any dev tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(donors_router, prefix="/donors")
