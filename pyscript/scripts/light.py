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

# Soloppgang eller ingen hjemme (alle lys av)
@time_trigger("once(sunrise)")
@state_trigger("group.someone_home == 'not_home'", state_hold=300)
def sunrise_or_nobody_home():
    lights = _get_light_devices()

    # zigbee group/scene
    light.turn_off(entity_id="light.all_lights", 
                   transition=20)
    switch.turn_off(entity_id="switch.all_lights")

    # happy wife, happy life
    if person.marte == 'home':
        lights.get('zwave_js').remove('light.taklys_kontor')

    # z-wave multicast shut down all lights
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)
 

# Kveld- og morgenbelysning
@time_trigger("once(05:30)", "once(sunset)")
@state_trigger("group.someone_home == 'home'")
@state_active("group.someone_home == 'home'")
@time_active("range(05:30, sunrise)", "range(sunset, 22:00)")
def morning_sunset_light():
    switches = ['switch.sunset_sunrise_lights', 'switch.night_lights']

    light.turn_on(entity_id="light.sunset_sunrise_lights", 
                  brightness=20,
                  transition=20)
    switch.turn_on(entity_id=switches)

# Nattbelysning
@time_trigger("once(22:30)")
@state_active("group.someone_home == 'home'")
def night_light():
    lights = _get_light_devices()

    light.turn_off(entity_id="light.sunset_sunrise_lights",
                   transition=20)

    switch.turn_off(entity_id="switch.sunset_sunrise_lights")

    # markus rom
    if group.someone_home == 'home':
        lights.get('zwave_js').remove('light.taklys_litet_soverom')

    # z-wave multicast shut down all lights
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)

##################
# Outdoor lights #
##################

@time_trigger("once(sunrise + 1m)")
def outdoor_light_sunrise():
    utelys = ['switch.utelys', 'switch.localtuya_socket01_2']
    
    switch.turn_off(entity_id=utelys)


@time_trigger("once(sunset - 1m)")
def outdoor_light_sunset():
    utelys = ['switch.utelys', 'switch.localtuya_socket01_2']

    switch.turn_on(entity_id=utelys)