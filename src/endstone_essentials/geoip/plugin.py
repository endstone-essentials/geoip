from endstone.plugin import Plugin

from endstone_essentials.geoip.listener import EssentialsGeoIPPlayerListener


class EssentialsGeoIP(Plugin):
    name = "EssentialsGeoIP"
    api_version = "0.4"

    def on_enable(self) -> None:
        listener = EssentialsGeoIPPlayerListener()
        self.register_events(listener)
        self.logger.info("This product includes GeoLite2 data created by MaxMind, "
                         "available from https://www.maxmind.com/.")
