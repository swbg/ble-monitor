import os

import yaml


class Config:
    def __init__(self):
        self.config = {}

    def set_config(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def update_config(self, config_path: str):
        with open(config_path, "r") as f:
            self.config.update(yaml.safe_load(f))

    def get(self, key: str):
        value = self.config.get(key)
        if value is None:
            return os.environ.get(key)
        return value


config = Config()
