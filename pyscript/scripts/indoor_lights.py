import homeassistant

LIGHT_BRIGHTNESS=20
LIGHT_TRANSITION=20


def _get_light_devices():
    ent_reg = homeassistant.helpers.entity_registry.async_get(hass)
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
@time_trigger("once(sunrise + 1h)")
@state_trigger("group.someone_home == 'not_home'", state_hold=30)
def sunrise_or_nobody_home(**kwargs):
    """ 
        Turns of all lights 1h after sunrise or
        when nobody home.
    """

    lights = _get_light_devices()

    # zigbee group/scene
    light.turn_off(entity_id="light.all_lights", 
                   transition=LIGHT_TRANSITION)
    switch.turn_off(entity_id="switch.all_lights")

    # happy wife, happy life
    if device_tracker.iphone_2 == 'home':
        lights.get('zwave_js').remove('light.taklys_kontor')

    # z-wave multicast shut down all lights
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)
 

# Kveld- og morgenbelysning
@time_trigger("once(05:30)", "once(sunset - 1h)")
@state_trigger("group.someone_home == 'home'")
@state_active("group.someone_home == 'home'")
@time_active("range(05:30, sunrise + 1h)", "range(sunset - 1h, 22:30)")
def morning_sunset_light(**kwargs):
    light.turn_on(entity_id="light.sunset_sunrise_lights", 
                    brightness=LIGHT_BRIGHTNESS,
                    transition=LIGHT_TRANSITION)
    switch.turn_on(entity_id="switch.night_lights")

    zwave_devices = ['light.taklys_trapp',
                     'light.taklys_inngang',
                     'light.taklys_bad_1_etg']

    zwave_js.multicast_set_value(entity_id=zwave_devices,
                                 command_class='38',
                                 property='targetValue',
                                 value=LIGHT_BRIGHTNESS)

# Nattbelysning
@time_trigger("once(22:30)")
@state_active("group.someone_home == 'home'")
def night_light(**kwargs):
    lights = _get_light_devices()

    light.turn_off(entity_id="light.sunset_sunrise_lights",
                    transition=LIGHT_TRANSITION)
    #switch.turn_on(entity_id="switch.night_lights")

    # z-wave multicast shut down all lights
    zwave_js.multicast_set_value(entity_id=lights.get('zwave_js'),
                                 command_class='38',
                                 property='targetValue',
                                 value=0)