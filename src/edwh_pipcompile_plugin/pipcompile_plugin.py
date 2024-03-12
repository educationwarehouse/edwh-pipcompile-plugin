"""
Dit script maakt het werken met pip-tools nog iets slimmer.
De volgende commando's zijn beschikbaar:
- pip.compile
- pip.install
- pip.remove
- pip.upgrade

Het verschil met standaard pip-tools is dat operations zoals install, remove en upgrade ook aanpassingen in de .in file
kunnen doen. Compile werkt hetzelfde, maar het is fijn om alle related commando's onder invoke pip.* te hebben.
"""

import glob
import os
import re
import typing
import warnings
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from types import TracebackType
from typing import Optional

import tomli
from edwh.helpers import kwargs_to_options
from edwh.meta import _python
from invoke import Context, run, task
from termcolor import cprint
from typing_extensions import Unpack

DEFAULT_SERVER = None  # pypi default


def pip_compile_executable(python: Optional[str] = None):
    # python = '/home/eddie/.local/pipx/venvs/edwh/bin/python'
    # -> /home/eddie/.local/pipx/venvs/edwh/bin/pip-compile
    if python is None:
        python = _python()

    command_parts = python.split("/")
    # command_parts[-1] = "pip-compile"
    command_parts[-1] = "uv pip compile"
    return "/".join(command_parts)


PIP_COMPILE = pip_compile_executable()

ConfigDict = typing.TypedDict(
    "ConfigDict",
    {
        # pip-tools:
        "output-file": str,
        "upgrade": bool,
        "i": str,  # pypi_server/--index-url
        "upgrade-package": str,
        "resolver": str,
        # and more but we don't really use that.
        # ...
        # internal:
        "combine": bool,
    },
    total=False,
)


class Color:
    """
    Holder for common ANSI color codes
    Usage:
    print(Color.OKBLUE, "something colored blue", Color.ENDC, "normal color")
    """

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def info(*a, **kw):
    """
    Print something in blue
    """
    # print(Color.OKBLUE, *a, Color.ENDC, **kw)
    cprint(*a, **kw, color="blue")


def success(*a, **kw):
    """
    Print something in green
    """
    cprint(*a, **kw, color="green")
    # print(Color.OKGREEN, *a, Color.ENDC, **kw)


def warn(*a, **kw):
    """
    Print something in yellow
    """
    cprint(*a, **kw, color="yellow")
    # print(Color.WARNING, *a, Color.ENDC, **kw)


def error(*a, **kw):
    """
    Print something in red
    """
    cprint(*a, **kw, color="red")
    # print(Color.FAIL, *a, Color.ENDC, **kw)


class show_diff:
    """
    Context manager to show the before and after of a filename (comparing the changes made within the context)
    """

    def __init__(self, file_name: str | Path):
        self.file = Path(file_name)
        self.file.touch(exist_ok=True)

        self.pre = ""
        self.post = ""

    def _read(self):
        with self.file.open() as f:
            return f.read()

    @staticmethod
    def __show_diff(first, second):
        for text in unified_diff(first.split("\n"), second.split("\n")):
            if text[:3] not in ("+++", "---", "@@ "):
                match text[0]:
                    case "+":
                        color = "green"
                    case "-":
                        color = "red"
                    case _:
                        color = None

                cprint(text, color=color)

    @property
    def has_difference(self):
        return self.pre != self.post

    def _show_diff(self):
        first = self.pre
        second = self.post

        self.__show_diff(first, second)

    def __enter__(self):
        self.pre = self._read()

    def __exit__(self, exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType):
        if traceback:
            return

        self.post = self._read()
        if self.has_difference:
            info("Difference: ")
            self._show_diff()
        else:
            warn("No difference.")


@dataclass
class rollback:
    """
    Context manager to roll back changes in a file on error
    """

    pre: str
    file: str

    def __enter__(self):
        pass

    def __exit__(self, exc_type: type[BaseException], exc_value: BaseException, traceback: TracebackType):
        if not traceback:
            # nothing on the hand
            return

        with open(self.file, "w") as f:
            if not self.pre:
                return
            warn(f"Rolling back changes in {self.file}")
            f.write(self.pre)


