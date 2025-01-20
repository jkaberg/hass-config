
import pytz
from datetime import datetime, date, timedelta, timezone

def current_time():
    dt = datetime.now()
    tz = pytz.timezone('Europe/Oslo')
    return tz.localize(dt)

def find_current_hour(prices, time):
    for hour in prices:
        if hour["start"].hour == time.hour and hour["start"].day == time.day:
            return hour

    return None

def calculate_min_max(prices):
    min_price = min([hour['price'] for hour in prices])
    max_price = max([hour['price'] for hour in prices])
    avg_price = sum([hour['price'] for hour in prices]) / len(prices)

    return round(min_price, 3), round(max_price, 3), round(avg_price, 3)

def calculate_price_with_tarif(start=None, price=None):
    # https://www.tensio.no/no/kunde/nettleie/nettleiepriser-for-privat
    # Alle priser i NOK
    # Regner ut den totale prisen per time per kWh

    price = (price / 1000) # Konvertere øre til NOK, ingen MVA

    # Terskelverdi strømstøtte
    treshold = 0.75 # Ingen MVA

    # Strømstøtte
    if price > treshold:
        price = (((price - treshold) * 0.1) + treshold) * 1.25
    else:
        price *= 1.25

    # Energiledd
    if start.hour in range(6, 22):
        tarif_price = 0.4249
    else:
        tarif_price = 0.2786

    return round(price + tarif_price, 3)

def calculate_percentage_price(prices=[]):
    min_price, max_price, avg_price = calculate_min_max(prices)

    for hour in prices:
        hour['percentage'] = round((hour['price'] - min_price) / (max_price - min_price) * 100, 1)

    return prices

def get_prices_for_date(date=None, config_entry='01JJ08RM9X31QJP5KTMWNCJNEM', area="NO3", currency="NOK"):
    data = []
    tz = pytz.timezone('Europe/Oslo')

    if not date:
        return data

    try:
        result = nordpool.get_prices_for_date(
            config_entry = config_entry,
            date = date,
            areas = area,
            currency = currency
        )
    except: #  ServiceValidationError: Nord Pool has not posted market prices for the provided date
        return data

    if not result:
        return data

    for hour in result[area]:
        h = {}
        h['start'] = datetime.fromisoformat(hour.get('start')).astimezone(tz)
        h['price'] = calculate_price_with_tarif(h['start'], hour.get('price'))

        data.append(h)

    return data

@service
@time_trigger("startup", "once(14:00)")
def energy_price_sensor():
    now = current_time()
    next_day = now + timedelta(days=1)

    today = get_prices_for_date(now.strftime("%Y-%m-%d"))
    tomorrow = get_prices_for_date(next_day.strftime("%Y-%m-%d"))
    all_prices = calculate_percentage_price(today + tomorrow)
 
    current_hour = find_current_hour(all_prices, now)
    min_price, max_price, avg_price = calculate_min_max(all_prices)

    attrs = {
        'unique_id': 'sensor.energy_price',
        'device_class': 'monetary',
        'icon': 'mdi:currency-usd',
        'unit_of_measurement': 'NOK/kWh',
        'updated': now,
        'prices': all_prices,
        'avg_price': avg_price,
        'max_price': max_price,
        'min_price': min_price
        }

    state.set(
        'sensor.energy_price',
        value=current_hour['price'],
        new_attributes={**current_hour, **attrs},
    )

@time_trigger("startup", "cron(0 * * * *)")
@state_active("sensor.energy_price.prices is not None")
def update_energy_price():
    hour = find_current_hour(sensor.energy_price.prices, current_time())

    state.set(f'sensor.energy_price', value=hour['price'])

    for key, value in hour.items():
        state.setattr(f'sensor.energy_price.{key}', value)