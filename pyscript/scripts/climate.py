@time_trigger("once(04:00:00)")
@state_active("climate.panasonic_ac == 'off' \
               and int(sensor.panasonic_ac_inside_temperature) < 21")
def morning_heat_on():
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

#@time_trigger("once(06:00:00)")
def morning_heat_off():
    if not climate.panasonic_ac is 'off':
        climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                              hvac_mode='off')

@state_trigger("climate.panasonic_ac == 'heat_cool'")
def heatpump_use_heat():
    """
    We never want to use heat_cool since it both heat and
    cool the air, thus using a lot of energy for nothing.

    Normally this only happends when the heatpump is activated
    via Google Assistant/Home.
    """
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

@state_trigger("float(sensor.vaskerom_humidity) < 40")
@state_active("switch.vaskerom_avfukter == 'on'")
def off_humidifier_washingroom():
    switch.turn_off(entity_id='switch.vaskerom_avfukter')

@state_trigger("float(sensor.vaskerom_humidity) > 40")
@state_active("switch.vaskerom_avfukter == 'off'")
def on_humidifier_washingroom():
    switch.turn_on(entity_id='switch.vaskerom_avfukter')