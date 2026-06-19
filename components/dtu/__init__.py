import esphome.config_validation as cv
from esphome.const import (
    __version__ as ESPHOME_VERSION,
)

if cv.Version.parse(ESPHOME_VERSION) > cv.Version.parse("2026.1.99"):
    from esphome.components.esp32 import include_builtin_idf_component

CODEOWNERS = ["@dentra"]


async def to_code(config):
    if cv.Version.parse(ESPHOME_VERSION) > cv.Version.parse("2026.1.99"):
        include_builtin_idf_component("esp_http_client")
