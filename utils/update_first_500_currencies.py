import requests, json
from home.models import currency


all_currencies = currency.objects.all()

symbols = [c.symbol for c in all_currencies[:500]]
symbols = ','.join(symbols)
response = requests.get(f'https://api.nomics.com/v1/currencies/ticker?key=e46fab48a3538b1ec642482aaa54fb68&ids={symbols}&interval=1d,7d')
currencies_info = json.loads(response.content.decode().replace('\n', ''))
for cur_info in currencies_info:
    try:
        cur = currency.objects.get(symbol=cur_info['id'])
        cur.price = cur_info['price']
        cur.daily_price_change_pct = float(cur_info['1d']['price_change_pct'])*100
        cur.weekly_price_change_pct = float(cur_info['7d']['price_change_pct'])*100
        cur.save()
    except:
        pass