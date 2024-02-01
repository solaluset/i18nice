"""
This script automates testing and code quality checks
It stashes unstaged changes before testing to ensure accurate results
It also automatically manages virtual environment and dependencies
Run "python dev-helper.py install" to install it as pre-commit hook in this repository
"""

import os
import sys
import stat
import shlex
import sysconfig
import subprocess
from contextlib import contextmanager


VENV_DIR = "dev_env"
REQUIREMENTS = "requirements/dev-requirements.txt"
ON_CI = bool(os.getenv("CI"))
SKIP_VENV = ON_CI or os.getenv("SKIP_VENV") == "1"


def get_root():
    return subprocess.check_output(
        ("git", "rev-parse", "--show-toplevel"),
        universal_newlines=True,
    ).strip()


os.chdir(get_root())
sys.argv[0] = os.path.basename(sys.argv[0])


def ensure_venv(packages):
    venv_dir = os.path.join(os.getcwd(), VENV_DIR)
    if sys.prefix == venv_dir or SKIP_VENV:
        # already in venv or skipping
        print("Installing packages...")
        pip_install(sys.executable, packages)
        return
    if not os.path.isdir(venv_dir):
        print("Creating virtual environment...")
        subprocess.run((sys.executable, "-m", "venv", venv_dir), check=True)
    python_path = os.path.join(
        sysconfig.get_path("scripts", "venv", {"base": venv_dir}),
        "python",
    )
    sys.exit(
        subprocess.run(
            (python_path, *sys.argv),
        ).returncode,
    )


def pip_install(python, args):
    subprocess.run((python, "-m", "pip", "install", *args), check=True)


def get_packages(profile=None):
    result = []
    collect = profile is None
    with open(REQUIREMENTS) as f:
        for line in f:
            if line.startswith("#"):
                collect = profile is None or line.lstrip("#").strip() == profile
                continue
            if collect:
                result.append(line)
    return result


@contextmanager
def stash_unstaged():
    if subprocess.check_output(("git", "ls-files", "--exclude-standard", "-om")) == b"":
        # nothing to stash
        yield
        return
    subprocess.run(
        ("git", "stash", "--keep-index", "--include-untracked", "-m", "temp"),
        check=True,
    )
    file_list = subprocess.check_output(
        ("git", "diff", "stash", "--name-only"),
        universal_newlines=True,
    ).splitlines()
    diffs = [
        subprocess.check_output(("git", "diff", "--binary", "-R", "stash", file))
        for file in file_list
    ]
    try:
        yield
    finally:
        # restore all files from stash
        for file, diff in zip(file_list, diffs):
            if subprocess.run(("git", "apply"), input=diff).returncode != 0:
                # revert changes made by script
                subprocess.run(("git", "checkout", "--", file))
                subprocess.run(("git", "apply"), input=diff, check=True)
        # pop untracked files
        if subprocess.run(("git", "stash", "pop")).returncode != 0:
            subprocess.run(("git", "stash", "drop"), check=True)


def _format_file(file):
    success = True
    if not os.path.exists(file):
        # file was removed
        return True
    with open(file) as f:
        try:
            data = f.readlines()
        except UnicodeDecodeError:
            return True
    for i, line in enumerate(data):
        if line.endswith((" \n", "\t\n")):
            success = False
            data[i] = line.rstrip(" \t\n") + "\n"
    if data and not data[-1].endswith("\n"):
        success = False
        data[-1] += "\n"
    if not success:
        with open(file, "w") as f:
            f.writelines(data)
    return success


def format_files():
    files = subprocess.check_output(
        ("git", "diff", "--staged", "--name-only")
        if "-a" not in sys.argv
        else ("git", "ls-files"),
        universal_newlines=True,
    ).splitlines()
    results = [_format_file(f) for f in files]
    return all(results)


def run_flake8():
    return subprocess.run((sys.executable, "-m", "flake8")).returncode == 0


def run_mypy():
    return subprocess.run((sys.executable, "-m", "mypy")).returncode == 0


def check_coverage():
    from runpy import run_module
    from coverage import Coverage  # type: ignore[import]

    cov = Coverage()
    cov.start()

    run_module("i18n.tests", run_name="__main__")

    cov.stop()
    return (
        cov.report() == 100.0
        # always succeed on GA
        or ON_CI
    )


def install():
    file = os.path.join(os.getcwd(), ".git", "hooks", "pre-commit")
    with open(file, "w") as f:
        print(shlex.quote(sys.executable), shlex.quote(sys.argv[0]), file=f)
    mode = os.stat(file).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(file, mode)


FUNCS = {
    "tests": (check_coverage,),
    "checks": (format_files, run_flake8, run_mypy),
}


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith(("run-", "-")):
        if args and args[0].startswith("run-"):
            _, _, profile = args[0].partition("-")
            funcs = FUNCS[profile]
            pkgs = get_packages(profile)
        else:
            funcs = sum(FUNCS.values(), start=())
            pkgs = get_packages()
        ensure_venv(pkgs)
        with stash_unstaged():
            for func in funcs:
                print("running", func.__name__)
                if not func():
                    return 1, func.__name__ + " failed"
    elif args[0] == "install":
        install()
    else:
        return 1, "Unknown command: " + args[0]
    return 0, "ok"


if __name__ == "__main__":
    code, text = main()
    print(text)
    sys.exit(code)
