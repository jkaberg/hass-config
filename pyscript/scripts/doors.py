

@state_trigger("lock.hoveddor", "lock.kjellerdor")
def doors(var_name=None):
   # door names
    door_names = {'lock.hoveddor': 'Hoveddør',
                  'lock.kjellerdor': 'Kjellerdør'}

    # map action to text
    actions = {'': ''}

    # map id to name
    persons = {'010': 'Joel',
               '011': 'Marte',
               '012': 'Jonas'}

    action = state.get(f"{var_name}.action")
    source = state.get(f"{var_name}.action_source_name")
    user = state.get(f"{var_name}.action_user")

    text = f"{door_names.get(var_name)} | Action: {action} | Source name: {source} | User: {user}"
    log.debug(text)

@state_trigger("group.someone_home == 'not_home'", state_hold=300)
@time_trigger("once(22:30)")
@state_active("lock.hoveddor == 'unlocked'")
def lock_maindoor():
   lock.lock(entity_id='lock.hoveddor')

@time_trigger("once(13:50)")
@state_active("group.someone_home == 'home' and lock.hoveddor == 'locked'")
def unlock_maindoor():
   lock.unlock(entity_id='lock.hoveddor')

@state_active("lock.hoveddor == 'unlocked'")
@time_active("range(22:30, 06:00)")
def lock_maindoor_night():
   lock.lock(entity_id='lock.hoveddor')