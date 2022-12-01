import requests
from datetime import datetime

@state_trigger("media_player.magicmirror")
@time_trigger("cron(*/1 * * * *)")
def cast(var_name='media_player.magicmirror', app_name='DashCast'):
    url = pyscript.config.get('global').get('magicmirror_url')
    attrs = state.getattr(var_name)

    if not ('app_name', app_name) in attrs.items():
        dash_cast.load_url(entity_id=var_name, url=url, force=True)

@state_trigger("binary_sensor.gang_pir_sensor_occupancy")
#@time_active("range(06:00, 22:30)")
@state_active("group.someone_home == 'home' and \
               media_player.magicmirror.app_name == 'DashCast'")
def motion(value=None):
    base_url = pyscript.config.get('global').get('magicmirror_url')
    api_key = pyscript.config.get('global').get('magicmirror_apikey')

    brightness = 100 if value == 'on' else 0

    url = f"{base_url}/api/brightness/{brightness}"
    task.executor(requests.get, url, headers={"Authorization": f"apiKey {api_key}"})