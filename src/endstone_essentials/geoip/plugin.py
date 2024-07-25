import gzip
import os
import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

import requests
from endstone.plugin import Plugin

from endstone_essentials.geoip.listener import EssentialsGeoIPPlayerListener


class EssentialsGeoIP(Plugin):
    prefix = "EssentialsGeoIP"
    api_version = "0.4"

    def __init__(self):
        super().__init__()
        self.database_file: Path | None = None

    def on_enable(self) -> None:
        self.save_default_config()

        listener = EssentialsGeoIPPlayerListener()
        self.register_events(listener)
        self.logger.info(
            "This product includes GeoLite2 data created by MaxMind, " "available from https://www.maxmind.com/."
        )
        self.load_database()

    def load_database(self):
        """
        Load the GeoIP database file.

        :return: None
        """
        database_cfg = self.config.get("database", {})
        if database_cfg.get("show-cities", False):
            self.database_file = Path(self.data_folder) / "GeoIP2-City.mmdb"
        else:
            self.database_file = Path(self.data_folder) / "GeoIP2-Country.mmdb"

        if not self.database_file.exists():
            if not database_cfg.get("download-if-missing", False):
                self.logger.error("Cannot find GeoIP database file")
                return

            self.download_database()
        else:
            update_cfg = database_cfg.get("update", {})
            if update_cfg.get("enabled", True):
                mod_time = datetime.fromtimestamp(self.database_file.stat().st_mtime)
                curr_time = datetime.now()
                if (curr_time - mod_time).days > update_cfg.get("by-every-x-days", 30):
                    self.download_database()

    def download_database(self):
        """
        Download the GeoIP database based on the configuration settings.

        :return: None
        """
        database_cfg = self.config.get("database", {})
        url: str | None

        if database_cfg.get("show-cities", False):
            url = database_cfg.get("download-url-city", None)
        else:
            url = database_cfg.get("download-url", None)

        if not url:
            self.logger.error("Empty GeoIP database URL")
            return

        license_key = database_cfg.get("license-key", None)
        if not license_key:
            self.logger.error("GeoIP database license key missing")
            return

        url = url.format(LICENSEKEY=license_key)
        self.logger.info("Downloading GeoIP database... This may take a while depending on your Internet speed.")

        with tempfile.NamedTemporaryFile(dir=self.data_folder, delete=False) as tf:
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        tf.write(chunk)

                tf.flush()

            else:
                self.logger.error("Failed to download database with response code " + str(response.status_code))
                tf.close()
                os.unlink(tf.name)
                return

        if url.endswith(".tar.gz"):
            with tarfile.open(tf.name, "rb") as tar:
                tar.extract(tar.getmembers()[0], self.database_file)
        elif url.endswith(".gz"):
            with gzip.open(tf.name, "rb") as f_in:
                with self.database_file.open("wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy(tf.name, self.database_file)

        tf.close()
        os.unlink(tf.name)
