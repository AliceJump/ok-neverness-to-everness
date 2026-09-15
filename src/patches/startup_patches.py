from __future__ import annotations

import sys

from ok.core.ui_config import resolve_ui_config

_PATCH_INSTALLED = False


def is_qt_mode(config, argv=None):
    ui_config = resolve_ui_config(config)
    arguments = sys.argv[1:] if argv is None else argv
    return (
        ui_config is not None
        and ui_config["type"] == "qt"
        and not any(argument in {"-h", "--headless"} for argument in arguments)
    )


def install_startup_patches(config):
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return

    from src.patches.i18n_patch import install_i18n_patch

    install_i18n_patch()
    if is_qt_mode(config):
        from src.patches.task_tab_patch import install_task_tab_patch

        install_task_tab_patch()
    _PATCH_INSTALLED = True
