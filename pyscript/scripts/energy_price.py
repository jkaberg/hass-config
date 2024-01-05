import requests
from datetime import datetime, timezone, timedelta


def find_current_hour(prices, time):
    for hour in prices:
        if hour["time_start"] <= time < hour["time_end"]:
            return hour

    return None

def calc_price(value, time):
    # based on: https://ts.tensio.no/kunde/nettleie-priser-og-avtaler
    support_price = 0.9125

    if value > support_price:
        value = ((value - support_price) * 0.1) + support_price

    if time.month in range(0, 2): # jan, feb, march
        tarif_price = 0.3020 if time.hour in range(6, 21) else 0.2145
    else:
        tarif_price = 0.3855 if time.hour in range(6, 21) else 0.2980

    return round(tarif_price + value, 3)

def mark_price(data, time_window, direction='lowest'):
    max_cost = float('-inf')
    pos = 0

    for i in range(len(data) - time_window + 1):
        window = data[i:i + time_window]
        total_cost = 0

        for entry in window:
            total_cost += entry["price_with_tarif"]

        if (direction == 'lowest' and total_cost < max_cost) or (direction == 'highest' and total_cost > max_cost):
            max_cost = total_cost
            pos = i

    for i, entry in enumerate(data):
        entry[f'is_{time_window}_{direction}'] = pos <= i < pos + time_window

    return data

@time_trigger("startup", "once(14:00)")
def fetch_prices(zone='NO3'):
    prices = []
    now = datetime.now(timezone.utc)
    price_windows = [4, 8]
    next_day = now + timedelta(days=1)
    urls = [
        f'https://www.hvakosterstrommen.no/api/v1/prices/{now.year}/{now.month:02d}-{now.day:02d}_{zone}.json',
        f'https://www.hvakosterstrommen.no/api/v1/prices/{now.year}/{now.month:02d}-{next_day.day:02d}_{zone}.json',
    ]

    for url in urls:
        tmp_prices = []
        ret = task.executor(requests.get, url)

        if ret.status_code == 200:
            for entry in ret.json(): # day for day
                price = entry.get('NOK_per_kWh')
                time_start = datetime.fromisoformat(entry.get('time_start'))
                time_end = datetime.fromisoformat(entry.get('time_end'))
                price_with_tarif = calc_price(price, time_start)

                tmp_prices.append({'price': price,
                                   'price_with_tarif': price_with_tarif,
                                   'time_start': time_start,
                                   'time_end': time_end})

        # find the lowest and highest (price) windows for the current day
        # this means these windows wont traverse into the next day
        for window in price_windows:
            tmp_prices = mark_price(tmp_prices, window, 'lowest')
            tmp_prices = mark_price(tmp_prices, window, 'highest')

        prices.extend(tmp_prices)

    current_hour = find_current_hour(prices, now)

    attrs = {
        'unique_id': 'sensor.energy_price',
        'device_class': 'monetary',
        'icon': 'mdi:currency-usd',
        'unit_of_measurement': 'NOK/kWh',
        'updated': now,
        'prices': prices
        }

    state.set(
        'sensor.energy_price',
        value=current_hour['price_with_tarif'],
        new_attributes={**current_hour, **attrs},
    )

@time_trigger("startup", "cron(0 * * * *)")
@state_active("sensor.energy_price.prices is not None")
def setup_sensors():
    current_time = datetime.now(timezone.utc)
    hour = find_current_hour(sensor.energy_price.prices, current_time)

    # create individual sensors for these        
    for key in [key for key in hour if key.endswith(('_lowest', '_highest'))]:
        state.set(
            f'sensor.energy_{key}',
            value='on' if hour[key] == True else 'off',
            new_attributes={
                'unique_id': f'sensor.energy_{key}',
                'object_id': f'sensor.energy_{key}',
                'device_class': 'total',
                'icon': 'mdi:transmission-tower-import'
            },
        )

    # update the main sensor attrs
    state.set(f'sensor.energy_price', value=hour['price_with_tarif'])

    for key, value in hour.items():
        state.setattr(f'sensor.energy_price.{key}', hour[key])