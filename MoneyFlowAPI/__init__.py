import os
import platform
from configparser import ConfigParser
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def create_default_config(config_path: Path):
    def_conf = ConfigParser()
    def_conf["Main"] = {
        "templates": os.path.join(config_path, "templates"),
    }
    def_conf["DB"] = {
        "engine": 'sqlite',
        "name": os.path.join(config_path, "moneyflow.sqlite3"),
    }
    with open(os.path.join(config_path, "config.ini"), "w") as configfile:
        def_conf.write(configfile)


def load_config(config_path: Path) -> ConfigParser:
    os.makedirs(config_path, exist_ok=True)
    config_file = os.path.join(config_path, "config.ini")

    if not os.access(config_path, os.W_OK):
        raise ImproperlyConfigured(f"{config_path} is not writeable!")

    config = ConfigParser()
    if not os.path.isfile(config_file):
        create_default_config(config_path)
    config.read(config_file)
    return config


def get_platform_config_path() -> Path:
    env_path = os.getenv('CONFIG_PATH')
    config_path = Path(os.getcwd(), 'config')

    if env_path:
        config_path = Path(env_path)
        return config_path
    current_os = platform.system()
    is_docker = False

    if os.path.exists('/.dockerenv'):
        is_docker = True

    if current_os == "Windows":
        config_path = Path(os.path.join(os.getenv("APPDATA"), "MoneyFlowAPI"))
        print("Running on Microsoft Windows")

    elif current_os == "Linux":
        if is_docker:
            config_path = Path("/MoneyFlowAPI/config")
            print("Running on Docker Container")
        else:
            config_path = Path(os.path.join(os.getenv("HOME"), ".config", "MoneyFlowAPI"))
            print("Running on a Linux distribution")

    elif current_os == "Darwin":
        config_path = Path(os.path.join(os.getenv("HOME"), "Library", "Application Support", "MoneyFlowAPI"))
        print("Running on macOS (Darwin kernel)")

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
