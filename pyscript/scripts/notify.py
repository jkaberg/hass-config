import homeassistant


def _get_pretty_name(device):
    ent_reg = homeassistant.helpers.entity_registry.async_get(hass)
    dev = ent_reg.async_get(device)

    if dev:
        return dev.name
    return None

def _notify(msg, title = None):
    notify.varsle_telefoner(message=msg, title=title)
            
    if group.someone_home == 'home':
        tts.google_translate_say(entity_id='media_player.nestmini7392',
                                message=msg,
                                language='no')



#@time_trigger("cron(*/1 * * * *)")
@state_trigger("weather.hjem")
def windows_open_and_rainfall(value=None, **kwargs):
    """
    Notify when windows are open and its rainy or similar.
    """
    devices = ["binary_sensor.loftstue_takvindu_nord_contact",
               "binary_sensor.loftstue_takvindu_sor_contact",
               "binary_sensor.trapp_takvindu_contact"]

    rainfall = ["hail",
                "lightning",
                "lightning-rainy",
                "pouring",
                "rainy",
                "snowy",
                "snowy-rainy"]

    notify_devices = ""

    if value in rainfall:
        for device in devices:
            # window open (== on)?
            if eval(device) == 'on':
                dev_name = _get_pretty_name(device)
                device_name = dev_name.replace('_contact', '')

                if not notify_devices:
                    notify_devices = device_name
                else:
                    notify_devices = f"{notify_devices}, {device_name}"
        
        if notify_devices:
            msg = f"{notify_devices} er åpent og det er meldt nedbør."

            _notify(title="Lukk vinduer!", msg=msg)

@state_trigger("float(sensor.kjeller_ytterdor_sensor_temperature) <= 3")
def cold_basement(**kwargs):
    _notify(title="Det er kaldt i kjelleren",
            msg=f"Det er nå {sensor.kjeller_ytterdor_sensor_temperature}°C i kjelleren.")


@state_trigger("input_boolean.kjokken_oppvaskmaskin_active == 'off'", state_hold=300)
@state_trigger("input_boolean.vaskerom_torketrommel_active == 'off'", state_hold=300)
@state_trigger("input_boolean.vaskerom_vaskemaskin_active == 'off'", state_hold=300)
def notify_machines_compelete(value=None, var_name=None,**kwargs):
    name = ""
    if var_name and value == 'off':
        if var_name == 'input_boolean.kjokken_oppvaskmaskin_active':
            name = 'Oppvaskmaskin'
        elif var_name == 'input_boolean.vaskerom_torketrommel_active':
            name = 'Tørketrommel'
        elif var_name == 'input_boolean.vaskerom_vaskemaskin_active':
            name = 'Vaskemaskin'

        if name:
            _notify(msg=f"{name} er ferdig!")