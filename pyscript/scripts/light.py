from time import sleep

from homeassistant.helpers import entity_registry

#################
# Indoor lights #
#################

def _get_light_devices():
    ent_reg = entity_registry.async_get(hass)
    lights = {}

    for entity in ent_reg.entities:
        if entity.startswith('light'):
            device = ent_reg.async_get(entity)

            if not lights.get(device.platform):
                lights[device.platform] = [device.entity_id]
            else:
                lights[device.platform].append(device.entity_id)
    
    return lights

def toggle_lights(var_name=None, state=None):
    if not isinstance(var_name, list):
        var_name = [var_name]

    for light in var_name:
        while state.get(light) != state:
            if var_name.startswith('switch'):
                eval(f"switch.turn_{state}({light})")
            elif var_name.startswith('light'):
                eval(f"light.turn_{state}({light})")

            sleep(2)


@state_trigger("group.someone_home == 'not_home'", state_hold=300)
def nobody_home():
    lights = _get_light_devices()

    # z-wave multicast shut down all lights
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)

@time_trigger("once(sunrise)")
def sunrise():
    #
    # task.executor(toggle_lights, "switch.all_lights", "off")
    switch.turn_off(entity_id="switch.all_lights")

@time_trigger("once(05:30)", "once(sunset)")
@time_active("range(05:30, sunrise)", "range(sunset, 22:00)")
def morning_sunset_light():
    switches = ['switch.sunset_sunrise_lights', 'switch.night_lights']

    #task.executor(toggle_lights, switches, "on")
    switch.turn_on(entity_id=switches)

# Nattbelysning
@time_trigger("once(22:30)")
def night_light():
    lights = _get_light_devices()

    zigbee_lights = ["switch.sunset_sunrise_lights", "light.kjokken_viftelys"]

    #task.executor(toggle_lights, zigbee_lights, "off")
    switch.turn_off(entity_id="switch.sunset_sunrise_lights")
    light.turn_off(entity_id="light.kjokken_viftelys")

    # markus rom
    if group.someone_home == 'home':
        lights.get('zwave_js').remove('light.taklys_litet_soverom')

    # z-wave multicast shut down all lights
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)

@state_trigger("light.taklys_kjokken", "light.taklys_kjokken.brightness")
def kitchen_light(value=None):
    if not binary_sensor.platetopp == 'on':
        if value == 'on':
            light.turn_on(entity_id="light.kjokken_viftelys", brightness=float(light.taklys_kjokken.brightness))
        else:
            light.turn_off(entity_id="light.kjokken_viftelys")

##################
# Outdoor lights #
##################

@time_trigger("once(sunrise + 1m)")
def outdoor_light_sunrise():
    utelys = ['switch.utelys', 'switch.localtuya_socket01_2']
    
    #task.executor(toggle_lights, utelys, "off")
    switch.turn_off(entity_id=utelys)


@time_trigger("once(sunset - 1m)")
def outdoor_light_sunset():
    utelys = ['switch.utelys', 'switch.localtuya_socket01_2']

    #task.executor(toggle_lights, utelys, "on")
    switch.turn_on(entity_id=utelys)