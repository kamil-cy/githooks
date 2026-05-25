import sys
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from pathlib import Path
from shutil import get_terminal_size
from subprocess import check_output, run
from typing import Any, Protocol, TypedDict, Unpack

from githooks.colors import (
    bg_green,
    bg_red,
    bg_yellow,
    fg_cyan,
    fg_green,
    fg_magenta,
    fg_red,
    fg_white,
    fg_yellow,
    is_cli,
    reset,
)
from githooks.constants import Glyphs
from githooks.exceptions import (
    CannotDetectOtherHooksError,
    InvalidGitPathError,
    NoOtherHooksMatchedError,
    ParamMustBeSequenceError,
)
from githooks.helpers import BuildMixin, Timer, remove_ansi, run_with_pty, wrap


class Priority(IntEnum):
    CRITICAL = 50
    HIGH = 40
    MEDIUM = 30
    LOW = 20
    INFO = 10
    NOTSET = 0


class HookBaseProtocol(Protocol):
    hook_name: str
    init_command: str

    locker: str = Glyphs.locker
    aborted_glyph: str = Glyphs.circle_red
    caution_glyph: str = Glyphs.circle_yellow
    clean_glyph: str = Glyphs.circle_green
    aborted_msg: str = "aborted"
    caution_msg: str = "allowed (caution)"
    clean_msg: str = "clean"


class CheckParams(TypedDict, total=False):
    category: str
    glyph_space: int
    glyph: str
    priority: int | Priority
    lines: list[str]
    msg: str
    output_lines: list[str]
    rc_success_set: set[int] | None
    rc: int | None
    duration: float | None


@dataclass
class CheckResult:
    success: bool
    color: str
    locker: bool
    glyph: str
    glyph_space: int
    priority: int | Priority
    category: str
    msg: str
    lines: list[str]
    output_lines: list[str]
    count: int = 0
    rc: int | None = None
    rc_success_set: set[int] | None = None
    duration: float | None = None


@dataclass
class GitHookState:
    priority: int | Priority = Priority.NOTSET
    rc: int | None = None
    duration: float = 0.0


class BaseParams(TypedDict, total=False):
    colors: bool
    print_fn: Callable[..., Any]


class CoreParams(BaseParams, total=False):
    priority: int | Priority
    include_successful: bool


class ResultParams(CoreParams, total=False):
    glyphs: bool
    indent: int
    duration: bool
    total: bool
    br_after_section: int
    ordered_list: bool | None


class ReportParams(ResultParams, total=False):
    outputs: bool
    results: bool
    summary: bool
    ending: bool


@dataclass
class ResultParamsDefaults(BuildMixin):
    colors: bool = True
    glyphs: bool = True
    indent: int = 2
    duration: bool = True
    total: bool = True
    priority: int | Priority = Priority.NOTSET
    include_successful: bool = True
    br_after_section: int = 1
    ordered_list: bool | None = None
    print_fn: Callable[..., Any] = print


@dataclass
class ReportParamsDefaults(ResultParamsDefaults):
    outputs: bool = True
    results: bool = True
    summary: bool = True
    ending: bool = True


class GitHookParams(ReportParams, total=False):
    ignore_files: list[Path | str] | None


class Git:
    def __init__(self) -> None:
        self.set_hook_paths()

    def set_hook_paths(self) -> None:
        cmd = "git rev-parse --git-path hooks"  # relative path to git hooks
        try:
            hook_path_relative = check_output(cmd, shell=True).decode().strip()  # noqa: S602
        except Exception as e:
            raise InvalidGitPathError from e
        self.hook_path = Path().cwd() / hook_path_relative
        self.hook_path_relative = Path(hook_path_relative)


