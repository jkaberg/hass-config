from homeassistant.helpers import entity_registry, device_registry

decorated_functions = {}

def _get_pretty_name(ent):
    ent_reg = entity_registry.async_get(hass)
    entity = ent_reg.async_get(ent)

    if entity:
        return entity.name
    return None

def _notify(msg, title='', speak=False):
    notify.varsle_telefoner(message=msg, title=title)
            
    if group.someone_home == 'home' and speak:
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

            _notify(title="Lukk vinduer!", msg=msg, speak=True)

@state_trigger("float(sensor.kjeller_ytterdor_sensor_temperature) <= 3")
def cold_basement():
    _notify(title="Det er kaldt i kjelleren",
            msg=f"Det er nå {sensor.kjeller_ytterdor_sensor_temperature}°C i kjelleren.")


#@state_trigger("binary_sensor.oppvaskmaskin == 'off'",
#               "binary_sensor.torketrommel == 'off'",
#               "binary_sensor.vaskemaskin == 'off'",
#               state_hold=300)
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
            _notify(msg=f"{name} er ferdig!", speak=True)


@time_trigger("startup")
#@time_trigger("cron(*/1 * * * *)")
def check_batteries():
    global decorated_functions

    decorated_functions = {}

    blacklist = ['sensor.lenovo_tb_x505f_battery_level', 
                 'sensor.vaerstasjon_battery_level',
                 'sensor.iphone_battery_level',
                 'sensor.sm_s901b_battery_level',
                 'sensor.0x0015bc003100d36f_battery',
                 'sensor.denne_ok_battery']

    sensors = state.names("sensor")
    battery_devices = []

    for sensor in sensors:
        if sensor in blacklist: continue

        if state.getattr(sensor).get('device_class') == "battery":
            battery_devices.append(sensor)

            log.debug(f"Setup battery notification for {sensor}")
            
            @state_trigger(f"float({sensor}) < 20",
                           f"{sensor} == 'unavailable'",
                           f"{sensor} == 'unknown'")
            def battery_checker(value=None, var_name=None):
                _notify(f"Lavt batteri på: {var_name} ({value}%)", title = "Lavt batteri")

            decorated_functions[sensor] = battery_checker

    for sensor in list(decorated_functions.keys()):
        if sensor not in battery_devices:
            del decorated_functions[sensor]

