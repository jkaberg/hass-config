@state_trigger("binary_sensor.kaffekoker == 'off'", state_hold=10)
@state_trigger("binary_sensor.kaffekoker == 'on'", state_hold=1200) # 20 min
def manage_coffemaker(value=None):
    """
    Turn off coffemaker after 20 min, and then reactivate the plug instantly
    """
    if value == 'on':
        switch.turn_off(entity_id='switch.kaffekoker_2')
    else:
        switch.turn_on(entity_id='switch.kaffekoker_2')

@state_trigger("'on' in [binary_sensor.platetopp, binary_sensor.stekeovn]")
@state_trigger("binary_sensor.platetopp == 'off' or binary_sensor.stekeovn == 'off'", state_hold=900)
def manage_kitchen_fan(value=None, var_name=None):
    if value == 'on':
        switch.turn_on(entity_id='switch.kjokken_vifte')

        if "platetopp" in var_name:
            light.turn_on(entity_id="light.kjokken_viftelys", brightness=254)
    else:
        switch.turn_off(entity_id='switch.kjokken_vifte')

        if light.taklys_kjokken == 'on':
            light.turn_on(entity_id="light.kjokken_viftelys", brightness=float(light.taklys_kjokken.brightness))
        else:
            light.turn_off(entity_id="light.kjokken_viftelys")