def in_to_out(filename: str | Path) -> Path:
    """
    Convert the .in filename to .txt (requirements.in -> requirements.txt)
    """
    return Path(filename).with_suffix(".txt")


def _pip_compile(*args: str, output_file: str, **kwargs: Unpack[ConfigDict]):
    """
    Execute pip-compile with positional and keyword args
    """
    kwargs.pop("combine", None)  # internal use only, not for pip-compile

    extra = {"output-file": output_file}

    run(f"{PIP_COMPILE} " + " ".join(args) + kwargs_to_options(kwargs, **extra), hide=True)


def _get_output_dir(filename: str | Path) -> Path:
    # Get the directory name from the filename
    dirname = os.path.dirname(str(filename))

    # Check if dirname is empty or the same as the current directory
    if not dirname or dirname == ".":
        return Path("./")
    else:
        return Path(dirname)


def _combine_infiles(paths: typing.Sequence[str | Path], kwargs: ConfigDict) -> list[str]:
    tempdir = Path("/tmp/edwh-pipcompile")
    tempdir.mkdir(exist_ok=True, parents=True)
    combined_infile = tempdir / "requirements.in"

    output_dir = _get_output_dir(paths[0])
    kwargs["output-file"] = kwargs.get("output-file") or str(output_dir / "requirements.txt")

    paths = [Path(_) for _ in paths]

    with combined_infile.open("wb") as f_out:
        for file in paths:
            if not file.exists():
                continue

            f_out.write(file.read_bytes() + b"\n")

    return [str(combined_infile)]


def process_file_input(directory):
    if isinstance(directory, list):
        return directory
    elif isinstance(directory, str) and "," in directory:
        warnings.warn(
            "',' via 'find_infiles' is no longer supported. Please split beforehand!", category=DeprecationWarning
        )
        return [_.strip() for _ in directory.split(",")]
    else:
        return [directory]


def pyproject_settings():
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        return {}

    full = tomli.loads(pyproject.read_text())
    return full.get("tool", {}).get("edwh", {}).get("pipcompile", {})


def relative_resolve(base: str | Path, filename: str | Path) -> str:
    """
    Given a base of 'directory', and a filename of '../myfile.txt',
    this can be resolved to 'myfile.txt' (implicit ./)
    """
    if isinstance(base, str):
        base = Path(base)

    root = f"{Path.cwd()}/"

    if isinstance(filename, str):
        filename = Path(filename)

    return str((base / filename).resolve()).removeprefix(root)


def from_config(directory: str, mut_kwargs: ConfigDict, settings: dict) -> list[str]:
    directory_raw = directory
    directory = directory.strip("/")
    if directory == ".":
        # ✨ special ✨
        directory = "__cwd__"

    if not (setting := settings.get(directory)):
        # nope
        return []

    directory_p = Path(directory_raw)  # raw is '.' instead of __cwd__ and with original slashes.

    if output_file := setting.get("output"):
        if not isinstance(output_file, str):
            raise TypeError(f"'output' can only be a string, not a {type(output_file).__name__}.")

        # existing kwargs has priority
        output_file = relative_resolve(directory_p, output_file)
        mut_kwargs["output-file"] = mut_kwargs.get("output-file") or output_file
        mut_kwargs["combine"] = True  # if an output file is included, the input files should be combined

    if input_files := setting.get("input"):
        return [
            # relative to the directory.
            # if you want to target a level up,
            # you can just use '../somefile.in' thanks to resolve()
            relative_resolve(directory_p, file)
            for file in input_files
        ]

    return []


def get_glob_pattern(directory: Optional[str], mut_kwargs: ConfigDict, settings: dict):
    if not directory.endswith(".in"):
        # ./somepath/
        if input_files := from_config(directory, mut_kwargs, settings):
            # [tool.edwh.pipcompile.somepath]
            return input_files

        pattern = f"{directory}/*.in" if directory else "*.in"
        return glob.glob(pattern)
    else:
        # ./somepath/*.in
        return glob.glob(directory)


