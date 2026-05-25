#!/usr/bin/env python

from githooks import PrePush

pre_push = PrePush(__file__)
pre_push.ignore_files(["pre_*_example.py", "*.svg", "README.md"])
pre_push.check_content_for("FIXME", "❌", "error")
pre_push.check_content_for("NotImplemented", "🚧", "fail")
pre_push.check_content_for("TODO", "⚠️", "warning", prevent=False)
pre_push.check_command("rm -rf build/")
pre_push.check_command("rm -rf dist/")
pre_push.check_command("pytest")
pre_push.report()
