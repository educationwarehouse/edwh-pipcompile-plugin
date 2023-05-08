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
import typing
from dataclasses import dataclass
import re
from invoke import run, task
from pathlib import Path
from difflib import unified_diff

DEFAULT_SERVER = None  # pypi default


# DEFAULT_SERVER = "https://devpi.edwh.nl/remco/dev/+simple"

# DEFAULT_OUT = 'py4web_requirements.txt'


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
    print(Color.OKBLUE, *a, Color.ENDC, **kw)


def success(*a, **kw):
    """
    Print something in green
    """
    print(Color.OKGREEN, *a, Color.ENDC, **kw)


def warn(*a, **kw):
    """
    Print something in yellow
    """
    print(Color.WARNING, *a, Color.ENDC, **kw)


def error(*a, **kw):
    """
    Print something in red
    """
    print(Color.FAIL, *a, Color.ENDC, **kw)


class show_diff:
    """
    Context manager to show the before and after of a filename (comparing the changes made within the context)
    """

    def __init__(self, file_name):
        self.file_name = file_name

        self.pre = ""
        self.post = ""

    def _read(self):
        with open(self.file_name) as f:
            return f.read()

    @staticmethod
    def __show_diff(first, second):
        for text in unified_diff(first.split("\n"), second.split("\n")):
            if text[:3] not in ("+++", "---", "@@ "):
                print(text)

    def _show_diff(self):
        first = self.pre
        second = self.post

        self.__show_diff(first, second)

    def __enter__(self):
        self.pre = self._read()

    def __exit__(self, type, value, traceback):
        if traceback:
            return

        self.post = self._read()
        info("Difference: ")
        self._show_diff()


@dataclass
class rollback:
    """
    Context manager to roll back changes in a file on error
    """

    pre: str
    file: str

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
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


def kwargs_to_options(data: dict = None, **kw) -> str:
    """
    Convert a dictionary of options to the cli variant
    e.g. {'a': 1, 'key': 2} -> -a 1 --key 2
    """
    if data:
        kw |= data

    options = []
    for key, value in kw.items():
        if value in (None, "", False):
            # skip falsey, but keep 0
            continue

        pref = ("-" if len(key) == 1 else "--") + key

        if isinstance(value, bool):
            options.append(f"{pref}")

        elif isinstance(value, list):
            options.extend(f"{pref} {subvalue}" for subvalue in value)
        else:
            options.append(f"{pref} {value}")

    return " " + " ".join(options)


def _pip_compile(*args, **kwargs):
    """
    Execute pip-compile with positional and keyword args
    """
    if "resolver" not in kwargs:
        kwargs["resolver"] = "backtracking"

    run("pip-compile " + " ".join(args) + kwargs_to_options(kwargs))


def _find_infiles(directory: str | Path = None) -> typing.Iterator:
    """
    Iterate over files ending with .in (in the current directory)
    """

    if directory and str(directory).endswith(".in"):
        # already one file!
        yield str(directory)
        return

    if directory:
        _glob = f"{directory}/*.in"
    else:
        _glob = "*.in"

    yield from glob.glob(_glob)


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


### ONLY @task's AFTER THIS!!!


@task()
def compile(_, path, pypi_server=DEFAULT_SERVER):
    """
    Task (invoke pip.compile) to run pip-compile on one or more files (-f requirements1.in -f requirements2.in)

    Arguments:
        _ (invoke.Context): invoke context
        path (str): path to directory to compile infiles or specific infile
        pypi_server (str): which server to get files from?

    Examples:
        pip.compile .
        pip.compile ./requirements.in
    """
    files = _find_infiles(Path(path))

    args = {}

    if pypi_server:
        args["i"] = pypi_server

    for file in files:
        _pip_compile(file, **args)

        success(f"Ran pip-compile! Check {in_to_out(file)}")


@task()
def install(ctx, path, package, pypi_server=DEFAULT_SERVER):
    """
    Install a package to the .in file of the specified directory and re-compile the requirements.txt
    The command also checks if the command is already added and if it exists on the specified pypi server

    Arguments:
        ctx (invoke.Context): invoke context
        path (str): path to directory to compile infiles or specific infile
        package (str): package name to install
        pypi_server (str): which server to get files from?

    Examples:
        pip.install . black
        pip.install . --package black
    """
    files = _find_infiles(Path(path))

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
        with rollback(contents, file), show_diff(in_to_out(file)):
            compile(ctx, path=path, pypi_server=pypi_server)


@task(iterable=["files"])
def upgrade(ctx, path, package=None, force=False, pypi_server=DEFAULT_SERVER):
    """
    Upgrade package(s) in one or multiple infiles. Version pins will be respected,
    unless a specific package with --force or a specific package with a new pin is supplied.

    Arguments:
        ctx (invoke.Context): invoke context
        path (str): path to directory to compile infiles or specific infile
        package (str): package name to install
        force (bool): if the version is pinned, remove pin and upgrade?
        pypi_server (str): which server to get files from?

    Example:
        invoke pip.upgrade . --package black --force
    """
    files = _find_infiles(Path(path))

    for file in files:
        with open(file, "r") as f:
            contents = f.read()

        out = in_to_out(file)
        args = {"upgrade": True}
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
                warn(
                    f"{package} is pinned to {dep_version} in {file}. Use --force to upgrade anyway."
                )
                continue
            # arg = f'--upgrade-package "{package}"'
            args["upgrade-package"] = package

            success(f"Upgrading {package} in {file}")
        else:
            success(f"Upgrading all in {file}")

        with rollback(contents, file), show_diff(out):
            # GEEN post: pip-compile, want --arg is nodig
            # ctx.run(f'pip-compile {arg} {file}')
            _pip_compile(file, **args)

        success("Upgrade complete.")


@task(
    iterable=["files"]
    # post=[pip_compile],
)
def remove(ctx, path, package, pypi_server=DEFAULT_SERVER):
    """
    Remove a package from one or multiple infiles

    Arguments:
        ctx (invoke.Context): invoke context
        path (str): path to directory to compile infiles or specific infile
        package (str): package name to install
        pypi_server (str): which server to get files from?

    Examples:
        pip.remove . black
        pip.remove . --package black
    """
    _package, *_ = extract_package_info(package)
    files = _find_infiles(Path(path))

    if not files:
        files = _find_infiles()

    for file in files:
        with open(file, "r") as f:
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

        with show_diff(in_to_out(file)):  # no rollback required since pip compile can't fail on remove
            compile(ctx, path=path, pypi_server=pypi_server)

        success(f"Package {_package} removed from {file}")
