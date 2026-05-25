# CHANGELOG

**v1.3.0: ⚠️ BREAKING CHANGE**

- rewrite whole codebase
- add `CommitMsg` with support for conventional commits, forbidden word filtering (with built-in set), inserting into commit message content and validating title length
- table-formatted color-aware `outputs` when using `check_command` have return code and can it's borders can be customized
- add support for forced finish with provided RC
- unify check rules and introduce params builder for checks
- introduce `report` method as a shortcut for `command_outputs`, `results`, `summary` and `ending`
- support for own check rules and customization of existing ones by overriding check params
- ... and many more

**v1.2.4:**

- add `-y` (`--yes` or `--assume-yes`) parameter to git hook installation to auto confirm actions (assumes you confirms all prompts and run non-interactively)
- add support for table-formatted color-aware `outputs` when using `check_command`
- add parameter `irrelevant` for `check_command`
- add CHANGELOG.md
- add `.vscode/launch.json`

**v1.2.3: ⚠️ BREAKING CHANGE**

- change project name from `simplegithooks` to just `githooks`, update the imports accordingly (I've contacted Alejandro Blanco with a request to transfer the `githooks` package name on PyPI, and he agreed - thanks, Alejandro)
- fix detection of not found command

**v1.2.2:**

- fix `pre-push` command

**v1.2.1:**

- add `PrePush` with `pre_push_example.py` example
- rewrite classes to generic `GitHook` with `PreCommitConfig` and `PrePushConfig` (based on `HookConfig` protocol)

**v1.1.6:**

- fix argparse color issue

**v1.1.5:**

- fix hook installation

**v1.1.4: ⚠️ BREAKING CHANGE**

- change project name to `simplegithooks`, update the imports accordingly
- introduce `githooks` CLI tool for invoking a git hook with installation support under `.git` folder
- minor fixes

**v1.1.3:**

- fix README.md links for images

**v1.1.0:**

- Terminal color support.
- Handling symbolic links when a file or a symbolic link already exists.
- Add `pre_commit.py` example
- Add README content

**v1.0.0:**

- First implementation of Git hooks with only `PreCommit` under old name.
- Handling ignored files, checking files content, checking command outputs, result and summary.
- Support for hook installation as a symbolic link when running as a script.
