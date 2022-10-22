@state_trigger("sensor.accumulated_energy_hourly2")
def handle_power_tariff(value=None):
    value = float(value)

    if value == 0: # resume
        handle_boiler(binary_sensor.priceanalyzer_is_five_cheapest)
        handle_ev_charger(binary_sensor.priceanalyzer_is_ten_cheapest)
    elif value >= 8.5:
        handle_boiler()
        handle_ev_charger()

@state_trigger("binary_sensor.priceanalyzer_is_five_cheapest")
def handle_boiler(value=None): # on / off
    temp = 75 if value == 'on' else 55

    climate.set_temperature(entity_id='climate.varmtvannsbereder',
                            temperature=temp)

@state_trigger("binary_sensor.priceanalyzer_is_ten_cheapest",
               "input_boolean.force_evcharge",
               "input_select.current_easee_charger")
def handle_ev_charger(value=None): # on / off
    current = int(input_select.current_easee_charger) if 'on' in [value, input_boolean.force_evcharge] or value.isdigit() else 0

    easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                current=current)