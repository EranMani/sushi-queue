from fastapi import FastAPI

# Create a FastAPI app
app = FastAPI(title="Sushi Queue", description="Async sushi order backend")

@app.get("/")
def root():
    return {"message": "Sushi Queue API"}
