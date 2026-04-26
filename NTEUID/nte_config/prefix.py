from gsuid_core.sv import get_plugin_available_prefix


def nte_prefix() -> str:
    return get_plugin_available_prefix("NTEUID")
