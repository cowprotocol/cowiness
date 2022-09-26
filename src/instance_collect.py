import os

import requests
from dotenv import load_dotenv

load_dotenv()

def fetch_order(oid):
    orderbook_url = os.getenv('ORDERBOOK_URL')
    url = orderbook_url + f'/api/v1/orders/{oid}'
    return requests.get(url).json()
