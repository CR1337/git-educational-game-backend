from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from endpoints import router
import debug
import events


@asynccontextmanager
async def lifespan(app: FastAPI):
    events.startup()
    yield
    events.shutdown()


if debug.in_debug_mode():
    app = FastAPI(lifespan=lifespan)

else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including OPTIONS
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router)


@app.middleware("http")
async def log_request_body(request: Request, call_next):
    body = await request.body()
    print("Raw request body:", body.decode())
    return await call_next(request)
