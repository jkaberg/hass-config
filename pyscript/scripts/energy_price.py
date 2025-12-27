import pytz
from datetime import datetime, date as date_type, timedelta, timezone

OSLO_TZ = pytz.timezone('Europe/Oslo')
PEAK_HOURS = range(6, 22)
SUPPORT_THRESHOLD = 0.75  # NOK per kWh before reimbursement kicks in
SUPPORT_RATE = 0.1
VAT_FACTOR = 1.25
TARIFF_PEAK = 0.4249
TARIFF_OFFPEAK = 0.2786

SENSOR_ENTITY_ID = 'sensor.energy_price'


def current_time():
    return datetime.now(timezone.utc).astimezone(OSLO_TZ)

def find_current_hour(prices, time, *, assume_sorted=False):
    entries = prices if assume_sorted else normalize_price_entries(prices)

    if not entries:
        return None

    for entry in entries:
        start = entry['start']
        if start <= time < start + timedelta(hours=1):
            return entry

    past_hours = [entry for entry in entries if entry['start'] <= time]
    if past_hours:
        return past_hours[-1]

    return entries[0]

def calculate_min_max(prices):
    values = [hour['price'] for hour in prices]
    min_price = min(values)
    max_price = max(values)
    avg_price = sum(values) / len(values)
    
    return round(min_price, 3), round(max_price, 3), round(avg_price, 3)
    
def calculate_price_with_tarif(start=None, price=None):
    # https://www.tensio.no/no/kunde/nettleie/nettleiepriser-for-privat
    # Alle priser i NOK
    # Regner ut den totale prisen per time per kWh

    if start is None or price is None:
        log.warning("calculate_price_with_tarif: missing start or price, skipping entry")
        return None

    try:
        price = float(price)
    except (TypeError, ValueError):
        log.warning("calculate_price_with_tarif: invalid raw price '%s'", price)
        return None

    price = price / 1000  # Konvertere øre til NOK, ingen MVA

    # Strømstøtte
    if price > SUPPORT_THRESHOLD:
        price = ((price - SUPPORT_THRESHOLD) * SUPPORT_RATE + SUPPORT_THRESHOLD) * VAT_FACTOR
    else:
        price *= VAT_FACTOR

    # Energiledd
    if start.hour in PEAK_HOURS:
        tarif_price = TARIFF_PEAK
    else:
        tarif_price = TARIFF_OFFPEAK

    return round(price + tarif_price, 3)
    
def calculate_percentage_price(prices):
    by_day = {}

    for hour in prices:
        by_day.setdefault(hour['start'].date(), []).append(hour)

    for day_prices in by_day.values():
        values = [entry['price'] for entry in day_prices]
        day_min = min(values)
        day_max = max(values)
        price_range = day_max - day_min

        for entry in day_prices:
            if price_range > 0:
                entry['percentage'] = round((entry['price'] - day_min) / price_range * 100, 1)
            else:
                entry['percentage'] = 0

    return prices


def ensure_datetime(value):
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            normalized_value = value.replace('Z', '+00:00') if value.endswith('Z') else value
            return datetime.fromisoformat(normalized_value)
        except ValueError:
            log.warning("energy_price_sensor: unable to parse datetime string '%s'", value)
            return None

    log.warning("energy_price_sensor: unexpected start value type '%s'", type(value))
    return None


def normalize_price_entries(prices):
    if not isinstance(prices, (list, tuple)):
        return []

    normalized = []

    for entry in prices:
        if not isinstance(entry, dict):
            continue

        start = ensure_datetime(entry.get('start'))
        if not start:
            continue

        price = entry.get('price')
        try:
            price = float(price)
        except (TypeError, ValueError):
            log.warning("energy_price_sensor: invalid price value '%s' skipped", price)
            continue

        normalized_entry = dict(entry)
        normalized_entry['start'] = start
        normalized_entry['price'] = price
        normalized.append(normalized_entry)

    normalized.sort(key=lambda item: item['start'])
    return normalized


def prices_include_date(prices, target_date):
    for entry in prices:
        start = entry.get('start')
        if isinstance(start, datetime) and start.date() == target_date:
            return True
    return False


def date_key(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date_type):
        return value.strftime("%Y-%m-%d")
    return str(value)


