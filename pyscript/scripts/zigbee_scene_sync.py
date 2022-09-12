import json
import homeassistant

def _get_scene(entity_id=None):
    ret = []
    if entity_id:
        devices = homeassistant.components.homeassistant.scene.entities_in_scene(hass, entity_id)
        ent_reg = homeassistant.helpers.entity_registry.async_get(hass)

        for device in devices:
            for entity in ent_reg.entities:
                if str(entity) == str(device):
                    d = ent_reg.async_get(entity)
                    ret.append(d.original_name)

    return ret

#@state_trigger("scene.zigbee_all_lamps")
def group_syncer(value=None, var_name=None, **kwargs):
    if var_name:
        device_names = _get_scene(entity_id=var_name)
        group_name = var_name.replace('scene.zigbee_', '')

        mqtt.publish(topic='zigbee2mqtt/bridge/request/group/remove',
                     payload=json.dumps({"id": group_name, "force": "true"}))

        mqtt.publish(topic='zigbee2mqtt/bridge/request/group/add',
                     payload=json.dumps({"friendly_name": group_name}))

        for name in device_names:
            mqtt.publish(topic='zigbee2mqtt/bridge/request/group/members/add',
                         payload=json.dumps({"group": group_name, "device": name}))