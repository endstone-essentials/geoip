from endstone.event import event_handler, PlayerLoginEvent


class EssentialsGeoIPPlayerListener:
    @event_handler
    def on_player_login(self, event: PlayerLoginEvent):
        print(event.player.name)
