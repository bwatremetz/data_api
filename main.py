from fastapi import FastAPI
from app.power_model.price_model import get_price_day_ahead

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/day_ahead")
async def day_ahead():
    data = get_price_day_ahead()
    return data.to_json(orient='records', date_format='iso')
