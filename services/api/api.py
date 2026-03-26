from fastapi import FastAPI
from endpoints import router
import debug


if debug.in_debug_mode():
    app = FastAPI()
else:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    
app.include_router(router)
