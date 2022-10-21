@time_trigger("once(04:00:00)")
@state_active("climate.panasonic_ac == 'off' \
               and float(sensor.kjokken_sensor_temperature) < 21")
def morning_heat_on():
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

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

@state_trigger("sensor.vaskerom_humidity")
def handle_humidifier(value=None):
    value = float(value)

    if value > 40 and switch.vaskerom_avfukter == 'off':
        switch.turn_on(entity_id='switch.vaskerom_avfukter')
    elif value < 40 and switch.vaskerom_avfukter == 'on':
        switch.turn_off(entity_id='switch.vaskerom_avfukter')
