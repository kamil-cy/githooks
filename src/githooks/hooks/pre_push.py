import sys

from githooks.hooks import GitHook, HookBaseProtocol


class PrePush(GitHook, HookBaseProtocol):
    hook_name: str = "pre-push"
    init_command: str = ""

    def _init_start(self) -> None:
        for line in sys.stdin:
            _, local_sha, _, remote_sha = line.strip().split()

        if remote_sha != "0" * 40:
            self._init_command = f"git diff --name-only {remote_sha}..{local_sha}"
        else:
            self._init_command = f"git diff --name-only {local_sha}"
