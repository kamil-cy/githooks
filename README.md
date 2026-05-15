![❤️ Made by human](https://raw.githubusercontent.com/kamil-cy/badges/main/svg/made_by_human_red_heart.svg)

# GitHooks

Write pretty and concise Git hooks in Python. GitHooks lets you write an entire Git hook directly in Python, without using YAML. It’s ideal when you want full control and all your logic contained in a single file.

- [Installing](#installing)
- [Hooks](#hooks)
  - [PreCommit](#precommit)
  - [PrePush](#prepush)
- [Common config](#common-config)
  - [`add_ignored_files` for ignoring files](#add_ignored_files-for-ignoring-files)
    - [Support for Python's pathlib.Path pattern matching](#support-for-pythons-pathlibpath-pattern-matching)
  - [`check_content_for` search for lines in files that match substring](#check_content_for-search-for-lines-in-files-that-match-substring)
  - [`check_command` for checking commands execution](#check_command-for-checking-commands-execution)
    - [Check commands which `RC=0` means failure](#check-commands-which-rc0-means-failure)
  - [`outputs` for table-formatted color-aware outputs when using `check_command`](#outputs-for-table-formatted-color-aware-outputs-when-using-check_command)
  - [`results` for all or filtered results](#results-for-all-or-filtered-results)
  - [ `summary` for quick summary](#summary-for-quick-summary)
  - [`rc` for the return code of the git hook](#rc-for-the-return-code-of-the-git-hook)
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

### Old version

`GitHooks` was previously named `SimpleGitHooks`, you can install latest old version by command `pip install simplegithooks` but it's recommended to use the latest `githooks`.

## Hooks

### PreCommit

Write simple pre-commit Git hook in your `.git/hooks/pre-commit`:

```python
#!/usr/bin/env python
from githooks import PreCommit

pre_commit = PreCommit(__file__)
pre_commit.add_ignored_file("src/githooks/pre-commit.py")
pre_commit.check_content_for("FIXME", "❌", "error")
pre_commit.check_content_for("NotImplemented", "🚧", "fail")
pre_commit.check_content_for("TODO", "⚠️", "warning", prevent=False)
pre_commit.check_command("ruff check")
print(pre_commit.results())
print(pre_commit.summary())
exit(pre_commit.rc)
```

Let's say you have such file in staged changes `main_1.py` because you've forgot to finish:

```python
import math

def add(b, c):
    # TODO add typing
    return b + c

def divide(a, b):
    # FIXME secure dividing by zero
    return a / b

def sqrt():
    raise NotImplementedError
```

And when you try to commit this file using `git commit -m "message"` the output will be:

![output_main_1a.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/main_1a.png)

What happened here? Let's focus only on checks that prevents us from commit this change:

- by default all checks prevents commit, unless you explicitly pass `prevent=False`
- `check_content_for("FIXME", "❌", "error")` failed because `FIXME` was found in `main_1.py`
- `check_content_for("NotImplemented", "🚧", "fail")` failed because `NotImplemented` was found in `main_1.py`
- `check_command("ruff check")` failed because command `ruff check` returned non-zero output (because of unused import `math`)

Then if you fix issues the code now looks more on less like this:

```python
import math

def add(b, c):
    # TODO add typing
    return b + c

def divide(a, b):
    try:
        return a / b
    except Exception:
        return float("inf")

def sqrt(x):
    return math.sqrt(x)
```

The output after commit will be:

![output_main_1b.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/main_1b.png)

Now `check_content_for("TODO", "⚠️", "warning", prevent=False)` failed because `TODO` was found in `main_1.py`, yet this is not preventing us from commit changes, so commit command was succeeded but with warning `Commit allowed conditionally.`

Still we can do better 😉, so let's try harder:

```python
import math
from typing import Any

def add(b:Any, c:Any):
    return b + c

def divide(a, b):
    try:
        return a / b
    except Exception:
        return float("inf")

def sqrt(x):
    return math.sqrt(x)
```

Finally we reached our goal:

![output_main_1c.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/main_1c.png)

### PrePush

Write simple pre-push Git hook in your `.git/hooks/pre-push`:

```python
#!/usr/bin/env python
import sys

from githooks import GitHook, PrePushConfig

pre_push = GitHook(__file__, PrePushConfig())
pre_push.add_ignored_files(["pre_push_example.py", "*.svg", "README.md"])
pre_push.check_command("rm -rf build/")
pre_push.check_command("rm -rf dist/")
pre_push.check_command("pytest")
print(pre_push.results())
print(pre_push.summary())
sys.exit(pre_push.rc)
```

You'll get similar outputs like for pre-commit.

## Common config

### `add_ignored_files` for ignoring files

```python
pre_commit.add_ignored_file("src/obsolete.py")
pre_commit.add_ignored_files(["src/stub1.py", "src/stub2.py"])
```

#### Support for Python's pathlib.Path pattern matching

```python
pre_commit.add_ignored_files(["pre-commit.py", "*.svg", "README.md"])
```

### `check_content_for` search for lines in files that match substring

```python
pre_commit.check_content_for("FIXME", "❌", "error")
pre_commit.check_content_for("NotImplemented", "🚧", "fail")
pre_commit.check_content_for("TODO", "⚠️", "warning", prevent=False)
```

#### `check_command` for checking commands execution

```python
pre_commit.check_command("ruff check . --fix --diff", prevent=False)
pre_commit.check_command("ruff check . --fix --show-fixes")
pre_commit.check_command("ruff format .")
pre_commit.check_command("echo false && false", irrelevant=True)
```

#### Check commands which `RC=0` means failure

```python
pre_commit.check_command("true", rc_zero_succes=False)  # ❯ true (ERROR, RC!=0 SUCCESS) 🔒
pre_commit.check_command("false", rc_zero_succes=False) # ❯ false (OK, RC!=0 SUCCESS)
```

### `outputs` for table-formatted color-aware outputs when using `check_command`

```python
pre_commit.check_command("ruff check . --fix --diff", prevent=False)
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

### `results` for all or filtered results

All results:

```python
print(pre_commit.results())
```

Filtered results:

```python
print(pre_commit.results("error"))
print(pre_commit.results("warning"))
print(pre_commit.results("error", preventing_only=True))
print(pre_commit.results("warning", preventing_only=True))
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
  ❯ echo false && false (ERROR, irrelevant=True)
  ❯ cd . && pytest (OK)
```

### `summary` for quick summary

```python
print(pre_commit.summary())
```

Example of a summary:

```
Summary:
  (nothing prevents from proceeding)
```

### `rc` for the return code of the git hook

This will finish git hook script withe the git hook result:

```python
sys.exit(pre_commit.rc)
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

## Creating a symlink

Run `githooks pre-commit --install path/to/pre_commit.py` or `githooks pre-push --install path/to/pre_push.py` to create a symlink for you repository:

![output_create_symlink.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/create_symlink.png)

If a hook file already exists, an additional message e.g. <span style="color:yellow">WARNING: file '/home/user/project/.git/hooks/pre-commit' already exists and will be overwritten.</span> will be shown as below:

![output_create_symlink.png](https://raw.githubusercontent.com/kamil-cy/githooks/main/docs/outputs/create_symlink_force.png)

### Auto confirmation

Pass `-y` or `--yes` or `--assume-yes` to skip confirmation with typing `CREATE_SYMBOLIC_LINK`. You will still get final result and warning if file or symbolic link already exists.

### Troubleshooting

If you pass a bad hook name you'll receive a hint if there is a typo e.g. <span style="color:white;background:grey;">Unknown or unsupported hook: <span style="color:red">preccomyt</span>, did you mean: <span style="color:cyan">pre-commit</span></span>.

In case of any problem while creating a symlink you'll get <span style="color:red;background:grey;">Failure, couldn't create the symbolic link.</span> instead of success message.

## Changelog<a id="changelog"></a>

See [Changelog](CHANGELOG.md).

## License<a id="license"></a>

This repository is licensed under the [MIT License](LICENSE).
