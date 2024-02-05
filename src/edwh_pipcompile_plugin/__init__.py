# SPDX-FileCopyrightText: 2023-present Remco Boerma <remco.b@educationwarehouse.nl>
#
# SPDX-License-Identifier: MIT

from .pipcompile_plugin import compile_infiles, install, remove, upgrade

compile_infile = compile_infiles  # alias for backwards compat

__all__ = [
    "compile_infile",
    "compile_infiles",
    "install",
    "remove",
    "upgrade",
]
