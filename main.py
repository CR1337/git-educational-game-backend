from fastapi import FastAPI
from routers import root, levels, games, files, git, editor

app = FastAPI()

# Include all routers
app.include_router(root.router)
app.include_router(levels.router)
app.include_router(games.router)
app.include_router(files.router)
app.include_router(git.router)
app.include_router(editor.router)
