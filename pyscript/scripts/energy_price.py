import requests
from datetime import datetime, timezone, timedelta

@service
def fetch_prices(zone='NO3'):
    prices = []
    current_price = None
    now = datetime.now()
    next_day = now + timedelta(days=1)
    urls = [
        f'https://www.hvakosterstrommen.no/api/v1/prices/{now.year}/{now.month:02d}-{now.day:02d}_{zone}.json',
        f'https://www.hvakosterstrommen.no/api/v1/prices/{now.year}/{now.month:02d}-{next_day.day:02d}_{zone}.json',
    ]

    key_mapping = {
        "NOK_per_kWh": "price",
        "time_start": "time_start",
        "time_end": "time_end",
    }

    for url in urls:
        log.debug(url)
        ret = task.executor(requests.get, url)

        if ret.status_code == 200:
            for entry in ret.json():
                price = {
                    key_mapping.get(key, key): value
                    for key, value in entry.items()
                    if key not in ["EUR_per_kWh", "EXR"]
                }
                prices.append(price)

                entry_start = datetime.fromisoformat(entry["time_start"])
                entry_end = datetime.fromisoformat(entry["time_end"])
                current_time = datetime.now(timezone.utc)

                if entry_start <= current_time < entry_end:
                    current_price = entry["NOK_per_kWh"]

    state.set(
        'sensor.energy_price',
        value=current_price,
        new_attributes={
            'unique_id': 'sensor.energy_price',
            'device_class': 'monetary',
            'icon': 'mdi:transmission-tower-import',
            'unit_of_measurement': 'NOK/kWh',
            'prices': prices,
        },
    )