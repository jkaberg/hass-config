@state_trigger("binary_sensor.front_door_ding == 'on'")
@state_active("group.someone_home == 'home'")
def doorbell_ring():
    media_player.play_media(media_content_id='https://hast.eth0.sh/local/audio/doorbell.mp3', 
                            media_content_type='music',
                            entity_id='media_player.gminis')