# edwh-pipcompile-plugin

[![PyPI - Version](https://img.shields.io/pypi/v/edwh-pipcompile-plugin.svg)](https://pypi.org/project/edwh-pipcompile-plugin)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edwh-pipcompile-plugin.svg)](https://pypi.org/project/edwh-pipcompile-plugin)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)
- [Changelog](#changelog)

## Installation

```console
pip install edwh-pipcompile-plugin
```

But probably you want to install the whole edwh package:

```console
pipx install edwh[pip]
# or
pipx install edwh[plugins,omgeving]
```

## Usage

To see all available subcommands or get help for a specific command, you can use:

```bash
edwh help pip
edwh help pip.compile
```

You can use `pip.compile` (and `pip.upgrade`, etc.) in multiple ways.
You can run it on a specific file: `ew pip.compile <myfile.in>`. This will result in a `myfile.txt`.
You can run it on a directory: `ew pip.compile <mydirectory>` or `ew pip.compile .`.
This will transform all `.in` files into `.out` files (with the same name):

- `mydirectory/first.in` -> `mydirectory/first.txt`
- `mydirectory/second.in` -> `mydirectory/second.txt`

You can also add `--combine` to combine multiple `.in` files into a single `.txt` file (
called `<directory>/requirements.txt`).

If you want to modify this behavior, you can do so via `pyproject.toml`:
```toml
[tool.edwh.pipcompile.directory]
input = ["first.in", "../second.in"] # will ignore other .in files;
# transformed to directory/first.in and ./second.in
output = "output.txt" # directory/output.txt
```

Where 'directory' is the name of a specific folder. 
You can use the special symbol `__cwd__` to target the project folder.

## License

`edwh-pipcompile-plugin` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Changelog

[See CHANGELOG.md](CHANGELOG.md)