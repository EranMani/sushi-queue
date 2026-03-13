from fastapi import FastAPI
from contextlib import asynccontextmanager

"""
VISUAL EXPLANATION: The Restaurant's Daily Routine
------------------------------------------------
# The lifespan function centralizes our startup and shutdown logic in one place.
# Without lifespan: We turn on the ovens when the first customer arrives and never turn them off (causing crashes).
# With lifespan: We prep properly before opening, and safely shut down everything at night.
"""

# THE MANAGER'S CLIPBOARD (@asynccontextmanager):
# This decorator turns a simple generator into a strict, unbreakable routine. 
# It guarantees to FastAPI that the closing shift will run safely no matter what.
# (app: FastAPI) is the master keys
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- MORNING PREP (Before yield) ---
    # Staff arrives, turns on ovens, and preps the kitchen.
    # Code here runs ONCE at startup: connect to DB, Redis, or warm up caches.
    print("Turning on the ovens... (Starting connections)")
    
    # --- OPEN FOR BUSINESS (The yield) ---
    # The 'yield' is the pause button. We flip the sign to "OPEN".
    # The lifespan function waits in the background while the app serves customers.
    yield 
    
    # --- CLOSING TIME (After yield) ---
    # The server is shutting down. The yield unpauses.
    # Staff turn off ovens and lock doors: safely disconnect from DB/Redis.
    print("Locking the doors... (Closing connections safely)")

# Create a FastAPI app
app = FastAPI(title="Sushi Queue", description="Async sushi order backend", lifespan=lifespan)

@app.get("/")
def root():
    return {"message": "Sushi Queue API"}
