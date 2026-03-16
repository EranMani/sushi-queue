from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.routes import auth, menu
from app.core.redis import get_redis, close_redis

"""
THE DAILY ROUTINE (Lifespan)
Safely handles startup (prep) and shutdown (closing) to prevent resource crashes.
@asynccontextmanager guarantees this routine runs unbroken.
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # MORNING PREP (Before yield): Runs ONCE at startup to open connections.
    await get_redis()
    
    # OPEN FOR BUSINESS (yield): The app pauses here to serve customers.
    yield 
    
    # CLOSING TIME (After yield): Safely disconnects resources on shutdown.
    await close_redis()

# Create a FastAPI app
app = FastAPI(title="Sushi Queue", description="Async sushi order backend", lifespan=lifespan)
app.include_router(auth.router, prefix="/api")
app.include_router(menu.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Sushi Queue API"}
