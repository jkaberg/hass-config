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
def heatpump_use_heat(value=None):
    """
    We never want to use heat_cool since it both heat and
    cool the air, thus using a lot of energy for nothing.

    Normally this only happends when the heatpump is activated
    via Google Assistant/Home.
    """
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')
