# CHANGELOG

**v1.2.4:**

- add `-y` (`--yes` or `--assume-yes`) parameter to git hook installation to auto confirm actions (assumes you confirms all prompts and run non-interactively)
- add CHANGELOG.md

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
