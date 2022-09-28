from homeassistant.helpers import entity_registry, device_registry

def _get_pretty_name(ent):
    ent_reg = entity_registry.async_get(hass)
    entity = ent_reg.async_get(ent)

    if entity:
        return entity.name
    return None

def _notify(msg, title = None, tts = False):
    notify.varsle_telefoner(message=msg, title=title)
            
    if group.someone_home == 'home' and tts:
        tts.google_translate_say(entity_id='media_player.nestmini7392',
                                 message=msg,
                                 language='no')

@state_trigger("weather.hjem")
def windows_open_and_rainfall(value=None):
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
            if state.get(device) == 'on':
                dev_name = _get_pretty_name(device)
                device_name = dev_name.replace('_contact', '')

                if not notify_devices:
                    notify_devices = device_name
                else:
                    notify_devices = f"{notify_devices}, {device_name}"
        
        if notify_devices:
            msg = f"{notify_devices} er åpent og det er meldt nedbør."

            _notify(title="Lukk vinduer!", msg=msg, tts=True)

@state_trigger("float(sensor.kjeller_ytterdor_sensor_temperature) <= 3")
def cold_basement():
    _notify(title="Det er kaldt i kjelleren",
            msg=f"Det er nå {sensor.kjeller_ytterdor_sensor_temperature}°C i kjelleren.")


@state_trigger("binary_sensor.oppvaskmaskin == 'off'",
               "binary_sensor.torketrommel == 'off'",
               "binary_sensor.vaskemaskin == 'off'",
               state_hold=300)
def notify_machines_compelete(value=None, var_name=None):
    name = ""
    if var_name and value == 'off':
        if var_name == 'binary_sensor.oppvaskmaskin':
            name = 'Oppvaskmaskin'
        elif var_name == 'binary_sensor.torketrommel':
            name = 'Tørketrommel'
        elif var_name == 'binary_sensor.vaskemaskin':
            name = 'Vaskemaskin'

        if name:
            _notify(msg=f"{name} er ferdig!", tts=True)


@time_trigger("once(20:00:00)")
def check_batteries(min_perc=20):
    notify = {}
    sensors = state.names("sensor")

    for sensor in sensors:
        device_class = state.getattr(sensor).get('device_class')
        if device_class == "battery":
            try:
                battery_level = float(state.get(sensor))

                if battery_level <= min_perc:
                    notify[sensor] = battery_level
            except ValueError: # some battery_level values cannot be cast to float, eg 'unavailable' and 'unknown'
                continue
            
    if notify:
        notify_devices = f""
        for device, battery_level in notify.items():
            #device = _get_pretty_name(device)
            if not notify_devices:
                notify_devices = f"{device} ({battery_level}%)"
            else:
                notify_devices = f"{notify_devices}, {device} ({battery_level}%)"

        msg = f"Lavt batteri på: {notify_devices}"

        _notify(msg, title = "Lavt batteri")
