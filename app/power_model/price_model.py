import pandas as pd
import requests
from entsoe import EntsoePandasClient
from config import Settings, get_settings
from cachetools import TTLCache, cached

# Move API key and URL to config secrets
URL_NOK = 'https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP?format=sdmx-json&lastNObservations=1&locale=no'

# Create region dictionnary
REGION = '10YNO-2--------T' # Norway NO2
time_zone = 'Europe/Oslo'   # localize the data in given timezone


def get_price_day_ahead(start_day:str, end_day:str, val:str='NOK', vat:bool=True, vat_rate:float=0.25, nettleie:bool=True)->pd.Series:
    """Load prices day ahead from Entsoe in val/kWh

    Args:
        start_day (str): first day to be downloaded (YYYMMDD)
        end_day (str): Last day to be downloaded not included (YYYYMMDD)
        val (str, optional): Currency code. As of today, EUR or NOK. Defaults to 'NOK'.
        vat (bool, optional): Add VAT. If true, must enter vat rate. Defaults to True.
        vat_rate (float, optional): VAT rate to be added. Defaults to 0.25.
        nettleie (bool, optional): add nettleie to the price (vat always included). Defaults to True

    Raises:
        ValueError: check currency code.

    Returns:
       pd.Series: datetime index, unlocolazied timezone, power price val/kWh
    """

    # Prices returned in Euro. Load exchange rate
    if val == 'NOK':
        prices_kwh = get_price_day_ahead_split_nok(start_day, end_day, vat_rate=vat_rate)
    elif val == 'EUR':
        raise ValueError('EUR not implemented yet')
    else:
        raise ValueError(f'{val} currency is unknown')

    # Calculate gross price as requested

    prices = prices_kwh['net_prices']

    # add VAT if requested
    if vat:
        prices = prices + prices_kwh['vat']

    # add nettleie if requested
    if nettleie:
        prices = prices + prices_kwh['nettleie']

    return prices


def get_price_day_ahead_split_nok(start_day:str, end_day:str, vat_rate:float):
    """returns all parts of electricity prices day ahead in dataframes columns

    Args:
        start_day (str): first day in yyyymmdd format
        end_day (str): last day in yyyymmdd (not included)
        vat_rate (float): vat rate for vat calculation

    Returns:
        pd.dataframe: dataframe index (time) = datetime - unlocalized timezone, columns [net_prices, vat, nettleie]
    """

    # Get EUR prices
    prices = get_price_day_ahead_EUR(start_day, end_day)
    prices = prices.reset_index()
    prices.columns = ['time', 'price_EUR']
    prices['date'] = prices['time'].dt.normalize().dt.tz_localize(None)

    # Get exchange rates
    exch_rate= get_NOK_exchange_rate(start_day, end_day)
    exch_rate = exch_rate.reset_index()
    exch_rate.columns = ['date', 'ex_rate']

    # get net prices in a dataframe by merging on dates
    prices = prices.merge(right=exch_rate, on='date')
    prices['price_NOK'] = prices['price_EUR']*prices['ex_rate']

    # get vat
    prices['vat'] = prices['price_NOK']*vat_rate

    prices = prices[['time', 'price_NOK', 'vat']].copy()
    prices = prices.rename(columns={'price_NOK': 'net_prices'})

    # remove timezone from datetie object
    prices['time'] = prices['time'].dt.tz_localize(None)

    # get nettleie
    prices['nettleie'] = get_nettleie(prices['time'].dt.hour)

    return prices.set_index('time')


@cached(cache=TTLCache(maxsize=1024, ttl=600))     # cache data for 10min
def get_price_day_ahead_EUR(start_day: str, end_day: str):
    """Return power prices from ENTSOE in EUR/kWh

    Args:
        start_day (str): start date format yyyymmdd @ 00:00
        end_day (str): end date format yyyymmdd @ 23:00

    Returns:
        pd.Series: price in EUR/kWh. Index datetime with timezone
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
    clientpd = EntsoePandasClient(get_settings().ENTSOE_API_KEY)
    region = REGION 

    # load prices EUR/MWh --> EUR/kWh
    return clientpd.query_day_ahead_prices(region, start=start, end=end) / 1000


# @cached(cache=TTLCache(maxsize=1024, ttl=600)) 
def get_NOK_exchange_rate(start_day:str, end_day:str)->pd.Series:
    """Get daily EUR/NOK exchange rate between 2 dates

    Args:
        start_day (str): start date format yyyymmdd @ 00:00
        end_day (str): end date format yyyymmdd @ 00:00

    Returns:
        pd.Series: exchange rate, date index
    """

    try:
        start = pd.Timestamp(start_day, tz=time_zone).date()
        end = pd.Timestamp(end_day, tz=time_zone).date()
    except ValueError:
        print(f'parameters are string convertible to pandas TimeStamp. Received parameters are {start_day} and {end_day}')
        raise
    except Exception:
        raise
    
    URL_temp = f'https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP?startPeriod={start.isoformat()}&endPeriod={end.isoformat()}&format=sdmx-json&locale=no'
    response = requests.get(URL_temp)

    if response.status_code == 200: 
        jj = response.json()

        # exchange rates
        ex = jj['data']['dataSets'][0]['series']['0:0:0:0']['observations']
        ex = pd.DataFrame(ex).astype(float).T.reset_index()

        # dates
        ids = pd.DataFrame(jj['data']['structure']['dimensions']['observation'][0]['values']).reset_index()
        ids['id'] = pd.to_datetime(ids['id'])

        # concat
        ex = pd.concat([ids,ex], axis=1).drop(columns=['index', 'start', 'end', 'name'])
        ex.columns=['date', 'ex_rate']

        # get potential missing dates (start / end of the vector)
        vec = pd.DataFrame(index=pd.date_range(start, end, freq='D'))
        vec = pd.concat([vec, ex.set_index('date')], axis=1)
        vec = vec.fillna(method='ffill').fillna(method='bfill')

    else:
        # Get last available code and deliver a constant vector
        exch_rate, _ = get_last_NOK_exchange_rate()
        vec = pd.DataFrame(index=pd.date_range(start, end, freq='D'))
        vec['ex_rate'] = exch_rate

    return vec


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



def get_nettleie(hour)->float:
    """Return nettleie in nok depending on time

    Prices 2022
    Energiledd dag	kl. 06:00 - kl.22:00	52,51 øre/kWh
    Energiledd natt	kl. 22:00 - kl. 06:00	42,51 øre/kWh

    Args:
        hour (int or pd.Series of int): hour of the day

    Returns:
        float / pd.Series: nettleie in nok / kWh
    """

    if isinstance(hour, pd.Series):
        return hour.apply(nettleie)
    else:
        return nettleie(hour)


def nettleie(hour:int)->float:
    """returns nettleie vs hour in nok

    Args:
        hour (int): hour of the day

    Returns:
        float: nettleie in nok
    """
    if hour<6 or hour>=22:
        return 42.51 / 100
    else:
        return 52.51 / 100

