@state_trigger("sensor.kaffekoker_power", state_hold=10)
@state_trigger("sensor.vaskerom_avfukter_power", state_hold=10)
@state_trigger("sensor.vaskerom_vaskemaskin_power", state_hold=600)
@state_trigger("sensor.vaskerom_torketrommel_power", state_hold=240)
@state_trigger("sensor.kjokken_oppvaskmaskin_power", state_hold=720)
def input_boolean_generic(value=None, var_name=None):
    """
    Subscribe to various power sensor and set corresponding input_boolean to true/false

    We probably need better logic here =]
    """
    if None not in (value, var_name):
        var_name = var_name.replace('sensor.', '')
        var_name = var_name.replace('_power', '_active')
        var_name = f"input_boolean.{var_name}"

        if int(value) >= 15:
            state.set(var_name, 'on')
        else:
            state.set(var_name, 'off')

@state_trigger("input_boolean.kaffekoker_active == 'off'", state_hold=10)
@state_trigger("input_boolean.kaffekoker_active == 'on'", state_hold=1200) # 20 min
def manage_coffemaker(value=None):
    """
    Turn off coffemaker after 20 min, and then reactivate the plug instantly
    """
    if value == 'on':
        switch.turn_off(entity_id='switch.kaffekoker_2')
    else:
        switch.turn_on(entity_id='switch.kaffekoker_2')
