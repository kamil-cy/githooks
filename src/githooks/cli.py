import argparse
import difflib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from githooks import __version__
from githooks.colors import fg_cyan, fg_red, reset
from githooks.hooks.commit_msg import CommitMsg
from githooks.hooks.pre_commit import PreCommit
from githooks.hooks.pre_push import PrePush

if TYPE_CHECKING:
    from githooks.hooks import GitHook


def main() -> None:
    hooks: dict[str, type[GitHook]] = {
        "pre-commit": PreCommit,
        "pre-push": PrePush,
        "commit-msg": CommitMsg,
    }
    description = "A simple command line interface for Git hooks"

    try:
        parser = argparse.ArgumentParser(description=description, color=True)
    except TypeError:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "hook_name",
        nargs="?",
        help="A hook name for execution or actions",
    )

    parser.add_argument(
        "-y",
        "--yes",
        "--assume-yes",
        action="store_true",
        help="Automatic confirms to prompts "
        "(assumes you confirms all prompts and run non-interactively",
    )

    parser.add_argument(
        "-i",
        "--install",
        metavar="PATH_TO_HOOK_FILE",
        action="store",
        help="Install the given hook",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    options = parser.parse_args()
    if options.version:
        sys.stdout.write(f"GitHooks {__version__}\n")
        sys.exit(0)

    hook_name: str = options.hook_name
    if not hook_name:
        parser.error("hook_name is required")

    try:
        hook_class: type[GitHook] = hooks[hook_name]
    except KeyError:
        similar = difflib.get_close_matches(hook_name, hooks.keys(), n=1)
        hint = f", did you mean: {fg_cyan}{similar[0]}{reset}" if similar else ""
        msg = f"Unknown or unsupported hook: {fg_red}{hook_name}{reset}{hint}\n"
        sys.stderr.write(msg)
        sys.exit(1)

    if options.install:
        install_path = Path(options.install)

        if not install_path.exists():
            sys.stderr.write(f"File {fg_cyan}{install_path!s}{reset} not found!")
            sys.exit(1)
        hook_class.install_git_hook(install_path.absolute(), hook_name, options.yes)
        sys.exit(0)

    hook: GitHook = hook_class()
    hook.run_default_git_hook(hook_name)
    # TODO obsłużyć pozostałe akcjie hooków
    # TODO sprawdzić czy działa CLI


if __name__ == "__main__":
    main()