def set_sensor_state(prices, now, *, already_normalized=False):
    normalized_prices = prices if already_normalized else normalize_price_entries(prices)

    if not normalized_prices:
        return False

    current_hour = find_current_hour(normalized_prices, now, assume_sorted=True)
    if not current_hour:
        log.warning("energy_price_sensor: no matching hour found for %s", now)
        return False

    min_price, max_price, avg_price = calculate_min_max(normalized_prices)

    attrs = {
        'unique_id': SENSOR_ENTITY_ID,
        'device_class': 'monetary',
        'icon': 'mdi:currency-usd',
        'unit_of_measurement': 'NOK/kWh',
        'updated': now,
        'prices': normalized_prices,
        'avg_price': avg_price,
        'max_price': max_price,
        'min_price': min_price,
    }

    state.set(SENSOR_ENTITY_ID, value=current_hour['price'], new_attributes={**current_hour, **attrs})

    return True

def get_prices_for_date(target_date=None, config_entry='01JJ08RM9X31QJP5KTMWNCJNEM', area="NO3", currency="NOK"):
    data = []
    tz = OSLO_TZ
    
    if not target_date:
        return data

    if isinstance(target_date, datetime):
        date_string = target_date.strftime("%Y-%m-%d")
    elif isinstance(target_date, date_type):
        date_string = target_date.strftime("%Y-%m-%d")
    else:
        date_string = str(target_date)
    
    try:
        result = nordpool.get_prices_for_date(
            config_entry = config_entry,
            date = date_string,
            areas = area,
            currency = currency
        )
    except: #  ServiceValidationError: Nord Pool has not posted market prices for the provided date
        return data
    
    if not result:
        return data

    day_prices = result.get(area)

    if not day_prices:
        return data
    
    for hour in day_prices:
        start_time = datetime.fromisoformat(hour.get('start')).astimezone(tz)
        price_with_tarif = calculate_price_with_tarif(start_time, hour.get('price'))

        if price_with_tarif is None:
            continue

        data.append({
            'start': start_time,
            'price': price_with_tarif,
        })

    data.sort(key=lambda entry: entry['start'])

    return data

@service
@time_trigger("startup", "cron(0 * * * *)")
def refresh_energy_price():
    now = current_time()
    today_date = now.date()
    tomorrow_date = (now + timedelta(days=1)).date()

    try:
        existing_prices = state.getattr(SENSOR_ENTITY_ID).get('prices') #sensor.energy_price.prices
    except AttributeError:
        existing_prices = []

    normalized_prices = normalize_price_entries(existing_prices) if existing_prices else []

    prices_by_date = {}
    for entry in normalized_prices:
        entry_date = entry['start'].date()
        if entry_date < today_date:
            continue
        prices_by_date.setdefault(entry_date, []).append(entry)

    missing_today = today_date not in prices_by_date
    missing_tomorrow = tomorrow_date not in prices_by_date

    if missing_today:
        fresh_today = get_prices_for_date(today_date)
        if fresh_today:
            prices_by_date[today_date] = fresh_today
        else:
            log.warning(
                "energy_price_sensor: today's prices (%s) unavailable; will retry on next trigger",
                date_key(now),
            )

    if missing_tomorrow:
        fresh_tomorrow = None

        if now.hour >= 13: # prices usually available after 13:00
            fresh_tomorrow = get_prices_for_date(tomorrow_date)

            if fresh_tomorrow:
                prices_by_date[tomorrow_date] = fresh_tomorrow
            else:
                log.info(
                    "energy_price_sensor: tomorrow's prices (%s) not available yet",
                    date_key(tomorrow_date),
                )

    if today_date not in prices_by_date:
        log.info("energy_price_sensor: price data unavailable; sensor unchanged")
        return False

    combined_prices = []
    for day in sorted(prices_by_date.keys()):
        day_entries = sorted(prices_by_date[day], key=lambda entry: entry['start'])
        combined_prices.extend(day_entries)

    combined_with_percentages = calculate_percentage_price(combined_prices)
    normalized_combined = normalize_price_entries(combined_with_percentages)

    set_sensor_state(normalized_combined, now, already_normalized=True)
    return True
