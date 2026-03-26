from contextlib import asynccontextmanager
from fastapi import FastAPI
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
    app = FastAPI(
        lifespan=lifespan,
        docs_url=None, 
        redoc_url=None, 
        openapi_url=None
    )


app.include_router(router)