def process_directory(directory: str, mut_kwargs: ConfigDict, settings: dict) -> list[str]:
    glob_iter = get_glob_pattern(directory, mut_kwargs, settings)

    if mut_kwargs.get("combine"):
        return _combine_infiles(list(glob_iter), mut_kwargs)
    else:
        return glob_iter


def yield_files(directories: list[str], mut_kwargs: ConfigDict, settings: dict):
    for directory in directories:
        yield from process_directory(directory, mut_kwargs, settings)


def find_infiles(
    directory: str | Path | list[str] | None = None,
    kwargs: Optional[ConfigDict] = None,
) -> typing.Generator[str, None, None]:
    """
    Iterate over files ending with .in (in the current directory)
    """
    if kwargs is None:
        kwargs = {}

    settings = pyproject_settings()

    # paths = directories or specific files/globs
    paths = process_file_input(directory)

    yield from yield_files(paths, kwargs, settings)


def extract_package_info(package: str) -> tuple[str, str, str]:
    """
    From a possibly pinned package string (e.g. edwh-ghost==0.01)
    extract the package info as a tuple of name, operator, version
    """
    package_re = re.compile(r"^(.+?) ?($|[><=]+)(.+)?", re.IGNORECASE)
    if _res := package_re.findall(package):
        return _res[0]
    else:
        return package, ">", "0"


# compiled with {package} later
PACKAGE_RE = r"^({package}) ?($|[><=]+(.*))"


def compile_package_re(package: str) -> re.Pattern:
    """
    Complete the PACKAGE_RE for a specific package
    """
    return re.compile(
        PACKAGE_RE.format(package=package),
        re.MULTILINE | re.IGNORECASE,
    )


# ## ONLY @task's AFTER THIS!!!


def compile_infile(_: Context, path: str, combine: bool, pypi_server: str = DEFAULT_SERVER):
    """
    Compile a specific .in file or directory with .in files.

    See `compile_infiles` for the normal usage.
    """
    args: ConfigDict = {
        "combine": combine,
    }
    files = find_infiles(path, args)
    if pypi_server:
        args["i"] = pypi_server
    for file in files:
        output_file = args.get("output-file", in_to_out(file))
        _pip_compile(file, output_file=output_file, **args)
        success(f"Ran compile! Check {output_file}")


@task(name="compile")
def compile_infiles(_, paths: str, pypi_server: Optional[str] = DEFAULT_SERVER, combine: bool = False):
    """
    Task (invoke pip.compile) to run pip-compile on one or more files (-f requirements1.in -f requirements2.in)

    Arguments:
        _ (invoke.Context): invoke context
        paths (str): path to directory to compile infiles or specific infile
        pypi_server (str): which server to get files from?
        combine (bool): if multiple .in files exist in the target directory, merge them to one requirements.txt?

    Examples:
        pip.compile .
        pip.compile ./requirements.in
    """
    for path in paths.split(","):
        compile_infile(_, path, combine, pypi_server)


def install_into_path(ctx: Context, path: str, package: str, combine: bool, pypi_server: str = DEFAULT_SERVER):
    """
    Install a new package for a specific infile.

    See `install` for normal usage.
    """
    args: ConfigDict = {"combine": combine}
    files = find_infiles(path, args)
    for file in files:
        with open(file, "r") as f:
            contents = f.read()

        _package, *_ = extract_package_info(package)

        if compile_package_re(_package).search(contents):
            error(f"Warning: {_package} already installed, use pip-upgrade to upgrade. ")
            continue

        with open(file, "a") as f:
            f.write("\n" + package)

        success(f"Installing {package} in {file}")

        # post: pip-compile
        output_file = args.get("output-file", in_to_out(file))
        with rollback(contents, file), show_diff(output_file):
            compile_infiles(ctx, paths=path, pypi_server=pypi_server)


@task()
def install(ctx, paths, package, pypi_server=DEFAULT_SERVER, combine: bool = False):
    """
    Install a package to the .in file of the specified directory and re-compile the requirements.txt
    The command also checks if the command is already added and if it exists on the specified pypi server

    Arguments:
        ctx (invoke.Context): invoke context
        paths (str): path to directory to compile infiles or specific infile
        package (str): package name to install
        pypi_server (str): which server to get files from?

    Examples:
        pip.install . black
        pip.install . --package black
    """
    for path in paths.split(","):
        install_into_path(ctx, path, package, combine, pypi_server)


