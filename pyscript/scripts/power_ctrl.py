import sys
from datetime import datetime, timedelta, timezone

from history import _get_statistic, _get_history

state.persist("pyscript.PWR_CTRL", default_value=0)

@time_trigger("startup", "cron(*/5 * * * *)")
#@state_trigger("sensor.energy_per_hour2")
def estimate_power_usage(var_name="sensor.energy_per_hour2", time_window=7):
    start_time = datetime.now() - timedelta(minutes=time_window)
    now_time = datetime.now()

    stats = _get_history(start_time, now_time, [var_name]).get(var_name)
    stats = [float(d.state) for d in stats]
    estimate = (((stats[-1] - stats[0]) * (60 - now_time.minute)) / len(stats)) + float(sensor.nygardsvegen_6_forbruk)
    log.debug(f"Estimated consumption: {estimate}")

    estimate = estimate if estimate > 0 else 0

    state.set('sensor.estimated_hourly_consumption', value=round(estimate, 3), new_attributes={'state_class': 'total', 
                                                                                               'device_class': 'energy',
                                                                                               'icon': 'mdi:transmission-tower-import',
                                                                                               'unit_of_measurement': 'kWh'})

@time_trigger("cron(0 0 1 * *)")
def energy_tarif():
    summer_time = range(4,9) # april til september
    tarif = 10

    if datetime.now().month in summer_time:
        tarif = 5

    state.set('input_select.energy_tariff', value=tarif)

@state_trigger("input_boolean.away_mode")
def away_mode(value=None):
    away = True if value == 'on' else False

    boiler(inactive=away)
    heating(inactive=away)

@state_trigger("sensor.nygardsvegen_6_forbruk")
@state_active("input_boolean.away_mode == 'off'")
def power_tarif(value=None):
    value = float(value)
    energy_tarif = float(input_select.energy_tariff)

    def check(n, v=value):
        if v > n and v > float(pyscript.PWR_CTRL):
            pyscript.PWR_CTRL = n
            return True
        return False

    if check(energy_tarif - 0.2): # 4.8 / 9.8
        heating(inactive=True)
    elif check(energy_tarif - 0.3): # 4.5 / 9.5
        boiler(inactive=True)
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
               "sensor.estimated_hourly_consumption",
               "sensor.garasje_status",
               "input_boolean.force_evcharge",
               "input_select.energy_tariff")
@state_active("input_boolean.away_mode == 'off'")
def ev_charger():
    current = 0
    limits = [0, 6, 10, 13, 16, 20, 25, 32]

    consumption = float(sensor.estimated_hourly_consumption)
    threshold = float(input_select.energy_tariff) - 0.4

    if 'on' in [binary_sensor.priceanalyzer_is_ten_cheapest, input_boolean.force_evcharge]:
        remaining_power = (threshold - consumption) + float(sensor.garasje_power)
        remaining_current = (remaining_power * 1000) / 230
        log.debug(f"{remaining_power} - {remaining_current}")
        current = max([x for x in limits if x <= remaining_current]) if remaining_current > 0 else 0

    if float(sensor.garasje_dynamic_charger_limit) != current:
        log.debug(f"Adjusting EV charger limit to {current}A, previously {sensor.garasje_dynamic_charger_limit}A")
    
        easee.set_charger_dynamic_limit(charger_id='EHCQPVGQ',
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
               'climate.panasonic_ac_2': LIVINGROOM, # gangen
               'climate.panasonic_ac_3': LIVINGROOM, # stua
               'climate.gulvvarme_inngang': FLOOR_HEATING,
               'climate.gulvvarme_stue': FLOOR_HEATING,
               'climate.gulvvarme_kjokken': FLOOR_HEATING,
               'climate.gulvvarme_tv_stue': FLOOR_HEATING,
               'climate.panelovn_kontor': LIVINGROOM}

    for heater, temp in heaters.items():
        temp += value

        try:
            if state.get(heater) is not 'off' and float(state.getattr(heater).get('temperature')) is not temp:
                climate.set_temperature(entity_id=heater,
                                        temperature=temp)
        except TypeError:
            # device unavilable or similar.
            pass