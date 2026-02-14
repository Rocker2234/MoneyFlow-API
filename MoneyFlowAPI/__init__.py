import os
import platform
from configparser import ConfigParser
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


# Time zone name form: https://data.iana.org/time-zones/tzdb-2021a/zone1970.tab
# Python date format: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes

def default_config(config_path: Path) -> ConfigParser:
    def_conf = ConfigParser()
    def_conf["Main"] = {
        "home_tz": "UTC",
        "templates": os.path.join(config_path, "templates"),
    }
    def_conf["DB"] = {
        "engine": 'sqlite',
        "name": os.path.join(config_path, "moneyflow.sqlite3"),
    }

    return def_conf


def load_config(config_path: Path) -> ConfigParser:
    os.makedirs(config_path, exist_ok=True)
    config_file = os.path.join(config_path, "config.ini")

    if not os.access(config_path, os.W_OK):
        raise ImproperlyConfigured(f"{config_path} is not writeable!")

    config = default_config(CONFIG_PATH)
    if not os.path.isfile(config_file):
        with open(os.path.join(config_path, "config.ini"), "w") as configfile:
            config.write(configfile)
    config.read(config_file)
    print(f"Home TZ: {config.get("Main", "home_tz")}")
    print(f"Templates: {config.get("Main", "templates")}")
    print(f"DB: {config.get("DB", "engine")}")
    print(f"DB NAME: {config.get("DB", "name")}")
    return config


def get_platform_config_path() -> Path:
    env_path = os.getenv('CONFIG_PATH')
    config_path = Path(os.getcwd(), 'config')

    if env_path:
        config_path = Path(env_path)
        return config_path
    current_os = platform.system()
    is_docker = False

    print(f"Running on {current_os}.")

    if os.path.exists('/.dockerenv'):
        is_docker = True

    if current_os == "Windows":
        config_path = Path(os.path.join(os.getenv("APPDATA"), "MoneyFlowAPI"))

    elif current_os == "Linux":
        if is_docker:
            config_path = Path("/MoneyFlowAPI/config")
            print("Running on Docker Container")
        else:
            config_path = Path(os.path.join(os.getenv("HOME"), ".config", "MoneyFlowAPI"))

    elif current_os == "Darwin":
        config_path = Path(os.path.join(os.getenv("HOME"), "Library", "Application Support", "MoneyFlowAPI"))

    return config_path


print("Initializing MoneyFlowAPI...")
CONFIG_PATH = get_platform_config_path()
USER_SETTINGS = load_config(CONFIG_PATH)
os.makedirs(USER_SETTINGS.get("Main", "templates"), exist_ok=True)

db_engine_mapping = {
    'postgres': 'django.db.backends.postgresql',
    'mysql': 'django.db.backends.mysql',
    'sqlite': 'django.db.backends.sqlite3',
    'oracle': 'django.db.backends.oracle'
}

if USER_SETTINGS.get('DB', 'engine') not in db_engine_mapping.keys():
    raise ImproperlyConfigured(f"{USER_SETTINGS.get('DB', 'engine')} is not supported!")
