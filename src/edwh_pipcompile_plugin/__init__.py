# SPDX-FileCopyrightText: 2023-present Remco Boerma <remco.b@educationwarehouse.nl>
#
# SPDX-License-Identifier: MIT

from .pipcompile_plugin import compile_infile, install, remove, upgrade

__all__ = [
    "compile_infile",
    "install",
    "remove",
    "upgrade",
]
