import pandas as pd
import requests
from entsoe import EntsoePandasClient

URL_NOK = 'https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP?format=sdmx-json&lastNObservations=1&locale=no'

def get_price_day_ahead():
    # Move API key to config secrets
    clientpd = EntsoePandasClient(api_key='acf71bdf-69df-460d-8d08-68fcbce55337')

    start = pd.Timestamp('20220806', tz='Europe/Oslo')
    end = pd.Timestamp('20220809', tz='Europe/Oslo')
    region=  '10YNO-2--------T'

    df = clientpd.query_day_ahead_prices(region, start=start, end=end)

    # Get NOK/EUR latest exchange rate - Move to another function
    response = requests.get(URL_NOK)
    jj = response.json()

    exch_rate = float(jj['data']['dataSets'][0]['series']['0:0:0:0']['observations']['0'][0])
    exch_rate_time = pd.to_datetime(jj['meta']['prepared'], utc=True).tz_convert('Europe/Oslo')

    # Split and add parameters
    df_nok_kwh_vat = df*exch_rate/1000*1.25

    # reset_index and set columns
    df_nok_kwh_vat = df_nok_kwh_vat.reset_index()
    df_nok_kwh_vat.columns = ['date', 'price']

    return df_nok_kwh_vat