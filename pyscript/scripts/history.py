from typing import Literal
from datetime import datetime, timezone, timedelta

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.recorder.statistics import statistics_during_period

decorated_functions = {}


async def _get_history(
    start_time: datetime,
    end_time: datetime | None,
    entity_ids: list[str] | None):

    start_time = start_time.astimezone(timezone.utc)
    end_time = end_time.astimezone(timezone.utc)

    return(await get_instance(hass).async_add_executor_job(get_significant_states, hass, start_time, end_time, entity_ids))

#https://github.com/home-assistant/core/blob/dev/homeassistant/components/recorder/websocket_api.py#L137
#https://github.com/home-assistant/core/blob/9cd159ee011d4c048aea8bd1e3285d7b1b764277/homeassistant/components/recorder/statistics.py#L1643
async def _get_statistic(
    start_time: datetime,
    end_time: datetime | None,
    statistic_ids: list[str] | None,
    period: Literal["5minute", "day", "hour", "week", "month"],
    types: set[Literal["last_reset", "max", "mean", "min", "state", "sum"]]):

    start_time = start_time.astimezone(timezone.utc)
    end_time = end_time.astimezone(timezone.utc)

    return(await get_instance(hass).async_add_executor_job(statistics_during_period, hass, start_time, end_time, statistic_ids, period, None, types))


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


#@time_trigger("cron(*/1 * * * *)")
@time_trigger("startup")
def correct_bad_readings():
    global decorated_functions

    # fetch all sensors listed in the energy dashboard
    sensors = [k.get('stat_consumption') for k in hass.data['energy_manager'].data.get('device_consumption')]

    for sensor in sensors:
        if sensor in decorated_functions:
            continue

        @state_trigger(f"{sensor}")
        def corrector(var_name=None):
            start_time = datetime.now() - timedelta(minutes=30)
            end_time = datetime.now()

            stats = _get_statistic(start_time, end_time, [var_name], "5minute", 'state')
            unit = state.getattr(var_name).get('unit_of_measurement')
            previous = None

            for d in stats.get(var_name):
                state = float(d.get('state'))

                if previous is None:
                    previous = state
                    continue

                delta = abs(state - previous)

                if delta >= (previous * 3):
                    log.debug(f"Delta to high for {var_name} | State: {state}, Previous state: {previous}, Delta: {delta}")
                    hass.data["recorder_instance"].async_adjust_statistics(statistic_id=var_name,
                                                                           start_time=d.get('start'),
                                                                           sum_adjustment=previous,
                                                                           adjustment_unit=unit)

        decorated_functions[sensor] = corrector

    for sensor in list(decorated_functions.keys()):
        if sensor not in sensors:
            state_trigger.remove_listener(sensor)
            del decorated_functions[sensor]