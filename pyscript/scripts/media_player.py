#@time_trigger("cron(*/3 * * * *)")
#@state_trigger("media_player.nestmini7392 == 'off' \
#                or media_player.nestmini9210 == 'off'")
def wake_players():
    """
    Mainly used with the doorbell to keep the mini's awake.
    This avoids the anoying "announce" bell/chime on the gminis
    right before playing media.
    """

    unwanted_states = ['off', 'idle']
    devices = ['media_player.nestmini7392',
               'media_player.nestmini9210']

    for device in devices:
        if state.get(device) in unwanted_states:
            media_player.play_media(media_content_id='https://hast.eth0.sh/local/audio/1sec.mp3', 
                                    media_content_type='music',
                                    entity_id=device)

@time_trigger("once(22:30)")
@state_active("media_player.shield_2 == 'paused'")
def shutdown_loft_tv():
    media_player.turn_off(entity_id='media_player.shield_2')