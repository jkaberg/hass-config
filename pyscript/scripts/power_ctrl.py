state.persist("pyscript.PWR_CTRL", default_value=0)

@time_trigger("once(14:30)", "once(21:00)")
def reload_priceanalyzer():
    homeassistant.reload_config_entry(entity_id='sensor.priceanalyzer_tr_heim_2')

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
        #log.error(f"n: {n} | v: {v} | temp: {pyscript.PWR_CTRL}")
        if v > n and not n == float(pyscript.PWR_CTRL):
            pyscript.PWR_CTRL = n
            return True
        return False

    if check(9.5):
        heating(inactive=True)
    elif check(9):
        boiler(inactive=True)
    elif check(8.5):
        ev_charger(inactive=True)
    elif value == 0:
        pyscript.PWR_CTRL = 0

@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def boiler(inactive=False):
    temp = 55 if inactive else int(sensor.vvbsensor_tr_heim)

    climate.set_temperature(entity_id='climate.varmtvannsbereder',
                            temperature=temp)

@state_trigger("input_boolean.force_evcharge",
               "input_select.current_easee_charger")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def ev_charger(inactive=False):
    current = int(input_select.current_easee_charger) \
        if 'on' in [binary_sensor.priceanalyzer_is_ten_cheapest, input_boolean.force_evcharge] \
        and not inactive else 0

    easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                current=current)

@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def heating(inactive=False, away_temp_adjust=4):
    value = -abs(away_temp_adjust) if inactive else float(sensor.priceanalyzer_tr_heim_2)

    BATHROOM = 25
    BEDROOM = 20
    LIVINGROOM = 21
    FLOOR_HEATING = 22

    # climate entity: setpoint
    heaters = {'climate.panelovn_inngang': LIVINGROOM,
               'climate.panelovn_hovedsoverom': 18,
               'climate.stort_soverom': BEDROOM,
               'climate.mellom_soverom': BEDROOM,
               'climate.litet_soverom': BEDROOM,
               'climate.gulvvarme_bad_1_etg': BATHROOM,
               'climate.gulvvarme_bad_2_etg': BATHROOM,
               'climate.panasonic_ac': BEDROOM,
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