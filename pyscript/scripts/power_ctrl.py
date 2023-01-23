import sys
from datetime import datetime, timedelta, timezone

from history import _get_statistic, _get_history

state.persist("pyscript.PWR_CTRL", default_value=0)

def check_treshold(treshold=0.8):
    # check if treshold is above desired energ
    return float(sensor.estimated_hourly_consumption_filtered) > ((float(input_select.energy_tariff) - 0.2) * treshold)

@time_trigger("cron(0 0 1 * *)")
def energy_tariff():
    # adjust tariff according to month of the year
    # the logic is we use less electricty in the summer months
    # and thus can set an lower default usage tariff
    summer_time = range(4,9) # april til september
    tariff = 10

    if datetime.now().month in summer_time:
        tariff = 5

    state.set('input_select.energy_tariff', value=tarif)

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
    elif value == 0:
        pyscript.PWR_CTRL = 0

@state_trigger("binary_sensor.priceanalyzer_is_five_cheapest")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def boiler(inactive=False):
    # TODO: calc % of current tariff instead of current apphroach 
    if binary_sensor.priceanalyzer_is_five_cheapest == 'on' and not inactive:
      switch.turn_on(entity_id='switch.vaskerom_vvb')
    else:
      switch.turn_off(entity_id='switch.vaskerom_vvb')

@state_trigger("binary_sensor.priceanalyzer_is_ten_cheapest",
               "input_boolean.force_evcharge",
               "sensor.estimated_hourly_consumption_filtered",
               "input_select.energy_tariff")
@state_active("input_boolean.away_mode == 'off'")
def ev_charger():
    current = 0
    limits = [0, 6, 10, 13, 16, 20, 25, 32]
    consumption = float(sensor.estimated_hourly_consumption_filtered)
    threshold = float(input_select.energy_tariff) - 0.2

    if 'on' in [binary_sensor.priceanalyzer_is_ten_cheapest, input_boolean.force_evcharge]:
        remaining_power = threshold - consumption + float(sensor.garasje_power)
        remaining_current = (remaining_power * 1000) / 230
        current = max([x for x in limits if x <= remaining_current])

    if float(sensor.garasje_current) != current:
        log.debug(f"Adjusting charger limit to {current}A, previously {sensor.garasje_current}A")
    
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=current)

@state_trigger("sensor.priceanalyzer_tr_heim_2")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def heating(inactive=False, away_temp_adjust=4):
    # TODO: calc % of current tariff instead of current apphroach 
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