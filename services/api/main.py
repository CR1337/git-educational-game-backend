from fastapi import FastAPI
from routers import root, git
from services.api.routers import filesystem, game, level

app = FastAPI()

# Include all routers
app.include_router(root.router)
app.include_router(level.router)
app.include_router(game.router)
app.include_router(filesystem.router)
app.include_router(git.router)
