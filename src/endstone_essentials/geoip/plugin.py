import gzip
import shutil
import tarfile
import tempfile

import requests
from endstone.plugin import Plugin

from endstone_essentials.geoip.listener import EssentialsGeoIPPlayerListener


class EssentialsGeoIP(Plugin):
    name = "EssentialsGeoIP"
    api_version = "0.4"

    def on_enable(self) -> None:
        self.save_default_config()

        listener = EssentialsGeoIPPlayerListener()
        self.register_events(listener)
        self.logger.info("This product includes GeoLite2 data created by MaxMind, "
                         "available from https://www.maxmind.com/.")
        self.download_database()

    def download_database(self):
        database = self.config.get("database", {})
        url: str | None
        if database.get("show-cities", False):
            url = database.get("download-url-city", None)
        else:
            url = database.get("download-url", None)

        if not url:
            self.logger.error("Empty GeoIP database URL")
            return

        license_key = database.get("license-key", None)
        if not license_key:
            self.logger.error("GeoIP database license key missing")
            return

        url = url.format(LICENSEKEY=license_key)
        self.logger.info("Downloading GeoIP database... This may take a while depending on your Internet speed.")

        with tempfile.NamedTemporaryFile(dir=self.data_folder) as tf:
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        tf.write(chunk)

                tf.flush()

                filepath = tf.name
                filename = url.split("/")[-1]

                if filename.endswith('.gz') or filename.endswith('.tar.gz'):
                    if filename.endswith('.tar.gz'):
                        with tarfile.open(tf.name) as tar:
                            tar.extractall(self.data_folder)

                    elif filename.endswith('.gz'):
                        with gzip.open(filepath, 'rb') as f_in:
                            with open(self.data_folder, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)

            else:
                self.logger.error("Failed to download database with response code " + str(response.status_code))
