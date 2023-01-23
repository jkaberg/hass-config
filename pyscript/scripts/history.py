from datetime import datetime, timezone, timedelta

from history import _get_statistic, _get_history

decorated_functions = {}

def calc_energy_hours():
    # day hours = 06:00 til 22:00
    # night hours = 22:00 til 06:00
    night_start, night_end = datetime.strptime("22:00", "%H:%M").time(), datetime.strptime("06:00", "%H:%M").time()
    now = datetime.now()
    first_hour_of_month = datetime(
        year=now.year, month=now.month, day=1, hour=0
    )
    night_hours, day_hours = 0, 0

    while first_hour_of_month < now:
        night_hours += night_start <= first_hour_of_month.time() <= night_end
        day_hours += not night_hours
        first_hour_of_month += timedelta(hours=1)

    return day_hours, night_hours

@time_trigger("cron(0 * * * *)")
def energy_top_3_month(var_name="sensor.nygardsvegen_6_forbruk"):
    start_time = datetime.today().replace(day=1)
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

@time_trigger("cron(0 * * * *)")
def calc_energy_price():
    capacity_link = {2: 83, 5: 147, 10: 252, 15: 371, 20: 490, 25: 610, 50: 1048}
    def is_float(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    start_time = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    now_time = datetime.today()
    consumption_data = _get_statistic(start_time, now_time, ["sensor.nygardsvegen_6_forbruk"], "hour", 'state')
    price_data = _get_history(start_time, now_time, ["sensor.priceanalyzer_current_price"])

    consumption = [d.get('state') for d in consumption_data.get('sensor.nygardsvegen_6_forbruk')]
    prices = [d.state for d in price_data.get('sensor.priceanalyzer_current_price')]

    consumption = sum([float(x) for x in consumption if is_float(x)])
    prices = [float(x) for x in prices if is_float(x)]

    # day_hours, night_hours = calc_energy_hours()
    # https://ts.tensio.no/kunde/nettleie-priser-og-avtaler
    # remove VAT (0.75) as its added later
    # day_cost = 0.3855 * 0.75
    # night_cost = 0.2980 * 0.75
    # if now_time.month in [0, 1, 2]:
    #     day_cost = 0.3020 * 0.75
    #     night_cost = 0.2145 * 0.75
    tarif_price = 0 # (day_hours * day_cost) + (night_hours * night_cost)
    cut_off = 0.7
    avg_price = sum(prices) / len(prices)
    our_price = (avg_price * 1.25) * consumption
    state_price = 0

    if avg_price > cut_off:
        our_price = (((((avg_price - cut_off) * 0.1) + cut_off) + tarif_price) * 1.25) * consumption
        state_price = ((avg_price - cut_off) * 0.9) * consumption #((((avg_price - cut_off) * 0.9) + tarif_price) * 1.25) * consumption

    our_price += capacity_link.get(int(input_select.energy_tariff))

    attrs = {'state_class': 'total', 
             'device_class': 'monetary',
             'icon': 'mdi:currency-usd',
             'unit_of_measurement': 'NOK'}

    state.set('sensor.estimated_electricity_avarage_cost', value=round(avg_price, 2), new_attributes=attrs)
    state.set('sensor.estimated_electricity_cost', value=round(our_price, 2), new_attributes=attrs)
    state.set('sensor.estimated_electricity_cost_state', value=round(state_price, 2), new_attributes=attrs)


@time_trigger("startup")
async def correct_bad_readings():
    global decorated_functions

    decorated_functions = {}

    # fetch all sensors listed in the energy dashboard
    sensors = [k.get('stat_consumption') for k in hass.data['energy_manager'].data.get('device_consumption')]

    for sensor in sensors:
        #log.debug(f"Corrector setting up {sensor}")
        @state_trigger(f"{sensor}")
        async def corrector(var_name=None, value=None):
            #log.debug(f"Corrector checking {var_name}")

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