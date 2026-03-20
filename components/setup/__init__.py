import logging

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import core
from esphome import cpp_generator as cpp
from esphome.const import CONF_ID, CONF_LAMBDA
from esphome.core import CORE, CoroPriority, coroutine_with_priority
from esphome.types import ConfigType

CONF_DEPENDS = "depends"
CONF_FINAL = "final"

CONFIG_SCHEMA = cv.ensure_list(
    cv.Any(
        cv.lambda_,
        cv.Schema(
            {
                cv.Optional(CONF_DEPENDS): cv.ensure_list(cv.string),
                cv.Required(CONF_LAMBDA): cv.lambda_,
                cv.Optional(CONF_FINAL, default=False): cv.boolean,
            }
        ),
    )
)


def _get_deps(config: ConfigType):
    deps = []
    for dep in config.get(CONF_DEPENDS, []):
        parts = str(dep).split(" as ")
        deps.append(
            {
                "key": parts[0].strip(),
                "var": parts[1].strip() if len(parts) == 2 else "",
            }
        )
    return deps


@coroutine_with_priority(CoroPriority.FINAL - 1)
async def _generate_code(config: ConfigType, onlyFinal: bool):
    for conf in config:
        if conf.get(CONF_FINAL, False) != onlyFinal:
            continue

        if isinstance(conf, cv.Lambda):
            conf = {CONF_LAMBDA: conf}

        deps = _get_deps(conf)
        if not set([dep["key"] for dep in deps]).issubset(core.CORE.config):
            continue
        lambda_: cpp.LambdaExpression = await cg.process_lambda(conf[CONF_LAMBDA], [])
        content = lambda_.content
        if lambda_.source:
            content = f"{lambda_.source.as_line_directive}\n{content}"
        vars = "\n".join(
            [
                f"auto *{dep['var']} = {core.CORE.config[dep['key']][CONF_ID]};"
                for dep in deps
                if dep["var"]
            ]
        )
        if vars:
            vars += "\n"
        content = cpp.indent_all_but_first_and_last(f"{{\n{vars}{content}\n}}")
        cg.add(cg.RawStatement(content))


@coroutine_with_priority(CoroPriority.WORKAROUNDS)
async def to_code(config: ConfigType):
    await _generate_code(config, False)
    CORE.add_job(_generate_code, config, True)
