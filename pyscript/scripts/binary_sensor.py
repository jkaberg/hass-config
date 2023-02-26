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

@state_trigger("binary_sensor.platetopp == 'on' or binary_sensor.stekeovn == 'on'")
@state_trigger("binary_sensor.platetopp == 'off' or binary_sensor.stekeovn == 'off'", state_hold=900)
def manage_kitchen_fan(value=None, var_name=None):
    if value == 'on':
        switch.turn_on(entity_id='switch.kjokken_vifte')

        if var_name == 'binary_sensor.platetopp':
            light.turn_on(entity_id="light.kjokken_viftelys", brightness=255)
    else:
        switch.turn_off(entity_id='switch.kjokken_vifte')

        if not light.taklys_kjokken == 'on':
            light.turn_off(entity_id="light.kjokken_viftelys")