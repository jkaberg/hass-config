import requests

@service
def magicmirror_motion(value=None):
    """ Dim the magic mirror screen based on motion """
    base_url = pyscript.config.get('global').get('magicmirror_url')
    api_key = pyscript.config.get('global').get('magicmirror_apikey')

    brightness = 100 if value == 'on' else 0

    url = f"{base_url}/api/brightness/{brightness}"
    task.executor(requests.get, url, headers={"Authorization": f"apiKey {api_key}"})