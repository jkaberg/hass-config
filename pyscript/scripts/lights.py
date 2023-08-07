from homeassistant.helpers import entity_registry

def turn_off_zwave_lights(remove_lights = []):
    ent_reg = entity_registry.async_get(hass)
    lights = {}

    for entity in ent_reg.entities:
        if entity.startswith('light'):
            device = ent_reg.async_get(entity)

            if not lights.get(device.platform):
                lights[device.platform] = [device.entity_id]
            else:
                lights[device.platform].append(device.entity_id)

    for light in remove_lights:
        lights.get('zwave_js').remove(light)
    
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)

@time_trigger("once(sunrise)")
def sunrise():
    lights = ["switch.all_lights", "switch.utelys_sor", "switch.utelys_nord"] #, 'switch.localtuya_socket01_2']

    switch.turn_off(entity_id=lights)
    turn_off_zwave_lights()

@time_trigger("once(sunset)")
def sunset(trigger_time=None):
    lights = ["switch.night_lights", "switch.utelys_sor", "switch.utelys_nord"] #, 'switch.localtuya_socket01_2']

    if trigger_time.hour in range(14, 22):
        lights.append("switch.sunset_sunrise_lights")

    switch.turn_on(entity_id=lights)

@time_trigger("once(05:30)")
@state_active("sun.sun == 'below_horizon'")
def morning_light():
    lights = ['switch.sunset_sunrise_lights']

    switch.turn_on(entity_id=lights)

@time_trigger("once(22:30)")
def night_light():
    lights = ["switch.sunset_sunrise_lights", "switch.kjokken_viftelys"]

    switch.turn_off(entity_id=lights)
    turn_off_zwave_lights(remove_lights=['light.taklys_litet_soverom'])

@state_trigger("group.someone_home == 'not_home'", state_hold=300)
def nobody_home():
    turn_off_zwave_lights()

@state_trigger("light.taklys_kjokken", "light.taklys_kjokken.brightness")
def kitchen_light(value=None):
    if value == 'on':
        light.turn_on(entity_id="light.kjokken_viftelys", brightness=255) #float(light.taklys_kjokken.brightness))
    else:
        light.turn_off(entity_id="light.kjokken_viftelys")