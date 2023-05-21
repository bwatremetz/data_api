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
    """ Get total prices fortoday and tomorrow

    Args:
        api_key (APIKey, optional): _description_. Defaults to Depends(auth.get_api_key).
        vat (bool, optional): Add VAT to the price. Defaults to True.
        nettleie (bool, optional): add nettleie to the price. Defaults to False.

    Returns:
        JSON string: prices vs time for today and tomorrow with specified details
    """

    today = datetime.now().strftime('%Y%m%d')
    dt_tom = datetime.now() + timedelta(days=2)  # last day is not included in request
    tomorrow = dt_tom.strftime('%Y%m%d')

    # serves today and tomorrow prices with vat in nok.
    if vat and nettleie:
        data = get_price_day_ahead(today, tomorrow, vat=True, vat_rate=0.25, nettleie=True).reset_index()
    elif vat:
        data = get_price_day_ahead(today, tomorrow, vat=True, vat_rate=0.25, nettleie=False).reset_index()
    else:
        data = get_price_day_ahead(today, tomorrow, vat=False, nettleie=False).reset_index()
        
    data.columns = ['date','price']
    return data.to_json(orient='records', date_format='iso')


@app.get("/day_ahead_today_split")
async def day_ahead_details(api_key: APIKey = Depends(auth.get_api_key)):
    """Get day ahead detailled prices for today and tomorrow (with vat and nettleie)

    Args:
        api_key (APIKey, optional): API key. Defaults to Depends(auth.get_api_key).
    """

    today = datetime.now().strftime('%Y%m%d')
    dt_tom = datetime.now() + timedelta(days=2)  # last day is not included in request
    tomorrow = dt_tom.strftime('%Y%m%d')

    data = get_price_day_ahead_split_nok(today, tomorrow, vat_rate=0.25).reset_index()
    data.columns = ['date','net_price', 'vat', 'nettleie']

    return data.to_json(orient='records', date_format='iso')


@app.get("/day_ahead_period_split")
async def day_ahead_period_details(start_day:str, end_day:str, api_key: APIKey = Depends(auth.get_api_key)):
    """Get day ahead detailled prices for a given period (with vat and nettleie)

    Args:
        start_day: first day of the period, format yyyymmdd
        end_day: last day of the period, format yyyymmdd
        api_key (APIKey, optional): API key. Defaults to Depends(auth.get_api_key).
    """

    data = get_price_day_ahead_split_nok(start_day=start_day, end_day=end_day, vat_rate=0.25).reset_index()
    data.columns = ['date','net_price', 'vat', 'nettleie']

    return data.to_json(orient='records', date_format='iso')