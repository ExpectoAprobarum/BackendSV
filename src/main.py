from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.views import games


app = FastAPI()

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST","GET","PUT"],
    allow_headers=["*"],
)


@app.get('/')
def index():
    return {'app_name' : 'Secret Voldemort', 'version' : '1.0'} 

app.include_router(games.router, prefix="/games")
