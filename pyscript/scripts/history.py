from datetime import datetime, timezone, timedelta

from history import _get_statistic, _get_history

decorated_functions = {}

@time_trigger("startup")
@time_trigger("cron(0 * * * *)")
def energy_top_3_month(var_name="sensor.nygardsvegen_6_forbruk"):
    start_time = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    end_time = datetime.today()
    peak_energy_usage = str()
    options = state.getattr('input_select.energy_tariff').get('options')

    statistics = _get_statistic(start_time, end_time, [var_name], "hour", 'state')
    top_three = sorted(statistics.get(var_name), key=lambda d: d['state'], reverse=True)[:3]

    avg_top_three = [d['state'] for d in top_three]
    avg_top_three = sum(avg_top_three) / len(top_three)

    nearest_above_avg = [int(x) for x in options if int(x) >= avg_top_three]
    nearest_above_avg = min(nearest_above_avg)

    for hour in top_three:
        peak_energy_usage = f"{peak_energy_usage}, {hour.get('state')}" if peak_energy_usage else str(hour.get('state'))

    peak_energy_usage += f" (avg {round(avg_top_three, 3)})"

    state.set('input_select.energy_tariff', value=nearest_above_avg)
    state.set('input_text.peak_energy_usage', value=peak_energy_usage)

@time_trigger("startup")
@time_trigger("cron(0 * * * *)")
def calc_energy_price():
    energy_sensor = "sensor.nygardsvegen_6_forbruk"
    nordpool_sensor = "sensor.nordpool_kwh_trheim_nok_3_00_0"
    capacity_tarif = {2: 83, 5: 147, 10: 252, 15: 371, 20: 490, 25: 610, 50: 1048}

    def is_float(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    start_time = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    now_time = datetime.today()
    consumption_data = _get_statistic(start_time, now_time, [energy_sensor], "hour", 'state')
    price_data = _get_history(start_time, now_time, [nordpool_sensor])
    prices = [float(d.state) for d in price_data.get(nordpool_sensor) if is_float(d.state)]

    cut_off = 0.7
    avg_price = sum(prices) / len(prices)

    our_price = 0
    state_price = 0
    tarif_price = 0
    consumption = 0

    for d in consumption_data.get(energy_sensor):
        consumption_dt = d.get('start')
        try:
            consumption += d.get('state')
        except:
            pass

        for p in price_data.get(nordpool_sensor):
            price_dt = p.last_changed
            if consumption_dt.day == price_dt.day and consumption_dt.hour == price_dt.hour:
                try:
                    price = float(p.state)
                except ValueError:
                    continue

                # https://ts.tensio.no/kunde/nettleie-priser-og-avtaler
                if price_dt.month in range(0, 2): # jan, feb, march
                    if price_dt.hour in range(6, 21):
                        tarif_price = 0.3020 # winter day
                    else:
                        tarif_price = 0.2145 # winter night
                else:
                    if price_dt.hour in range(6, 21):
                        tarif_price = 0.3855 # summer day
                    else:
                        tarif_price = 0.2980 # summer night

                tarif_price *= 0.75 # remove VAT, we add it later.

                if avg_price > cut_off:
                    our_price += (((((price - cut_off) * 0.1) + cut_off) + tarif_price) * 1.25) * d.get('state')
                    state_price += ((price - cut_off) * 0.9) * d.get('state')
                else:
                    our_price += ((price + tarif_price) * 1.25) * d.get('state')

                #log.debug(our_price)

    # add capacity tarif
    our_price += capacity_tarif.get(int(input_select.energy_tariff))

    attrs = {'state_class': 'total', 
             'device_class': 'monetary',
             'icon': 'mdi:currency-usd',
             'unit_of_measurement': 'NOK'}

    state.set('sensor.electricity_avarage_cost', value=round(avg_price, 2), new_attributes=attrs)
    state.set('sensor.electricity_cost', value=round(our_price, 2), new_attributes=attrs)
    state.set('sensor.electricity_consumption', value=round(consumption, 2), new_attributes={'state_class': 'total', 
                                                                                             'device_class': 'energy',
                                                                                             'icon': 'mdi:transmission-tower-import',
                                                                                             'unit_of_measurement': 'kWh'})
    state.set('sensor.electricity_cost_state', value=round(state_price, 2), new_attributes=attrs)

@state_trigger("sensor.electricity_cost")
#@time_trigger("cron(*/1 * * * *)")
def estimate_electricity_cost(value=None):
    capacity_tarif = {2: 83, 5: 147, 10: 252, 15: 371, 20: 490, 25: 610, 50: 1048}
    value = float(state.get('sensor.electricity_cost'))
    now = datetime.now()
    days_in_month = (datetime(now.year, now.month + 1, 1) - datetime(now.year, now.month, 1)).days
    days_passed = (now - datetime(now.year, now.month, 1)).days + 1
    remaining_days = days_in_month - days_passed

    attrs = {'state_class': 'total', 
             'device_class': 'monetary',
             'icon': 'mdi:currency-usd',
             'unit_of_measurement': 'NOK'}

    if now.day in range (0,13): # "fix" bad starting calculations, eg very big estimates.
        value -= capacity_tarif.get(int(input_select.energy_tariff))

    estimate = value + remaining_days * value / days_passed
    state.set('sensor.estimated_electricity_cost', value=round(estimate, 2), new_attributes=attrs)

@time_trigger("startup")
async def correct_bad_readings():
    global decorated_functions

    decorated_functions = {}

    # fetch all sensors listed in the energy dashboard
    sensors = [k.get('stat_consumption') for k in hass.data['energy_manager'].data.get('device_consumption')]

    for sensor in sensors:
        log.debug(f"Setting up statistics corrector for {sensor}")
        @state_trigger(f"{sensor}")
        async def corrector(var_name=None, value=None):
            log.debug(f"Statistics corrector checking {var_name}")

            start_time = datetime.now() - timedelta(minutes=30)
            end_time = datetime.now()

            stats = _get_statistic(start_time, end_time, [var_name], "5minute", 'state')
            unit = state.getattr(var_name).get('unit_of_measurement')

            stat = [{'start': d.get('start'), 'value': float(d.get('state'))} for d in stats.get(var_name)]
            previous, last = stat[:-1], stat[-1]
            previous_values = [v.get('value') for v in previous]

            average = sum(previous_values) / len(previous_values)
            delta = abs(last.get('value') - average)

            #log.debug(f"Checking if delta ({delta}) is larger than avarage ({average})")

            if delta > average:
                log.debug(f"Delta to high for {var_name} | State: {last.get('value')}, Avarage value: {average}, Delta: {delta}")
                hass.data["recorder_instance"].async_adjust_statistics(statistic_id=var_name,
                                                                       start_time=last.get('start'),
                                                                       sum_adjustment=average,
                                                                       adjustment_unit=unit)

        decorated_functions[sensor] = corrector

    # this isn't needed afaik? or can we listen to an event regarding the energy manager, then this would be nice.
    for sensor in list(decorated_functions.keys()):
        if sensor not in sensors:
            del decorated_functions[sensor]