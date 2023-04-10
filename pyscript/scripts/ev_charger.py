@state_trigger("sensor.garasje_status",
               "input_boolean.away_mode",
               "input_boolean.force_evcharge",
               "binary_sensor.priceanalyzer_is_ten_cheapest")
def on_off():
    if 'on' in [input_boolean.force_evcharge, binary_sensor.priceanalyzer_is_ten_cheapest] \
               and sensor.garasje_status in ['awaiting_start', 'ready_to_charge', 'charging'] \
               and input_boolean.away_mode == 'off':
        if switch.garasje_is_enabled == 'off':
            switch.turn_on(entity_id="switch.garasje_is_enabled")
    else: # off
        if switch.garasje_is_enabled == 'on':
            switch.turn_off(entity_id="switch.garasje_is_enabled")

@state_trigger("switch.garasje_is_enabled",
               "sensor.estimated_hourly_consumption")
@state_active("switch.garasje_is_enabled == 'on'")
def adjust_limits():
    current = 0
    limits = [0, 6, 10, 13, 16, 20, 25, 32]
    consumption = float(sensor.estimated_hourly_consumption)
    threshold = float(input_select.energy_tariff) - 0.6

    # we add garasje_power because this way we know what we have left to "work with"
    remaining_power = (threshold - consumption) + float(sensor.garasje_power)
    remaining_current = (remaining_power * 1000) / 230

    current = max([x for x in limits if x <= remaining_current]) if remaining_current > 0 else 0

    if float(sensor.garasje_dynamic_charger_limit) != current:
        log.debug(f"Adjusting EV charger limit to {current}A, previously {sensor.garasje_dynamic_charger_limit}A")

        easee.set_charger_dynamic_limit(charger_id='EHCQPVGQ', current=current)