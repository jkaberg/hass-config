@time_trigger("once(sunrise + 30min)")
def outdoor_light_off(**kwargs):
    zwave_js.multicast_set_value(area_id="utebelysning",
                                 command_class='37',
                                 property='targetValue',
                                 value=False)

@time_trigger("once(sunset - 30min)")
def outdoor_light_on(**kwargs):
    zwave_js.multicast_set_value(area_id="utebelysning",
                                 command_class='37',
                                 property='targetValue',
                                 value=True)