

@state_trigger("lock.hoveddor", "lock.kjellerdor")
def doors(var_name=None):
   # door names
    door_names = {'hoveddor': 'Hoveddør',
                  'kjellerdor': 'Kjellerdør'}

    # map action to text
    actions = {'': ''}

    var_name = var_name.replace('lock.', '')

    # map id to name
    persons = {'010': 'Joel',
               '011': 'Marte',
               '012': 'Jonas'}

    code = state.get(f"sensor.{var_name}_last_used_pin_code")
    source = state.get(f"sensor.{var_name}_last_unlock_source")
    user = state.get(f"sensor.{var_name}_last_unlock_user")

    text = f"{door_names.get(var_name)} | Code: {code} | Source name: {source} | User: {user}"
    log.debug(text)

@state_trigger("group.someone_home == 'not_home'", state_hold=300)
@state_active("lock.hoveddor == 'unlocked'")
def lock_maindoor():
   lock.lock(entity_id='lock.hoveddor')

@state_trigger("group.someone_home == 'home'")
@time_trigger("once(06:30)", "once(13:50)")
@time_active("range(06:00, 22:30)")
@state_active("lock.hoveddor == 'locked' and group.someone_home == 'home'")
def unlock_maindoor():
   if switch.hoveddor_auto_relock == 'on':
      switch.turn_off(entity_id="switch.hoveddor_auto_relock")

   lock.unlock(entity_id='lock.hoveddor')

@time_trigger("once(22:30)")
def autolock_maindoor_on():
   if switch.hoveddor_auto_relock == 'off':
      switch.turn_on(entity_id="switch.hoveddor_auto_relock")

   if lock.hoveddor == 'unlocked':
      lock.lock(entity_id='lock.hoveddor')

@time_trigger("once(06:30)")
@state_active("group.someone_home == 'home'")
def autolock_maindoor_off():
   switch.turn_off(entity_id="switch.hoveddor_auto_relock")