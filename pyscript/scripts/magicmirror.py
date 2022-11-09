import requests
from datetime import datetime

@state_trigger("media_player.magicmirror.app_name != 'DashCast' \
                or media_player.magicmirror != 'idle'")
def cast_magicmirror():
    url = pyscript.config.get('global').get('magicmirror_url')

    dash_cast.load_url(entity_id='media_player.magicmirror', url=url, force=True)

#state_trigger()
@time_trigger("once(06:00)", "once(09:00)", "once(16:00)", "once(22:30)")
@time_active("range(06:00, 22:30)")
@state_active("group.someone_home == 'home'")
def motion_magicmirror(value=None, trigger_time=None):
    def set_brightness(brightness=0):
        base_url = pyscript.config.get('global').get('magicmirror_url')
        apikey = pyscript.config.get('global').get('magicmirror_apikey')
        url = f"{base_url}/api/brightness/{brightness}"

        task.executor(requests.get, url, headers={"Authorization": f"apiKey {apikey}"})

    brightness = 0

    if isinstance(trigger_time.now(), datetime):
        hour = trigger_time.now().hour
        
        if hour in [6, 16]:
            brightness = 100
        elif hour == 9:
            brightness = 50
        elif hour == 22:
            brightness = 0

    #brightness = 100 if value == 'on' else 0

    set_brightness(brightness)