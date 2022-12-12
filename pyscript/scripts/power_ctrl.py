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
        if v > n and v > float(pyscript.PWR_CTRL):
            pyscript.PWR_CTRL = n
            return True
        return False

    if check(9.3):
        heating(inactive=True)
    elif check(8.5):
        boiler(inactive=True)
    elif check(8):
        ev_charger(inactive=True)
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
               "input_select.current_easee_charger")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def ev_charger(inactive=False):
    if 'on' in [input_boolean.force_evcharge, binary_sensor.priceanalyzer_is_ten_cheapest] and not inactive:
        current = int(input_select.current_easee_charger)
    else:
        current = 0

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
               'climate.panasonic_ac': LIVINGROOM,
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