from helpers import is_float
from history import _get_statistic, _get_history

from datetime import datetime, timedelta
"""
@time_trigger("startup",
              "cron(*/5 * * * *)")
def estimate_power_usage(var_name="sensor.nygardsvegen_6_strom_forbruk_per_time"):
    now = datetime.now()

    # get some sampling data first
    if now.minute in range(0, 4): return

    usage = float(state.get(var_name))
    per_minute = usage / now.minute
    estimated = round(per_minute * 60, 2)

    state.set('sensor.estimated_hourly_consumption',
              value=estimated,
              new_attributes={'state_class': 'total',
                              'unique_id': 'sensor.estimated_hourly_consumption123',
                              'device_class': 'energy',
                              'icon': 'mdi:transmission-tower-import',
                              'unit_of_measurement': 'kWh'})
"""
@time_trigger("startup")
@state_trigger("sensor.nordpool_kwh_trheim_nok_3_00_0")
def energy_price_with_tarif(value=None):
    """ Calculate the energy price including tarif costs """
    value = float(sensor.nordpool_kwh_trheim_nok_3_00_0)
    now = datetime.now()

    if value > 0.89:
        value = ((value - 0.89) * 0.1) + 0.89

    if now.month in range(0, 2): # jan, feb, march
        tarif_price = 0.3020 if now.hour in range(6, 21) else 0.2145
    else:
        tarif_price = 0.3855 if now.hour in range(6, 21) else 0.2980

    price = round(tarif_price + value, 3)

    state.set('sensor.energy_price_with_tarif',
              value=price,
              new_attributes={'state_class': 'total', 
                              'device_class': 'monetary',
                              'icon': 'mdi:currency-usd',
                              'unit_of_measurement': 'NOK/kWh'})
"""
@time_trigger("startup",
              "cron(0 * * * *)")
def estimate_electricity_cost(value=None):
    now = datetime.now()
    days_in_month = (datetime(now.year, now.month + 1, 1) - datetime(now.year, now.month, 1)).days
    days_passed = (now - datetime(now.year, now.month, 1)).days + 1

    estimate = (float(sensor.nygardsvegen_6_strom_kost_per_maned) / days_passed) * days_in_month
    state.set('sensor.estimated_electricity_cost',
              value=round(estimate, 3),
              new_attributes={'state_class': 'total',
                              'device_class': 'monetary',
                              'icon': 'mdi:currency-usd',
                              'unit_of_measurement': 'NOK'})

@time_trigger("startup",
              "cron(0 * * * *)")
def energy_top_3_month():
    peak_energy_usage = str()
    top_three = state.getattr('sensor.energy_level_upper_threshold').get('top_three')
    options = state.getattr('input_select.energy_tariff').get('options')

    top_three = sorted([k.get('energy') for k in top_three], key=float, reverse=True)
    avg_top_three = sum(top_three) / len(top_three)

    nearest_above_avg = [int(x) for x in options if int(x) >= avg_top_three]
    nearest_above_avg = min(nearest_above_avg)

    for hour in top_three:
        hour = round(hour, 3)
        peak_energy_usage = f"{peak_energy_usage}, {hour}" if peak_energy_usage else str(hour)

    peak_energy_usage += f" (avg {round(avg_top_three, 3)})"

#    if nearest_above_avg > float(input_select.energy_tariff):
#        state.set('input_select.energy_tariff', value=nearest_above_avg)

    state.set('input_text.peak_energy_usage', value=peak_energy_usage)

@time_trigger("startup",
              "cron(0 * * * *)")
def calc_avg_energy_price():
    nordpool_sensor = "sensor.nordpool_kwh_trheim_nok_3_00_0"

    start_time = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    now_time = datetime.today()
    price_data = _get_history(start_time, now_time, [nordpool_sensor])
    prices = [float(d.state) for d in price_data.get(nordpool_sensor) if is_float(d.state)]

    avg_price = sum(prices) / len(prices)

    state.set('sensor.electricity_avarage_cost',
              value=round(avg_price, 2),
              new_attributes={'state_class': 'total', 
                              'device_class': 'monetary',
                              'icon': 'mdi:currency-usd',
                              'unit_of_measurement': 'NOK'})"""