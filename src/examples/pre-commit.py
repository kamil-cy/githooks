#!/usr/bin/env python
from githooks import Glyphs, PreCommit, Priority

pre_commit = PreCommit(__file__)
pre_commit.check_example__positive_number(42, priority=Priority.HIGH)
# pre_commit.check_other_hooks(prefix_in=["pre-commit"], suffix_not_in=["err", "sample"])
# pre_commit.check_other_hook("pre-commit.other.ok")
pre_commit.ignore_files(["examples/*", "*.svg", "README.md"])
pre_commit.check_content_for(Glyphs.firecracker, "FIXME", glyph_space=1)
pre_commit.check_content_for(Glyphs.construction, "NotImplemented", glyph_space=1)
pre_commit.check_content_for(Glyphs.warning, "TODO", priority=Priority.MEDIUM)
pre_commit.check_content_for(
    Glyphs.printer,
    "print(",
    "print(...)",
    priority=Priority.LOW,
)
pre_commit.check_command("cd . && pytest", glyph=Glyphs.test_tube)
pre_commit.check_command("ruff check . --fix --diff", priority=Priority.MEDIUM)
pre_commit.check_command("ruff check . --fix --show-fixes")
pre_commit.check_command("ruff format .")
# pre_commit.check_command("mypy --explicit-package-bases --ignore-missing-imports .")
pre_commit.check_command("mypy .")
pre_commit.check_command("echo false - no prevent && false", priority=Priority.MEDIUM)
pre_commit.check_command("echo false - irrelevant && false", priority=Priority.INFO)
pre_commit.check_command("echo sleep 0.1 && sleep 0.1 && false", priority=Priority.LOW)
pre_commit.check_command("true; " * 100, rc_success_set={0})
pre_commit.check_command("false", rc_success_set={1})
# pre_commit.report(force_return_code=1)
pre_commit.report(
    # outputs=True,
    # indent=8,
    # priority=Priority.HIGH,
    # priority=Priority.MEDIUM,
    include_successful=True,
)

# pre_commit.command_outputs(report_warnings=False)
# pre_commit.command_outputs()
# pre_commit.results()
# pre_commit.summary()
# pre_commit.ending()

# pre_commit.ignore_file("src/githooks/pre_commit_example.py")

# pre_commit.check_command("uv add --group dev ruff mypy bandit semgrep")
# pre_commit.check_command("bandit -r . --severity-level all --confidence-level all -f txt -o bandit-report.txt")
# pre_commit.check_command('semgrep scan --config auto --config "p/python" --config "p/fastapi" --error')

# pre_commit.results("error")
# pre_commit.results("warning")
# pre_commit.results(priority=Priority.HIGH)
