state.persist("pyscript.PWR_CTRL", default_value=0)

@time_trigger("once(14:30)", "once(21:00)")
def reload_priceanalyzer():
    homeassistant.reload_config_entry(entity_id='sensor.priceanalyzer_tr_heim_2')

@state_trigger("input_boolean.away_mode")
def handle_away_mode(value=None):
    if value == 'on': # away
        handle_boiler(off=True)
        handle_electric_heating(off=True)
    else: # home
        handle_boiler()
        handle_electric_heating()

@state_trigger("sensor.accumulated_energy_hourly2")
@state_active("input_boolean.away_mode == 'off'")
def handle_power_tariff(value=None):
    value = float(value)
    temp = 0 if not pyscript.PWR_CTRL else float(pyscript.PWR_CTRL)

    def check(n, v=value, t=temp):
        return v > n and n > t

    if check(9.5):
        handle_electric_heating(off=True)
    elif check(9):
        handle_boiler(off=True)
    elif check(8.5):
        handle_ev_charger(off=True)

    pyscript.PWR_CTRL = value

@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def handle_boiler(off=False):
    temp = 55 if off else int(sensor.vvbsensor_tr_heim)

    climate.set_temperature(entity_id='climate.varmtvannsbereder',
                            temperature=temp)

@state_trigger("input_boolean.force_evcharge",
               "input_select.current_easee_charger")
@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def handle_ev_charger(off=False):
    current = int(input_select.current_easee_charger) if 'on' in [binary_sensor.priceanalyzer_is_ten_cheapest, input_boolean.force_evcharge] and not off else 0

    easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                current=current)

@time_trigger("cron(0 * * * *)")
@state_active("input_boolean.away_mode == 'off'")
def handle_electric_heating(off=False, heating_adjust=2):
    value = -abs(heating_adjust) if off else float(sensor.priceanalyzer_tr_heim_2)

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
               'climate.panasonic_ac': LIVINGROOM,
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