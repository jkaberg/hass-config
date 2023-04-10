from helpers import is_float
from history import _get_statistic, _get_history

from datetime import datetime, timedelta


@time_trigger("startup",
              "cron(*/5 * * * *)")
def estimate_power_usage(var_name="sensor.nygardsvegen_6_strom_forbruk_per_time"):
    """ Estimate power usage for the current hour """
    now = datetime.now()

    # get some sampling data first
    if now.minute in range(0, 4): return

    usage = float(state.get(var_name))
    per_minute = usage / now.minute
    estimated = round(per_minute * 60, 2)

    state.set('sensor.estimated_hourly_consumption',
              value=estimated,
              new_attributes={'state_class': 'total', 
                              'device_class': 'energy',
                              'icon': 'mdi:transmission-tower-import',
                              'unit_of_measurement': 'kWh'})

@time_trigger("startup")
@state_trigger("sensor.nordpool_kwh_trheim_nok_3_00_0")
def energy_price_with_tarif(value=None):
    """ Calculate the energy price including tarif costs """
    value = float(sensor.nordpool_kwh_trheim_nok_3_00_0)
    now = datetime.now()

    if now.month in range(0, 2): # jan, feb, march
        if now.hour in range(6, 21):
            tarif_price = 0.3020 # winter day
        else:
            tarif_price = 0.2145 # winter night
    else:
        if now.hour in range(6, 21):
            tarif_price = 0.3855 # summer day
        else:
            tarif_price = 0.2980 # summer night

    price = round(tarif_price + value, 3)

    state.set('sensor.energy_price_with_tarif',
              value=price,
              new_attributes={'state_class': 'total', 
                              'device_class': 'monetary',
                              'icon': 'mdi:currency-usd',
                              'unit_of_measurement': 'NOK/kWh'})

@time_trigger("startup",
              "cron(0 * * * *)")
def estimate_electricity_cost(value=None):
    """ Estimate the energy cost for the current month based on previous usage """
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
    """ Calculate the top 3 energy consumption hours for current month """
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
    """ Calculate the avarage energy price for the current month """
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
                              'unit_of_measurement': 'NOK'})

@time_trigger("startup")
@state_trigger("sensor.nygardsvegen_6_strom_forbruk_per_dag")
def unknown_energy_consumption():
    now_time = datetime.today()
    start_time = now_time.replace(hour=0, minute=0, second=0)
    my_var_name = 'sensor.unknown_energy_consumption'

    def get_today_stat(sensor_name):
        values = _get_history(start_time, now_time, [sensor_name]).get(sensor_name)
        return float(values[-1].state) - float(values[0].state)

    energy_sensors = [k.get('stat_consumption') for k in hass.data['energy_manager'].data.get('device_consumption')]
    energy_values = sum([get_today_stat(x) for x in energy_sensors if not x == my_var_name])
    difference = float(sensor.nygardsvegen_6_strom_forbruk_per_dag) - energy_values

    state.set(my_var_name,
              value=difference,
              new_attributes={'friendly_name': 'Ukjent forbruk',
                              'state_class': 'total',
                              'device_class': 'energy',
                              'icon': 'mdi:chart-line-variant',
                              'unit_of_measurement': 'kWh'})