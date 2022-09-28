import pandas as pd
import requests
from entsoe import EntsoePandasClient

# Move API key and URL to config secrets
URL_NOK = 'https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP?format=sdmx-json&lastNObservations=1&locale=no'
API_KEY='acf71bdf-69df-460d-8d08-68fcbce55337'

# Create region dictionnary
REGION = '10YNO-2--------T' # Norway NO2
time_zone = 'Europe/Oslo'



def get_price_day_ahead(start_day:str, end_day:str, val:str='NOK', vat:bool=True, vat_rate:float=0.25):
    """Load prices day ahead from Entsoe in val/kWh

    Args:
        start_day (str): first day to be downloaded (YYYMMDD)
        end_day (str): Last day to be downloaded not included (YYYYMMDD)
        val (str, optional): Currency code. As of today, EUR or NOK. Defaults to 'NOK'.
        vat (bool, optional): Add VAT. If true, must enter vat rate. Defaults to True.
        vat_rate (float, optional): VAT rate to be added. Defaults to 0.25.

    Raises:
        ValueError: check currency code.

    Returns:
       pd.Series: datetime index, power price val/kWh
    """

    prices = get_price_day_ahead_EUR(start_day, end_day)

    # Prices returned in Euro. Load exchange rate
    if val == 'NOK':
        exch_rate, _ = get_last_NOK_exchange_rate()
    elif val == 'EUR':
        exch_rate = 1.0
    else:
        raise ValueError(f'{val} currency is unknown')

    prices_kwh = prices*exch_rate

    # add VAT if requested
    if vat:
        prices_kwh = prices_kwh*(1.0 + vat_rate)

    prices_kwh.columns = ['price_kwh']

    return prices_kwh


# add cache (10 min) to avoid multiple queries
def get_price_day_ahead_EUR(start_day: str, end_day: str):
    """_summary_

    Args:
        start_day (str): _description_
        end_day (str): _description_

    Returns:
        _type_: _description_
    """
    try:
        start = pd.Timestamp(start_day, tz=time_zone)
        end = pd.Timestamp(end_day, tz=time_zone)
    except ValueError:
        print(f'parameters are string convertible to pandas TimeStamp. Received parameters are {start_day} and {end_day}')
        raise
    except Exception:
        raise
    
    # Create Entsoe client
    clientpd = EntsoePandasClient(API_KEY)
    region = REGION 

    # load prices EUR/MWh --> EUR/kWh
    df = clientpd.query_day_ahead_prices(region, start=start, end=end) / 1000

    return df


def get_last_NOK_exchange_rate():
    """_summary_

    Returns:
        _type_: _description_
    """
    # Get NOK/EUR latest exchange rate - Move to another function
    response = requests.get(URL_NOK)
    jj = response.json()

    exch_rate = float(jj['data']['dataSets'][0]['series']['0:0:0:0']['observations']['0'][0])
    exch_rate_time = pd.to_datetime(jj['meta']['prepared'], utc=True).tz_convert('Europe/Oslo')

    return exch_rate, exch_rate_time