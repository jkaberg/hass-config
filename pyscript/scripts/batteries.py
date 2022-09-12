@time_trigger("once(20:00:00)")
def check_batteries(min_perc=20):
    notify = {}
    sensors = state.names("sensor")
    for sensor in sensors:
        sensor_attr = state.getattr(sensor)
        if "device_class" in sensor_attr and sensor_attr["device_class"] == "battery":
            battery_level = state.get(sensor)

            if not isinstance(battery_level, int):
                continue

            if int(battery_level) <= min_perc:
                notify[sensor] = battery_level
            
    if notify:
        tmp_msg = f""
        for device, battery_level in devices.items():
            if not tmp_msg:
                tmp_msg = f"{device} ({battery_level}%)"
            else:
                tmp_msg = f"{tmp_msg}, {device} ({battery_level}%)"

        persistent_notification.create(message=f'Lavt batteri på: {tmp_msg}', title="Batteri varning!")