@state_trigger("sensor.accumulated_energy_hourly2")
def power_handler(value=None):
    value = float(value)

    if value == 0 and input_boolean.powersaver_active == 'on': # resume
        switch.turn_on(entity_id='switch.vaskerom_vvb')
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=int(input_select.current_easee_charger))

    elif value >= 8.5:
        switch.turn_off(entity_id='switch.vaskerom_vvb')
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=0)


@state_trigger("input_boolean.powersaver_active")
def powersaver_active(value=None):
    if value == 'on':
        switch.turn_on(entity_id='switch.vaskerom_vvb')
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=int(input_select.current_easee_charger))
    else:      
        switch.turn_off(entity_id='switch.vaskerom_vvb')
        if input_boolean.force_evcharge == 'off':
            easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                        current=0)


@state_trigger("input_boolean.force_evcharge")
def force_evcharge(value=None):
    if value == 'on':
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=int(input_select.current_easee_charger))
    else:
        easee.set_charger_max_limit(charger_id='EHCQPVGQ',
                                    current=0)