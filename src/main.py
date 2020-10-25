from fastapi import FastAPI
from src.views import games
app = FastAPI()

@app.get('/')
def index():
    return {'app_name' : 'Secret Voldemort', 'version' : '1.0'} 

app.include_router(games.router, prefix="/games")
