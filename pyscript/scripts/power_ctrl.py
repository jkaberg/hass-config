
state.persist("pyscript.PWR_CTRL", default_value=0)

@time_trigger("once(14:30)", "once(21:00)")
def reload_priceanalyzer():
    homeassistant.reload_config_entry(entity_id='sensor.priceanalyzer_tr_heim')

@state_trigger("sensor.accumulated_energy_hourly2")
def handle_power_tariff(value=None):
    value = float(value)
    heating_adjust = 2
    temp = 0 if not pyscript.PWR_CTRL else float(pyscript.PWR_CTRL)

    def check(n, v=value, t=temp):
        return v > n and n > t

    if check(9.5):
        handle_electric_heating(-abs(heating_adjust))
    elif check(9):
        handle_boiler()
    elif check(8.5):
        handle_ev_charger()
    elif value == 0 and input_boolean.away_mode == 'off': # resume
        handle_boiler(binary_sensor.priceanalyzer_is_five_cheapest)
        handle_ev_charger(binary_sensor.priceanalyzer_is_ten_cheapest)
        handle_electric_heating(sensor.priceanalyzer_tr_heim)

    pyscript.PWR_CTRL = value

@state_trigger("input_boolean.away_mode")
def handle_away_mode(value=None):
    heating_adjust = 4

    if value == 'on':
        handle_boiler()
        handle_electric_heating(-abs(heating_adjust))
    else:
        handle_boiler(binary_sensor.priceanalyzer_is_ten_cheapest)
        handle_electric_heating(sensor.priceanalyzer_tr_heim)

@state_trigger("binary_sensor.priceanalyzer_is_five_cheapest")
@state_active("input_boolean.away_mode == 'off'")
def handle_boiler(value=None): # on / off
    temp = 75 if value == 'on' else 55

    climate.set_temperature(entity_id='climate.varmtvannsbereder',
                            temperature=temp)

@state_trigger("binary_sensor.priceanalyzer_is_ten_cheapest",
               "input_boolean.force_evcharge",
               "input_select.current_easee_charger")
def handle_ev_charger(value=None): # on / off
    # .isdigit() == current_easee_charger endret seg
    current = int(input_select.current_easee_charger) if 'on' in [value, input_boolean.force_evcharge] or value.isdigit() else 0

    easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                current=current)

@state_trigger("sensor.priceanalyzer_tr_heim")
@state_active("input_boolean.away_mode == 'off'")
def handle_electric_heating(value=None):
    value = float(value)

    BAD = 25
    SOVEROM = 20
    PANELOVN = 21
    GULVVARME = 22

    # climate entity: setpoint
    heaters = {'climate.panelovn_inngang': PANELOVN,
               'climate.panelovn_hovedsoverom': 18,
               'climate.panelovn_stort_soverom': SOVEROM,
               'climate.panelovn_mellom_soverom': SOVEROM,
               'climate.panelovn_litet_soverom': SOVEROM,
               'climate.gulvvarme_bad_1_etg': BAD,
               'climate.gulvvarme_bad_2_etg': BAD,
               'climate.panasonic_ac': PANELOVN,
               'climate.gulvvarme_stue': GULVVARME,
               'climate.gulvvarme_kjokken': GULVVARME,
               'climate.gulvvarme_tv_stue': GULVVARME,
               'climate.panelovn_kontor': PANELOVN}

    for heater, temp in heaters.items():
        temp += value

        climate.set_temperature(entity_id=heater,
                                temperature=temp)