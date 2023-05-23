@state_trigger("binary_sensor.kaffekoker == 'off'", state_hold=10)
def manage_coffemaker_on(value=None):
    switch.turn_on(entity_id='switch.kaffekoker_2')

@state_trigger("binary_sensor.kaffekoker == 'on'", state_hold=1200) # 20 min
def manage_coffemaker_off(value=None):
    switch.turn_off(entity_id='switch.kaffekoker_2')

@state_trigger("binary_sensor.platetopp == 'on'",
               "binary_sensor.stekeovn == 'on'")
def manage_kitchen_fan_on(var_name=None):
    switch.turn_on(entity_id='switch.kjokken_vifte')

    if var_name == 'binary_sensor.platetopp':
        light.turn_on(entity_id="light.kjokken_viftelys", brightness=255)

@state_trigger("binary_sensor.platetopp == 'off' \
               and binary_sensor.stekeovn == 'off'", state_hold=600)
def manage_kitchen_fan_off():
    switch.turn_off(entity_id='switch.kjokken_vifte')

    if not light.taklys_kjokken == 'on':
        light.turn_off(entity_id="light.kjokken_viftelys")