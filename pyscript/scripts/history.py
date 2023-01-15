import sys
from datetime import datetime, timezone, timedelta

if "/config/pyscript/modules" not in sys.path:
    sys.path.append("/config/pyscript/modules")

from history import _get_statistic, _get_history

decorated_functions = {}

@time_trigger("cron(0 * * * *)")
def energy_get_top_3_month():
    var_name="sensor.nygardsvegen_6_forbruk"

    start_time = datetime.today().replace(day=1)
    end_time = datetime.today()
    peak_energy_usage = str()
    
    statistics = _get_statistic(start_time, end_time, [var_name], "hour", 'state')
    top_three = sorted(statistics.get(var_name), key=lambda d: d['state'], reverse=True)[:3]

    for hour in top_three:
        peak_energy_usage = f"{peak_energy_usage}, {hour.get('state')}" if peak_energy_usage else str(hour.get('state'))

    state.set('input_text.peak_energy_usage', value=peak_energy_usage)


@time_trigger("cron(0 * * * *)")
def calc_energy_price():
    start_time = datetime.today().replace(day=1, hour=0, minute=0, second=0)
    now_time = datetime.today()
    usage_data = _get_statistic(start_time, now_time, ["sensor.nygardsvegen_6_forbruk"], "hour", 'state')
    price_data = _get_history(start_time, now_time, ["sensor.priceanalyzer_current_price"])

    previous_price_value = 0
    cut_off_price = 0.7
    our_price = 0
    state_price = 0
    avg_price = []
    consumption = 0

    for usage in usage_data.get("sensor.nygardsvegen_6_forbruk"):
        start = usage.get('start')
        end = usage.get('end')
        consumption += usage.get('state')

    for data in price_data.get("sensor.priceanalyzer_current_price"):
        price = float
        try:
            price = float(data.state)
            #log.debug(data.last_changed)
            previous_price_value = price
        except ValueError: # unknown or no value
            price = previous_price_value

        avg_price.append(price)

    consumption = round(consumption, 2)
    month_avg_price = round(sum(avg_price)/len(avg_price), 2)

    if month_avg_price >= cut_off_price:
        state_price = round(consumption * ((month_avg_price - cut_off_price) * 0.9), 2)
        our_price = round(consumption * (((month_avg_price - cut_off_price) * 0.1) + cut_off_price), 2)
    else:
        our_price += consumption * (month_avg_price * 1.25)

    log.debug(f"Snitt pris: {month_avg_price}NOK, Forbruk: {consumption}kWh, Strømstøtte: {state_price}NOK, Vår pris: {our_price}NOK")

    state.set('input_number.electricity_cost_state', value=state_price)
    state.set('input_number.electricity_cost', value=our_price)


@time_trigger("startup")
async def correct_bad_readings():
    global decorated_functions

    decorated_functions = {}

    # fetch all sensors listed in the energy dashboard
    sensors = [k.get('stat_consumption') for k in hass.data['energy_manager'].data.get('device_consumption')]

    for sensor in sensors:
        log.debug(f"Corrector setting up {sensor}")
        @state_trigger(f"{sensor}")
        async def corrector(var_name=None, value=None):
            log.debug(f"Corrector checking {var_name}")

            start_time = datetime.now() - timedelta(minutes=30)
            end_time = datetime.now()

            stats = _get_statistic(start_time, end_time, [var_name], "5minute", 'state')
            unit = state.getattr(var_name).get('unit_of_measurement')

            stat = [{'start': d.get('start'), 'value': float(d.get('state'))} for d in stats.get(var_name)]
            previous, last = stat[:-1], stat[-1]
            previous_values = [v.get('value') for v in previous]

            average = sum(previous_values) / len(previous_values)
            delta = abs(last.get('value') - average)

            log.debug(f"Checking if delta ({delta}) is larger than avarage ({average})")

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