def upgrade_infile(
    _: Context, path: str, package: str | None, combine: bool, force: bool, pypi_server: str = DEFAULT_SERVER
):
    """
    Upgrade the packages of a specific infile or folder with infiles.

    See `upgrade` for normal usage.
    """
    args: ConfigDict = {
        "combine": combine,
    }
    files = find_infiles(path, args)
    for file in files:
        with open(file) as f:
            contents = f.read()

        out = args.get("output-file", in_to_out(file))
        args["upgrade"] = True
        if pypi_server:
            args["i"] = pypi_server

        if package:
            _package, operator, version = extract_package_info(package)

            reg = compile_package_re(_package)

            dependency = reg.findall(contents)

            if not dependency:
                error(
                    f"Package {_package} not installed in {file}! "
                    f"Please use `invoke pip-install` to add this dependency."
                )
                continue

            if force or (operator and version):
                with open(file, "w") as f:
                    f.write(reg.sub(package, contents))
            elif dep_version := dependency[0][2]:
                warn(f"{package} is pinned to {dep_version} in {file}. Use --force to upgrade anyway.")
                continue
            # arg = f'--upgrade-package "{package}"'
            args["upgrade-package"] = package

            info(f"Upgrading {package} in {file}")
        else:
            info(f"Upgrading all in {file}")

        with rollback(contents, file), show_diff(out):
            # GEEN post: pip-compile, want --arg is nodig
            # ctx.run(f'pip-compile {arg} {file}')
            _pip_compile(file, output_file=out, **args)

        success(f"Upgrade complete. Check {out}")


@task(iterable=["files"])
def upgrade(_, paths, package=None, force=False, pypi_server=DEFAULT_SERVER, combine: bool = False):
    """
    Upgrade package(s) in one or multiple infiles. Version pins will be respected,
    unless a specific package with --force or a specific package with a new pin is supplied.

    Arguments:
        _ (invoke.Context): invoke context
        paths (str): path to directory to compile infiles or specific infile
        package (str): package name to install
        force (bool): if the version is pinned, remove pin and upgrade?
        pypi_server (str): which server to get files from?
        combine (bool): if multiple .in files exist in the target directory, merge them to one requirements.txt?

    Example:
        invoke pip.upgrade . --package black --force
    """
    for path in paths.split(","):
        upgrade_infile(_, path, package, combine, force, pypi_server)


def remove_from_path(ctx: Context, path: str, _package: str, pypi_server: str = DEFAULT_SERVER):
    """
    Remove a package for a specific infile.

    See `remove` for normal usage.
    """
    args = {}
    # first try with path, then without
    files = find_infiles(path, args) or find_infiles(kwargs=args)
    for file in files:
        with open(file) as f:
            contents = f.read()

        reg = compile_package_re(_package)
        if not reg.search(contents):
            error(f"Package {_package} not installed in {file}!")
            continue
        # else

        new_deps = compile_package_re(_package).sub("", contents)
        new_deps = new_deps.replace("\n\n", "\n")  # remove empty line
        with open(file, "w") as f:
            f.write(new_deps)

        output_file = args.get("output-file", in_to_out(file))
        with show_diff(output_file):  # no rollback required since pip compile can't fail on remove
            compile_infiles(ctx, paths=path, pypi_server=pypi_server)

        success(f"Package {_package} removed from {file}")


@task(
    iterable=["files"]
    # post=[pip_compile],
)
def remove(ctx, paths, package, pypi_server=DEFAULT_SERVER):
    """
    Remove a package from one or multiple infiles

    Arguments:
        ctx (invoke.Context): invoke context
        paths (str): path to directory to compile infiles or specific infile
        package (str): package name to install
        pypi_server (str): which server to get files from?

    Examples:
        pip.remove . black
        pip.remove . --package black
    """
    _package, *_ = extract_package_info(package)

    for path in paths.split(","):
        remove_from_path(ctx, path, _package, pypi_server)
