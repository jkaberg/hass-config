import sys
from datetime import datetime, timedelta, timezone

if "/config/pyscript/modules" not in sys.path:
    sys.path.append("/config/pyscript/modules")

from history import _get_statistic, _get_history

state.persist("pyscript.PWR_CTRL", default_value=0)
state.persist("pyscript.CHARGER_LIMIT", default_value=0)

@state_trigger("sensor.strommaler_power")
def estimated_power_consumption(value=None, var_name=None, window_size=5):
    start_time = datetime.now(timezone.utc) - timedelta(minutes=window_size)
    now_time = datetime.now(timezone.utc)

    data = _get_history(start_time, now_time, [var_name])
    watt_usage_history = [float(d.state) for d in data.get(var_name) if d.last_updated < datetime.now(timezone.utc)]
    average_watt_usage = sum(watt_usage_history) / len(watt_usage_history)
    minute = datetime.now(timezone.utc).minute
    
    if minute >= (60 - window_size):
        current_time_remaining = (60 - minute + 60) * 60
    else:
        current_time_remaining = (60 - minute) * 60

    current_time_remaining += (60 - datetime.now(timezone.utc).second)
    estimated_remaining_usage = round(((average_watt_usage * current_time_remaining) / (60 * 60)) / 1000, 3)

    log.debug(f"Estimated power consumption is {estimated_remaining_usage} kWh, based on values {watt_usage_history}")
    state.set('sensor.estimated_hourly_consumption', estimated_remaining_usage)

@state_trigger("input_boolean.away_mode")
def away_mode(value=None):
    away = True if value == 'on' else False

    boiler(inactive=away)
    heating(inactive=away)

@state_trigger("sensor.nygardsvegen_6_forbruk")
@state_active("input_boolean.away_mode == 'off'")
def power_tariff(value=None):
    value = float(value)

    def check(n, v=value):
        if v > n and v > float(pyscript.PWR_CTRL):
            pyscript.PWR_CTRL = n
            return True
        return False

    if check(9.3):
        heating(inactive=True)
    elif check(8.5):
        boiler(inactive=True)
#    elif check(8):
#        ev_charger(inactive=True)
    elif value == 0:
        pyscript.PWR_CTRL = 0

@state_trigger("binary_sensor.priceanalyzer_is_five_cheapest")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def boiler(inactive=False):
    if binary_sensor.priceanalyzer_is_five_cheapest == 'on' and not inactive:
      switch.turn_on(entity_id='switch.vaskerom_vvb')
    else:
      switch.turn_off(entity_id='switch.vaskerom_vvb')

@state_trigger("binary_sensor.priceanalyzer_is_ten_cheapest",
               "input_boolean.force_evcharge",
               "sensor.estimated_hourly_consumption",
               "input_select.energy_tariff")
#@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def ev_charger(inactive=False):
    charger_limit = float(pyscript.CHARGER_LIMIT)
    limits = [0, 6, 10, 13, 16, 20, 25, 32]

    if 'on' in [input_boolean.force_evcharge, binary_sensor.priceanalyzer_is_ten_cheapest] and not inactive:
        consumption = float(sensor.estimated_hourly_consumption)
        threshold = float(input_select.energy_tariff)
        remaining_power = threshold - consumption + float(sensor.garasje_power)
        remaining_current = (remaining_power * 1000) / 230
        current = max([x for x in limits if x <= remaining_current])
        #log.debug(f"est. consumption {consumption}, treshold {threshold}, r. power {remaining_power}, r. current {remaining_current}, current {current}")
        #current = int(input_select.current_easee_charger)
    else:
        current = 0

    if charger_limit != current: #avoid hammering the Easee api
        log.debug(f"Adjusting charger limit to {current}A, previously {charger_limit}A")
        pyscript.CHARGER_LIMIT = charger_limit
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=current)

@state_trigger("sensor.priceanalyzer_tr_heim_2")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def heating(inactive=False, away_temp_adjust=4):
    value = -abs(away_temp_adjust) if inactive else float(sensor.priceanalyzer_tr_heim_2)

    BATHROOM = 25
    BEDROOM = 20
    LIVINGROOM = 21
    FLOOR_HEATING = 23

    # climate entity: setpoint
    heaters = {'climate.inngang': LIVINGROOM,
               'climate.hovedsoverom': 18,
               'climate.stort_soverom': BEDROOM,
               'climate.mellom_soverom': BEDROOM,
               'climate.litet_soverom': BEDROOM,
               'climate.gulvvarme_bad_1_etg': BATHROOM,
               'climate.gulvvarme_bad_2_etg': BATHROOM,
               'climate.panasonic_ac_3': LIVINGROOM,
               'climate.gulvvarme_inngang': FLOOR_HEATING,
               'climate.gulvvarme_stue': FLOOR_HEATING,
               'climate.gulvvarme_kjokken': FLOOR_HEATING,
               'climate.gulvvarme_tv_stue': FLOOR_HEATING,
               'climate.panelovn_kontor': LIVINGROOM}

    for heater, temp in heaters.items():
        temp += value

        try:
            if temp != float(state.getattr(heater).get('temperature')):
                climate.set_temperature(entity_id=heater,
                                        temperature=temp)
        except TypeError:
            # device unavilable or similar.
            pass


# lag automasjon som finner effekttrinn 