from fastapi import FastAPI, Depends
from functools import lru_cache
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from app.power_model.price_model import get_price_day_ahead, get_price_day_ahead_split_nok
from datetime import datetime, timedelta
import auth

from config import Settings, get_settings

# Use Python 3.10 and above
# use >uvicorn main:app --reload 


# api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
# api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


app = FastAPI()

# Open Route
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Lockedown Route
# API_KEY comes with parameter or header access_token
@app.get("/day_ahead_today")
async def day_ahead(api_key: APIKey = Depends(auth.get_api_key), vat:bool=True, nettleie:bool=False):
    """_summary_

    Args:
        api_key (APIKey, optional): _description_. Defaults to Depends(auth.get_api_key).
        vat (bool, optional): _description_. Defaults to True.
        nettleie (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """

    today = datetime.today().strftime('%Y%m%d')
    dt_tom = datetime.today() + timedelta(days=2)  # last day is not included in request
    tomorrow = dt_tom.strftime('%Y%m%d')

    # serves today and tomorrow prices with vat in nok.
    if vat and nettleie:
        data = get_price_day_ahead(today, tomorrow, vat=True, vat_rate=0.25, nettleie=True).reset_index()
    elif vat and not nettleie:
        data = get_price_day_ahead(today, tomorrow, vat=True, vat_rate=0.25, nettleie=False).reset_index()
    else:
        data = get_price_day_ahead(today, tomorrow, vat=False, nettleie=False).reset_index()
        
    data.columns = ['date','price']
    return data.to_json(orient='records', date_format='iso')


@app.get("/day_ahead_today_split")
async def day_ahead_details(api_key: APIKey = Depends(auth.get_api_key)):
    """_summary_

    Args:
        api_key (APIKey, optional): _description_. Defaults to Depends(auth.get_api_key).
    """

    today = datetime.today().strftime('%Y%m%d')
    dt_tom = datetime.today() + timedelta(days=2)  # last day is not included in request
    tomorrow = dt_tom.strftime('%Y%m%d')

    data = get_price_day_ahead_split_nok(today, tomorrow, vat_rate=0.25).reset_index()

    return data.to_json(orient='records', date_format='iso')


