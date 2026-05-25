![❤️ Made by human](https://raw.githubusercontent.com/kamil-cy/badges/main/svg/made_by_human_red_heart.svg)

# GitHooks

Write pretty and concise Git hooks in Python. GitHooks lets you write an entire Git hook directly in Python, without using YAML. It’s ideal when you want full control and all your logic contained in a single file.

- [Installing](#installing)
  - [Old version](#old-version)
- [Hooks](#hooks)
  - [PreCommit](#precommit)
  - [PrePush](#prepush)
  - [CommitMsg](#commitmsg)
- [Common config](#common-config)
  - [`ignore_files` for ignoring files](#ignore_files-for-ignoring-files)
    - [Support for Python's pathlib.Path pattern matching](#support-for-pythons-pathlibpath-pattern-matching)
  - [`check_content_for` search for lines in files that match substring](#check_content_for-search-for-lines-in-files-that-match-substring)
  - [`check_command` for checking commands execution](#check_command-for-checking-commands-execution)
    - [Check commands which `RC=0` means failure](#check-commands-which-rc0-means-failure)
  - [`report` full report including `outputs`, `results`, `summary` and `ending`](#report-full-report-including-outputs-results-summary-and-ending)
    - [`outputs` for table-formatted color-aware outputs when using `check_command`](#outputs-for-table-formatted-color-aware-outputs-when-using-check_command)
    - [`results` for all or filtered results](#results-for-all-or-filtered-results)
    - [`summary` for quick summary](#summary-for-quick-summary)
    - [`ending` for the return code of the git hook](#ending-for-the-return-code-of-the-git-hook)
  - [support for other git hooks](#support-for-other-git-hooks)
    - [`check_other_hook`](#check_other_hook)
    - [`check_other_hooks`](#check_other_hooks)
- [Dedicated `commit-msg` methods](#dedicated-commit-msg-methods)
  - [`custom_check`](#custom_check)
  - [`check_title_regex_fullmatch`](#check_title_regex_fullmatch)
  - [`check_title_regex_search`](#check_title_regex_search)
  - [`check_title_regex_match`](#check_title_regex_match)
  - [`check_title_contains_words_set`](#check_title_contains_words_set)
  - [`check_content_contains_words_set`](#check_content_contains_words_set)
  - [`check_title_conventional_commit`](#check_title_conventional_commit)
  - [`check_content_forbidden_words_set`](#check_content_forbidden_words_set)
  - [`check_content_spelling`](#check_content_spelling)
  - [`check_title_length`](#check_title_length)
  - [`insert_into_content`](#insert_into_content)
- [Creating a symlink](#creating-a-symlink)
  - [Auto confirmation](#auto-confirmation)
  - [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)
- [License](#license)

## Installing

You can install via `pip`:

```sh
pip install githooks
```

No dependency required.

### Old version

`GitHooks` was previously named `SimpleGitHooks`, you can install latest old version by command `pip install simplegithooks` but it's recommended to use the latest `githooks`.

## Hooks

### PreCommit

Write a simple pre-commit Git hook file e.g.: `helpers/pre-commit` and then install it with a command `githooks pre-commit --install helpers/pre-commit.py`:

```python
#!/usr/bin/env python
from githooks import PreCommit, Priority

pre_commit = PreCommit(__file__)
pre_commit.ignore_file("helpers/pre-commit.py")
pre_commit.check_content_for("❌", "FIXME")
pre_commit.check_content_for("🚧", "NotImplemented")
pre_commit.check_content_for("⚠️", "secure", priority=Priority.MEDIUM)
pre_commit.check_command("ruff check")
pre_commit.report()
```

Let's say you have such file in staged changes `main.py` because you've forgot to finish:

```python
import math

def add(b, c):
    # TODO add typing
    return b + c

def divide(a, b):
    # secure dividing by zero
    return a / b

def sqrt():
    # FIXME
    raise NotImplementedError
```

And when you try to commit this file using `git commit -m "message"` the output will be:

![output__precommit_1a.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/precommit_1a.png)

![output__precommit_1b.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/precommit_1b.png)

What happened here? Let's focus only on checks that prevents us from commit this change (notice a locker icon):

- by default all checks prevents commit (Priority.HIGH), unless you explicitly pass level `priority=Priority.MEDIUM` or lower level
- `check_content_for("❌", "FIXME", "error")` failed because `FIXME` was found in `main.py`
- `check_content_for("🚧", "NotImplemented", "fail")` failed because `NotImplemented` was found in `main.py`
- `check_command("ruff check")` failed because command `ruff check` returned non-zero output (because of unused import `math`)

Then if you fix issues the code now looks more on less like this:

```python
import math
from typing import Any

def add(b:Any, c:Any):
    return b + c

def divide(a, b):
    # secure dividing by zero
    return a / b

def sqrt(x):
    return math.sqrt(x)
```

The output after commit will be:

![output__precommit_2.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/precommit_2.png)

Now `check_content_for("⚠️", "secure", priority=Priority.MEDIUM)` failed because phrase `secure` was found in `main.py`, yet this is not preventing us from commit changes, so commit command was succeeded but with warning `Commit allowed conditionally.`

Still we can do better 😉, so let's try harder:

```python
import math
from typing import Any

def add(b:Any, c:Any):
    return b + c

def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return float("inf")

def sqrt(x):
    return math.sqrt(x)
```

Finally we reached our goal:

![output__precommit_3.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/precommit_3.png)

### PrePush

Write simple pre-push Git hook e.g.: `.git/hooks/pre-push` and then instal it with a command `githooks pre-push --install helpers/pre-push.py`:

```python
#!/usr/bin/env python

from githooks import PrePush

pre_push = PrePush(__file__)
pre_push.ignore_files(["pre_push_example.py", "README.md"])
pre_push.check_command("pytest", rc_success_set={0, 5})
pre_push.report()
```

You'll get similar outputs like for pre-commit:

![output__prepush_1.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/prepush_1.png)

### CommitMsg

Write simple commit-msg Git hook e.g.: `.git/hooks/commit-msg` and then instal it with a command `githooks commit-msg --install helpers/commit-msg.py`:

```python
#!/usr/bin/env python
from githooks import CommitMsg

commit_msg = CommitMsg(__file__)
commit_msg.check_title_conventional_commit()
commit_msg.check_content_forbidden_words_set()
commit_msg.check_content_spelling()
commit_msg.check_title_length(60)
commit_msg.insert_into_content(0, 7, "🎯 ")
commit_msg.report()
```

You'll get similar outputs like for pre-commit, but also with it as `commit-msg` is just after `pre-commit`:

![output__commitmsg_1.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/commitmsg_1.png)

## Common config

### `ignore_files` for ignoring files

```python
pre_commit.ignore_file("src/obsolete.py")
pre_commit.ignore_files(["src/stub1.py", "src/stub2.py"])
```

#### Support for Python's pathlib.Path pattern matching

```python
pre_commit.ignore_files(["pre-commit.py", "*.svg", "README.md"])
```

### `check_content_for` search for lines in files that match substring

```python
pre_commit.check_content_for("FIXME", "❌", "error")
pre_commit.check_content_for("NotImplemented", "🚧", "fail")
pre_commit.check_content_for("TODO", "⚠️", "warning", priority=Priority.MEDIUM)
```

### `check_command` for checking commands execution

```python
pre_commit.check_command("ruff check . --fix --diff", priority=Priority.MEDIUM)
pre_commit.check_command("ruff check . --fix --show-fixes")
pre_commit.check_command("ruff format .")
pre_commit.check_command("echo false && false", priority=Priority.INFO)
```

#### Check commands which `RC=0` means failure

```python
pre_commit.check_command("true", rc_success_set={1})  # ❯ true (ERROR, RC==1 SUCCESS) 🔒
pre_commit.check_command("false", rc_success_set={1}) # ❯ false (OK, RC==1 SUCCESS)
```

### `report` full report including `outputs`, `results`, `summary` and `ending`

#### `outputs` for table-formatted color-aware outputs when using `check_command`

```python
pre_commit.check_command("ruff check . --fix --diff", priority=Priority.MEDIUM)
print(pre_commit.outputs())
```

Example of an output:

```
┌─────────────────────────────────┐
│ ruff check . --fix --show-fixes │
├─────────────────────────────────┤
│ All checks passed!              │
└─────────────────────────────────┘
```

#### `results` for all or filtered results

All results:

```python
print(pre_commit.results())
```

Filtered results:

```python
print(pre_commit.results("error"))
print(pre_commit.results("warning"))
```

Example of results:

```
Results:
  ❌ FIXME not found
  🚧 NotImplemented not found
  ⚠️ TODO not found
  ❯ ruff check . --fix --diff (OK)
  ❯ ruff check . --fix --show-fixes (OK)
  ❯ ruff format . (OK)
  ❯ mypy --explicit-package-bases --ignore-missing-imports . (OK)
  ❯ echo false && false (ERROR, priority=Priority.INFO)
  ❯ cd . && pytest (OK)
```

#### `summary` for quick summary

```python
print(pre_commit.summary())
```

Example of a summary:

```
Summary:
  (nothing to show)
```

#### `ending` for the return code of the git hook

This will finish git hook script withe the git hook result:

```python
sys.exit(pre_commit.ending)
```

Possible outputs are:

```
🟢 Commit clean.
```

```
🟡 Commit allowed (caution).
```

```
🔴 Commit aborted.
```

### support for other git hooks

GitHooks supports other hooks which can be run like a regular command, but with dedicated interface

#### `check_other_hook`

Runs other file for provided relative path, e.g.:

```python
pre_commit.check_other_hook("pre-commit.old")
```

#### `check_other_hooks`

Runs other files if they match provided rules for names, e.g.:

```python
pre_commit.check_other_hooks(prefix_in=["pre-commit"], suffix_not_in=["err", "sample"])
```

## Dedicated `commit-msg` methods

### `custom_check`

```python
commit_msg.custom_check(
    commit_msg.title == 42,
    glyph=Glyphs.question_mark_white,
    glyph_space=1,
    category="custom check for 'title == 42'",
    msg=f"custom check {'ok' if commit_msg.title == 42 else f"fail '{commit_msg.title}' != 42"}",
    priority=Priority.LOW,
)
```

### `check_title_regex_fullmatch`

```python
commit_msg.check_title_regex_fullmatch(
    r"""^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w\-]+\))?(!)?: .+$""",
    priority=Priority.HIGH,
)
```

### `check_title_regex_search`

```python
commit_msg.check_title_regex_search(r"^(feat|fix)", priority=Priority.MEDIUM)
```

### `check_title_regex_match`

```python
commit_msg.check_title_regex_match(r"[A-Za-z]+", priority=Priority.MEDIUM)
```

### `check_title_contains_words_set`

```python
commit_msg.check_title_contains_words_set({"client"})
```

### `check_content_contains_words_set`

```python
commit_msg.check_content_contains_words_set({"fix"})
```

### `check_title_conventional_commit`

```python
commit_msg.check_title_conventional_commit()
```

### `check_content_forbidden_words_set`

```python
commit_msg.check_content_forbidden_words_set({":"}, glyph=Glyphs.no_entry, priority=Priority.LOW)
```

```python
commit_msg.check_content_forbidden_words_set()
```

### `check_content_spelling`

```python
commit_msg.check_content_spelling()
```

### `check_title_length`

```python
commit_msg.check_title_length(60)
```

### `insert_into_content`

```python
commit_msg.insert_into_content(0, 7, "🎯 ")
```

## Creating a symlink

Run `githooks pre-commit --install path/to/pre_commit.py` or `githooks pre-push --install path/to/pre_push.py` to create a symlink for you repository:

![output__create_symlink.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/create_symlink.png)

If a hook file already exists, an additional message e.g. <span style="color:yellow">WARNING: file '/home/user/project/.git/hooks/pre-commit' already exists and will be overwritten.</span> will be shown as below:

![output__create_symlink.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/create_symlink_force.png)

### Auto confirmation

Pass `-y` or `--yes` or `--assume-yes` to skip confirmation with typing `CREATE_SYMBOLIC_LINK`. You will still get final result and warning if file or symbolic link already exists.

### Troubleshooting

If you pass a bad hook name you'll receive a hint if there is a typo e.g. <span style="color:white;background:grey;">Unknown or unsupported hook: <span style="color:red">preccomyt</span>, did you mean: <span style="color:cyan">pre-commit</span></span>.

In case of any problem while creating a symlink you'll get <span style="color:red;background:grey;">Failure, couldn't create the symbolic link.</span> instead of success message.

## Changelog<a id="changelog"></a>

See [Changelog](CHANGELOG.md).

## License<a id="license"></a>

This repository is licensed under the [MIT License](LICENSE).
