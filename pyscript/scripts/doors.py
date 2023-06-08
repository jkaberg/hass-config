

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