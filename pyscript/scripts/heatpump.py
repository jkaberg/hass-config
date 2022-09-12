#@time_trigger("once(04:00:00)")
def morning_heat_on(**kwargs):
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')

#@time_trigger("once(06:00:00)")
def morning_heat_off(**kwargs):
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='off')

@state_trigger("climate.panasonic_ac == 'heat_cool'")
def heatpump_use_heat(value=None, **kwargs):
    """
    We never want to use heat_cool since it both heat and
    cool the air, thus using a lot of energy for nothing.

    Normally this only happends when the heatpump is activated
    via Google Assistant/Home.
    """
    climate.set_hvac_mode(entity_id='climate.panasonic_ac',
                          hvac_mode='heat')
