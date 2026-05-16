from githooks.hooks import GitHook, HookBaseProtocol


class PreCommit(GitHook, HookBaseProtocol):
    hook_name: str = "pre-commit"
    init_command: str = "git diff --cached --name-only"