class GitHook(HookBaseProtocol):
    callbacks: dict[str, Callable[[], Any]]
    git = Git()

    def __init__(
        self,
        hook_file_path: str | None = None,
        **git_hook_params: Unpack[GitHookParams],
    ) -> None:
        self._init_start()

        @dataclass
        class Defaults:
            outputs: bool = True
            results: bool = True
            summary: bool = True
            ending: bool = True

            colors: bool = True
            glyphs: bool = True
            indent: int = 2
            total: bool = True
            duration: bool = True
            include_successful: bool = True
            ignore_files: list[Path | str] | None = None
            print_fn: Callable[..., Any] = print

            priority: int | Priority = Priority.NOTSET
            ordered_list: bool | None = True
            br_after_section: int = 0

        self.params = Defaults(**git_hook_params)

        self.hook_file_path = Path(hook_file_path) if hook_file_path else None
        self._ignored_files: list[Path | str] = self.params.ignore_files or []
        self.files_from_git = self.get_files_from_command()
        self.files: dict[str, list[str]] = self.get_files_with_lines()

        self.state = GitHookState()
        self.result_list: list[CheckResult] = []

        self.init_event(hook_file_path)
        self._init_end()

    def _init_start(self) -> None: ...
    def _init_end(self) -> None: ...

    @classmethod
    def run_default_git_hook(cls, hook_name: str) -> None:
        hook_path_absolute = GitHook.git.hook_path / hook_name
        if not hook_path_absolute.exists():
            msg = (
                f"{fg_yellow}Hook '{fg_magenta}{hook_name}{fg_yellow}' not found in"
                " {fg_magenta}'.git/hooks'{fg_yellow} directory!{reset}"
            )
            sys.stdout.write(f"{msg}\n")
            sys.exit(1)
        run(hook_path_absolute, check=False)  # noqa: S603

    @classmethod
    def install_git_hook(
        cls,
        path_from: Path,
        hook_name: str,
        auto_confirm: bool = False,
    ) -> None:
        hook_path_absolute = GitHook.git.hook_path / hook_name
        cls.create_symbolic_link(path_from, hook_path_absolute, auto_confirm)

    @classmethod
    def create_symbolic_link_action(
        cls,
        create_symbolic_link_cmd: str,
        path_from: Path,
    ) -> None:
        try:
            check_output(create_symbolic_link_cmd, shell=True).decode().strip()  # noqa: S602
            path_from.chmod(path_from.stat().st_mode | 64)
        except:  # noqa: E722
            msg = f"{fg_red}Failure, couldn't create the symbolic link.{reset}\n"
            sys.stderr.write(msg)
        else:
            msg = f"{fg_green}Success, the symbolic link was created.{reset}\n"
            sys.stderr.write(msg)

    @classmethod
    def create_symbolic_link(
        cls,
        path_from: Path,
        path_to: Path,
        auto_confirm: bool = False,
    ) -> None:
        overwrite = bool(path_to.exists() or path_to.is_symlink())
        new_name = str(path_to) + f".{datetime.now(UTC):%Y%m%d_%H%M%S}.old"
        create_symbolic_link_cmd = f"ln -s {path_from} {path_to}"
        warning = (
            f"WARNING: file '{path_to}' already exists and will be overwritten.\n"
            f"Current file will be renamed to {new_name}\n"
        )
        sys.stderr.write(f"{fg_yellow}{warning if overwrite else ''}{reset}")

        if not auto_confirm:
            msg = (
                "To use this Git hook you must either create a symbolic link for"
                " this file or copy it's content to the Git hook file.\n"
                "Do you want to execute the following command to create the symbolic link?\n"
                f"  {fg_magenta}{create_symbolic_link_cmd}{reset}\n"
                f"Please type '{fg_cyan}CREATE_SYMBOLIC_LINK{reset}' "
                "to execute this command (mind underscores): "
            )
            sys.stderr.write(msg)
            try:
                ans = input()
            except KeyboardInterrupt:
                sys.stderr.write(f"{fg_yellow} Detected ^C, exiting...{reset}\n")
                return
            if ans.strip() != "CREATE_SYMBOLIC_LINK":
                msg = f"You've not provided '{fg_cyan}CREATE_SYMBOLIC_LINK{reset}', exiting...\n"
                sys.stderr.write(msg)
                return

        if overwrite:
            path_to.rename(new_name)
        cls.create_symbolic_link_action(create_symbolic_link_cmd, path_from)

    TABLE = """
    012345678901234
    ┏━━━━━━┳━━━━━━┓
    ┃ cmd  ┃ RC=0 ┃
    ┡━━━━━━┻━━━━━━┩
    │ output      │
    └─────────────┘
    """  # you can use own border, but it must have the same dimensions

    def report(
        self,
        table: str = TABLE,
        for_category: str | None = None,
        force_return_code: int | None = None,
        **result_params: Unpack[ReportParams],
    ) -> None:
        params = ReportParamsDefaults.build(self.params, result_params)
        if params.outputs:
            self.command_outputs(
                table=table,
                priority=params.priority,
                include_successful=params.include_successful,
                colors=params.colors,
                print_fn=params.print_fn,
            )
        if params.results:
            self.results(
                for_category=for_category,
                indent=params.indent,
                priority=params.priority,
                include_successful=params.include_successful,
                colors=params.colors,
                glyphs=params.glyphs,
                total=params.total,
                ordered_list=params.ordered_list,
                br_after_section=params.br_after_section,
                print_fn=params.print_fn,
            )
        if params.summary:
            self.summary(
                for_category=for_category,
                indent=params.indent,
                priority=params.priority,
                include_successful=params.include_successful,
                colors=params.colors,
                glyphs=params.glyphs,
                total=params.total,
                ordered_list=params.ordered_list,
                br_after_section=params.br_after_section,
                print_fn=params.print_fn,
            )
        if params.ending:
            rc = self.ending()
        else:
            rc, _ = self.final_result()

        if force_return_code is not None:
            if params.colors:
                s = "{CR}Hook {N} exited with {CM}RC={R}{CR}, but forced {CM}RC={F}{C0}"
            else:
                s = "Hook {N} exited with RC={R}, but forced RC={F}"
            params.print_fn(
                s.format(
                    CR=fg_red + bg_yellow,
                    N=self.hook_name,
                    CM=fg_cyan,
                    R=rc,
                    F=force_return_code,
                    C0=reset,
                ),
            )
            sys.exit(force_return_code)
        sys.exit(rc)

    def ending(
        self,
        **base_params: Unpack[BaseParams],
    ) -> int:
        params = ResultParamsDefaults.build(self.params, base_params)
        rc, result = self.final_result(**base_params)
        params.print_fn(result)
        return rc

    def init_event(self, hook_file_path: str | None) -> None:
        if not hook_file_path:
            return
        if not hasattr(self, "callbacks"):
            return
        as_hook = self.callbacks.get("as_git_hook", lambda: None)
        as_script = self.callbacks.get("as_script", lambda: None)
        if ".git/hooks/" in hook_file_path:
            as_hook()
        else:
            as_script()

    def get_files_with_lines(
        self,
        files: list[str] | None = None,
    ) -> dict[str, list[str]]:
        if files is None:
            files = self.files_from_git
        files_with_lines: dict[str, list[str]] = {}
        for filename in files:
            with suppress(Exception), Path(filename).open() as f:
                files_with_lines[filename] = f.readlines()
        return files_with_lines

    def get_files_from_command(self) -> list[str]:
        return check_output(self.init_command, shell=True).decode().split()  # noqa: S602

    def ignore_file(self, path: Path | str | None = None) -> None:
        if path is None:
            return
        self._ignored_files.append(path)

    def ignore_files(self, paths: list[Path | str] | None = None) -> None:
        if paths is None:
            return
        self._ignored_files.extend(paths)

    def custom_check(
        self,
        condition: bool,
        **kwargs: Unpack[CheckParams],
    ) -> int:
        t = Timer()
        # ...
        t.stop()
        check_params: CheckParams = {
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(condition, **check_params)

    def check_example__positive_number(
        self,
        value: int,
        **kwargs: Unpack[CheckParams],
    ) -> int:
        t = Timer()
        lines: list[str] = []
        msg = f"value {value} > 0" if value > 0 else f"value {value} <= 0"
        t.stop()
        check_params: CheckParams = {
            "category": "positive number check",
            "glyph": Glyphs.new,
            "msg": msg,
            "lines": lines,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(value > 0, **check_params)

    def check_content_for(  # type: ignore[misc]
        self,
        glyph: str,
        substring: str,
        label: str | None = None,
        **kwargs: Unpack[CheckParams],
    ) -> int:
        if label is None:
            label = substring
        success: bool = True
        lines: list[str] = []
        msg = f"'{label}' not found"
        t = Timer()
        for filename, file_lines in self.files.items():
            if filename in self._ignored_files or any(
                Path(filename).match(str(p)) for p in self._ignored_files
            ):
                continue
            for n, line in enumerate(file_lines, start=1):
                if substring not in line:
                    continue
                msg = f"'{label}' found"
                lines.append(f"{filename}:{n}")
                success = False
        t.stop()
        check_params: CheckParams = {
            "category": label,
            "glyph": glyph,
            "glyph_space": 2,
            "lines": lines,
            "msg": msg,
            "duration": t.elapsed,
            **kwargs,  # type: ignore[typeddict-item]
        }
        return self.validate_check(success, **check_params)

    def check_command(  # type: ignore[misc]
        self,
        command: str,
        rc_success_set: set[int] | None = None,
        **check_command_params: Unpack[CheckParams],
    ) -> tuple[int, str]:
        if rc_success_set is None:
            rc_success_set = {0}
        elif not isinstance(rc_success_set, (list, tuple, set, frozenset)):
            raise ParamMustBeSequenceError("rc_success_set", rc_success_set)

        params = ResultParamsDefaults.build(self.params, check_command_params)
        t = Timer()
        buf = command
        rc, output_lines = run_with_pty(command)
        priority = check_command_params.get("priority", Priority.HIGH)

        if rc == 127 and 127 not in rc_success_set:  # noqa: PLR2004
            buf = f"{fg_white}{bg_red}{buf} (command not found!){reset}"
            success = False
        else:
            success = rc in rc_success_set
            if success:
                RC = "OK"
                color = fg_cyan if priority <= Priority.INFO else fg_green
            else:
                RC = "ERROR"
                color = fg_cyan if priority <= Priority.INFO else fg_yellow
                if priority >= Priority.HIGH:
                    color = fg_red
            color = color if params.colors else ""
            RCSS = ", ".join(str(i) for i in rc_success_set)
            NZ = f", rc_success_set={RCSS}" if rc_success_set else ""
            DBG = ", priority=INFO" if priority <= Priority.INFO else ""
            buf = f"{color}{buf} ({RC}{NZ}{DBG}){reset}"
        t.stop()
        check_params: CheckParams = {
            "category": command,
            "glyph": Glyphs.command,
            "glyph_space": 1,
            "msg": buf,
            "priority": priority,
            "output_lines": output_lines.splitlines(),
            "rc": rc,
            "rc_success_set": rc_success_set,
            "duration": t.elapsed,
            **check_command_params,  # type: ignore[typeddict-item]
        }
        return self.validate_check(success, **check_params), output_lines

    def _process_results(
        self,
        summary: bool,
        buf: str,
        for_category: str | None = None,
        **result_params: Unpack[ResultParams],
    ) -> str:
        params = ResultParamsDefaults.build(self.params, result_params)

        if params.duration and summary:
            buf += f" [{self.state.duration * 1000:.4f}ms]"
        buf += ":\n"

        _indent = " " * params.indent
        c0 = f"{reset}" if params.colors else ""
        nothing_prevents = True

        count = 0
        for r_obj in self.result_list:
            if for_category and r_obj.category != for_category:
                continue
            if not self._include_result_obj(params.priority, params.include_successful, r_obj):
                continue

            if r_obj.priority >= Priority.HIGH and not r_obj.success:
                nothing_prevents = False
            color = r_obj.color if params.colors else ""

            glyph = f"{r_obj.glyph}{' ' * r_obj.glyph_space}" if params.glyphs else ""
            glyph = glyph if params.glyphs else ""
            _total = len(r_obj.lines)
            RCSS = ", ".join(str(i) for i in r_obj.rc_success_set) if r_obj.rc_success_set else ""
            SIGN = self._get_sign(r_obj)
            CAT = r_obj.category
            TT = f"{c0} (total: {_total})" if params.total and _total else ""
            RC = f"{c0} (rc_success_set={RCSS}) {color}" if r_obj.rc_success_set else ""
            LR = " " + self.locker if r_obj.locker else ""
            duration = params.duration and r_obj.duration is not None and r_obj.duration
            if duration >= self.state.duration / 10:
                CD = fg_red
            else:
                CD = c0 if duration < self.state.duration / 100 else fg_yellow
            CD = CD if params.colors else ""
            T = f"{c0} [{CD}{duration * 1000:.4f}ms{CD}{c0}]" if duration else ""
            if summary:
                buf += f"{_indent}{SIGN}{glyph}{color}{CAT}{RC}{TT}{T}{LR}{c0}\n"
            else:
                buf += f"{_indent}{glyph}{color}{r_obj.msg}{TT}{LR}{c0}\n"
                for i, line in enumerate(r_obj.lines, start=1):
                    ln = f"{i:>{len(str(_total))}}. " if params.ordered_list else "- "
                    buf += f"{_indent * 2}{ln}{color}{line}{c0}\n"
            buf += "\n" * params.br_after_section if params.br_after_section else ""
            count += 1
        if nothing_prevents and not count:
            buf = f"{buf}{c0}{_indent}(nothing to show)\n"
        params.print_fn(buf)
        return buf

    def summary(
        self,
        for_category: str | None = None,
        **result_params: Unpack[ResultParams],
    ) -> str:
        return self._process_results(
            summary=True,
            buf="Summary",
            for_category=for_category,
            **result_params,
        )

    def results(
        self,
        for_category: str | None = None,
        **result_params: Unpack[ResultParams],
    ) -> str:
        return self._process_results(
            summary=False,
            buf="Results",
            for_category=for_category,
            **result_params,
        )

    def command_outputs(
        self,
        table: str = TABLE,
        **output_params: Unpack[CoreParams],
    ) -> str:
        params = ResultParamsDefaults.build(self.params, output_params)
        array = [line.strip() for line in table.splitlines()[2:-1]]
        b = {
            "┏": array[0][0],
            "━": array[0][1],
            "┳": array[0][7],
            "┓": array[0][14],
            "┃": array[1][0],
            "┡": array[2][0],
            "┻": array[2][7],
            "┩": array[2][14],
            "│": array[3][0],
            "└": array[4][0],
            "─": array[4][1],
            "┘": array[4][14],
        }
        result: str = ""
        for r_obj in self.result_list:
            if r_obj.rc is None:
                continue
            if not self._include_result_obj(params.priority, params.include_successful, r_obj):
                continue

            NO = "--- no output ---"
            RCSS = ", ".join(str(i) for i in r_obj.rc_success_set) if r_obj.rc_success_set else ""
            RC_EX1 = f" rc_success_set={RCSS}" if r_obj.rc_success_set else ""
            RC_EX2 = " irrelevant" if r_obj.priority <= Priority.LOW else ""
            RC = f"RC={r_obj.rc}{RC_EX1}{RC_EX2}"
            color = r_obj.color if params.colors else ""
            cols = get_terminal_size().columns
            lc = len(r_obj.category)
            lr = len(RC)
            len_longest_line: int = lc + lr + 3
            lines: list[str] = []
            for line in r_obj.output_lines:
                len_longest_line = max(len_longest_line, len(remove_ansi(line)))
                lines.extend(wrap(line, cols - 4))
            if not r_obj.output_lines:
                len_longest_line = max(len(NO), len_longest_line)
            lll = min(len_longest_line, cols - 4)
            command_lines = wrap(r_obj.category, lll - lr - 3)
            result += f"{b['┏']}{b['━'] * (lr + 2)}{b['┳']}{b['━'] * (lll - lr - 1)}{b['┓']}\n"
            rc_included = False
            for cmd in command_lines:
                fill = " " * (lll - lr - 3 - len(remove_ansi(cmd)))
                if rc_included:
                    _rc = " " * lr
                else:
                    _rc = f"{RC:{lr}}"
                    rc_included = True
                result += f"{b['┃']} {_rc} {b['┃']}{color} {cmd}{fill} {reset}{b['┃']}\n"
            result += f"{b['┡']}{b['━'] * (lr + 2)}{b['┻']}{b['━'] * (lll - lr - 1)}{b['┩']}\n"

            if lines == []:
                result = f"{result}{b['│']} {NO:^{lll}} {b['│']}\n"
            for line in lines:
                fill = " " * (lll - len(remove_ansi(line)))
                if is_cli() and params.colors:
                    result = f"{result}{b['│']} {line}{fill} {b['│']}\n"
                else:
                    result = f"{result}{b['│']} {remove_ansi(line)}{fill} {b['│']}\n"
            result = f"{result}{b['└']}{b['─'] * (lll + 2)}{b['┘']}\n"
            result = f"{result}{reset}"
        params.print_fn(result)
        return result

    def _get_sign(self, result_obj: CheckResult, spaces: int = 2) -> str:
        if result_obj.success:
            sign = "✔"
        elif result_obj.priority <= Priority.INFO:
            sign = "･"
        elif result_obj.priority <= Priority.LOW:
            sign = "△"
        elif result_obj.priority <= Priority.MEDIUM:
            sign = "⚠"
        else:
            sign = "✘"
        return sign + " " * spaces

    def _include_result_obj(
        self,
        priority: int | Priority,
        include_successful: bool,
        result_obj: CheckResult,
    ) -> bool:
        if include_successful and result_obj.success:
            return True
        return result_obj.priority >= priority and not result_obj.success

    def final_result(self, **base_params: Unpack[BaseParams]) -> tuple[int, str]:
        params = ResultParamsDefaults.build(self.params, base_params)
        rc = 0
        if self.state.priority >= Priority.HIGH:
            color = bg_red
            glyph, msg = self.aborted_glyph, self.aborted_msg
            if hasattr(self, "callbacks"):
                self.callbacks.get("aborted", lambda: None)()
            rc = 1
        elif self.state.priority >= Priority.MEDIUM:
            color = bg_yellow
            glyph, msg = self.caution_glyph, self.caution_msg
            if hasattr(self, "callbacks"):
                self.callbacks.get("caution", lambda: None)()
        else:
            color = bg_green
            glyph, msg = self.clean_glyph, self.clean_msg
            if hasattr(self, "callbacks"):
                self.callbacks.get("clean", lambda: None)()
        color = color if params.colors else ""
        result = f"{reset} {glyph} {color}{self.hook_name} {msg}{reset}\n"
        return rc, result

    def validate_check(
        self,
        success: bool,
        **check_params: Unpack[CheckParams],
    ) -> bool:
        @dataclass
        class Defaults:
            glyph: str = Glyphs.check_mark
            glyph_space: int = 2
            priority: int | Priority = Priority.HIGH
            msg: str = "(no message provided)"
            category: str = "(no category provided)"
            lines: list[str] = field(default_factory=list)
            output_lines: list[str] = field(default_factory=list)
            rc: int | None = None
            rc_success_set: set[int] | None = None
            duration: float | None = None

        params = Defaults(**check_params)
        locker = False
        if params.priority <= Priority.INFO:
            color = fg_cyan
        elif success:
            color = fg_green
        elif params.priority >= Priority.HIGH:
            self.state.priority = max(self.state.priority, params.priority)
            color = fg_red
            locker = True
        else:
            self.state.priority = max(self.state.priority, Priority.MEDIUM)
            color = fg_yellow

        self.result_list.append(
            CheckResult(
                category=params.category,
                color=color,
                glyph_space=params.glyph_space,
                glyph=params.glyph,
                priority=params.priority,
                lines=params.lines,
                locker=locker,
                msg=params.msg,
                output_lines=params.output_lines,
                rc_success_set=params.rc_success_set,
                rc=params.rc,
                success=success,
                duration=params.duration,
            ),
        )
        if params.duration:
            self.state.duration += params.duration
        return success

    def check_other_hook(  # type: ignore[misc]
        self,
        path_to_file: str,
        name: str | None = None,
        rc_success_set: set[int] | None = None,
        **kwargs: Unpack[CheckParams],  # type: ignore[typeddict-item]
    ) -> tuple[int, str]:
        if rc_success_set is None:
            rc_success_set = {0}
        check_params: CheckParams = {
            "category": name or path_to_file,
            "glyph": Glyphs.gear,
            "glyph_space": 2,
            **kwargs,  # type: ignore[typeddict-item]
        }
        return self.check_command(  # type: ignore[misc]
            str(self.git.hook_path / path_to_file),
            rc_success_set,
            **check_params,  # type: ignore[arg-type]
        )

    def check_other_hooks(  # type: ignore[misc]
        self,
        name: str | None = None,
        prefix_in: Sequence | None = None,
        suffix_not_in: Sequence | None = None,
        suffix_in: Sequence | None = None,
        prefix_not_in: Sequence | None = None,
        **kwargs: Unpack[CheckParams],  # type: ignore[typeddict-item]
    ) -> list[tuple[int, str]]:
        for param_name, value in {
            "prefix_in": prefix_in,
            "suffix_not_in": suffix_not_in,
            "suffix_in": suffix_in,
            "prefix_not_in": prefix_not_in,
        }.items():
            if not isinstance(value, (list, tuple, set, frozenset)):
                raise ParamMustBeSequenceError(param_name, value)

        if not self.hook_file_path:
            raise CannotDetectOtherHooksError

        files: list[str] = []
        prefix = f"{self.git.hook_path}/"
        for file in self.git.hook_path.glob("*"):
            if file == self.hook_file_path:
                continue
            files.append(str(file.relative_to(prefix)))

        rcs: list[int] = []
        outputs: list[str] = []
        for file in files:  # type: ignore[assignment]
            prefix_in_condition = file.startswith(tuple(p for p in prefix_in or []))  # type: ignore[attr-defined]
            suffix_not_in_condition = file.endswith(tuple(s for s in suffix_not_in or []))  # type: ignore[attr-defined]
            suffix_in_condition = file.endswith(tuple(s for s in suffix_in or []))  # type: ignore[attr-defined]
            prefix_not_in_condition = file.startswith(tuple(p for p in prefix_not_in or []))  # type: ignore[attr-defined]
            if prefix_in and prefix_in_condition:
                if suffix_not_in_condition:
                    continue
            elif suffix_in and suffix_in_condition:
                if prefix_not_in_condition:
                    continue
            else:
                continue

            check_params: CheckParams = {**kwargs}
            rc, output = self.check_other_hook(
                file,  # type: ignore[arg-type]
                name=name,
                **check_params,  # type: ignore[arg-type]
            )
            rcs.append(rc)
            outputs.append(output)

        if not rcs:
            raise NoOtherHooksMatchedError
        return list(zip(rcs, outputs, strict=True))
