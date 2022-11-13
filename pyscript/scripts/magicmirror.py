import requests
from datetime import datetime

@state_trigger("media_player.magicmirror.app_name != 'DashCast'",
               "media_player.magicmirror == 'off'")
#@state_active("media_player.magicmirror != 'unavailable'")
def cast():
    url = pyscript.config.get('global').get('magicmirror_url')

    dash_cast.load_url(entity_id='media_player.magicmirror', url=url, force=True)

@state_trigger("binary_sensor.gang_pir_sensor_occupancy")
@time_active("range(06:00, 22:30)")
@state_active("group.someone_home == 'home' and \
               media_player.magicmirror.app_name == 'DashCast'")
def motion(value=None):
    def set_brightness(brightness=0):
        base_url = pyscript.config.get('global').get('magicmirror_url')
        api_key = pyscript.config.get('global').get('magicmirror_apikey')
        url = f"{base_url}/api/brightness/{brightness}"

        task.executor(requests.get, url, headers={"Authorization": f"apiKey {api_key}"})

    brightness = 100 if value == 'on' else 0

    log.debug(f"setting brightness to {brightness}")

    set_brightness(brightness)