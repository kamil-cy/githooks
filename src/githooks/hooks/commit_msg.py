import re
import sys
from collections.abc import Callable
from contextlib import suppress
from difflib import get_close_matches
from typing import Any, ClassVar, Unpack

from githooks import Glyphs
from githooks.constants import BASE_BLOCK_SET
from githooks.exceptions import InvalidPathCommitMsgError, ParamMustBeSequenceError
from githooks.helpers import file_put, split_words
from githooks.hooks import CheckParams, GitHook, HookBaseProtocol, Timer


class CommitMsg(GitHook, HookBaseProtocol):
    hook_name: str = "commit-msg"
    init_command: str = "git diff --cached --name-only"

    conventional_commit_types: ClassVar = frozenset(
        {"chore", "docs", "feat", "fix", "refactor", "style", "test"},
    )
    conventional_commit_types_extended: ClassVar = conventional_commit_types | frozenset(
        {"build", "ci", "perf", "revert"},
    )

    def __init_end(self) -> None:
        self.message_file_path: str | None = None
        self.title: str = ""
        self.lines: list[str] = []
        self.type: str = ""
        self.scope: str | None = None
        self.breaking: bool = False
        self.subject: str | None = None
        self.body: str | None = None

        self.load_message_file()
        self.parse_title()

    def load_message_file(
        self,
        message_file_path: str | None = None,
        message: str | None = None,
        open_fn: Callable[..., Any] = open,
    ) -> None:
        if message_file_path:
            if message:
                raise InvalidPathCommitMsgError
            self.message_file_path = message_file_path
        elif message:
            self.lines = message.splitlines()
            self.title = self.lines[0]
            return
        elif sys.argv[0].startswith(".git/hooks"):
            self.message_file_path = sys.argv[1]
        else:
            self.message_file_path = ".git/COMMIT_EDITMSG"

        with open_fn(self.message_file_path) as f:
            self.lines = [line.strip() for line in f]
            self.title = self.lines[0]
        return

    def parse_title(self, title: str | None = None) -> None:
        if title is None:
            title = self.title
        else:
            self.title = title
        title_as_list = split_words(title)

        lists: dict[str, list[str]] = {"type": [], "scope": [], "subject": []}
        key = "type"
        length = len(title_as_list)
        for i, el in enumerate(title_as_list):
            if el == "!" and i < length - 1 and title_as_list[i + 1] == ":":
                self.breaking = True
            elif el in {")", ":"}:
                key = "subject"
            elif el == "(":
                key = "scope"
            else:
                lists[key].append(el)
        self.type = " ".join(lists["type"])
        self.scope = " ".join(lists["scope"])
        self.subject = " ".join(lists["subject"])

    def insert_into_content(self, row: int, col: int, text: str, line_end: str = "\n") -> None:
        lines: list[str] = []
        for i in range(max(row + 1, len(self.lines))):
            line = ""
            with suppress(IndexError):
                line = self.lines[i]
            if i == row:
                line = f"{line[:col]}{text}{line[col:]}" if col < len(line) else f"{line}{text}"
            lines.append(line)
        if self.message_file_path is not None:
            file_put(self.message_file_path, lines, line_end)

    def is_conventional_commit(self, extended: bool = True) -> tuple[bool, str, str]:
        if extended:
            conventional_commit_types = self.conventional_commit_types_extended
        else:
            conventional_commit_types = self.conventional_commit_types

        error: str = ""
        hint: str = ""
        valid_type: bool = self.type in conventional_commit_types
        type_, _, _ = self.type.partition(" ")

        if not valid_type:
            similar: list[str] = get_close_matches(
                type_,
                conventional_commit_types,
                n=1,
            )
            inline_help = f", did you mean: '{similar[0]}'?" if similar else ""
            error = f"invalid type: '{type_}'{inline_help}"
            allowed = ", ".join(conventional_commit_types)
            hint = f"commit message title must start with one of: {allowed}"
        valid_subject: bool = self.subject is not None
        return all([valid_type, valid_subject]), error, hint

    def _check_title_regex(
        self,
        pattern: str,
        regex_fn: Callable[..., Any] = re.fullmatch,
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        t = Timer()
        if success := regex_fn(pattern, self.title):
            msg = f"commit message title is valid for regex '{pattern}'"
        else:
            msg = f"commit message title does not match regex '{pattern}'"
        t.stop()
        fn_names = {re.fullmatch: "fullmatch", re.search: "search", re.match: "match"}
        check_params: CheckParams = {
            "category": f"title regex {fn_names[regex_fn]} '{pattern}'",
            "glyph": Glyphs.input_symbols,
            "msg": msg,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(bool(success), **check_params)

    def check_title_regex_fullmatch(self, pattern: str, **kwargs: Unpack[CheckParams]) -> bool:
        return self._check_title_regex(pattern, regex_fn=re.fullmatch, **kwargs)

    def check_title_regex_search(self, pattern: str, **kwargs: Unpack[CheckParams]) -> bool:
        return self._check_title_regex(pattern, regex_fn=re.search, **kwargs)

    def check_title_regex_match(self, pattern: str, **kwargs: Unpack[CheckParams]) -> bool:
        return self._check_title_regex(pattern, regex_fn=re.match, **kwargs)

    def check_title_conventional_commit(
        self,
        extended: bool = True,
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        t = Timer()
        is_conventional_commit, error, hint = self.is_conventional_commit(extended)
        hint = f"({hint})" if hint else ""
        if success := is_conventional_commit:
            msg = "commit message title is valid according to conventions"
        else:
            msg = f"{error} {hint}"
        t.stop()
        check_params: CheckParams = {
            "category": "conventional commit",
            "glyph": Glyphs.tree_leafless,
            "msg": msg,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(success, **check_params)

    def content_find_forbidden_words(
        self,
        forbidden_words: set[str],
        whole_words: bool = False,
        invert: bool = False,
    ) -> set[str]:
        words: set[str] = set()
        if whole_words:
            for line in self.lines:
                for word in split_words(line, True):
                    words.add(word.lower())
            if invert:
                return words - forbidden_words
            return words & forbidden_words
        for line in self.lines:
            for fw in forbidden_words:
                if fw in line.lower():
                    for word in line.split():
                        if fw in word.lower():
                            words.add(word)
        if invert:
            return words - forbidden_words
        return words

    def check_forbidden_words_file(
        self,
        forbidden_words_file_path: str,
        open_fn: Callable[..., Any] = open,
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        with open_fn(forbidden_words_file_path) as f:
            words = [line.strip() for line in f.readlines()]
        check_params: CheckParams = {
            "category": f"forbidden words file ({forbidden_words_file_path})",
            "glyph": Glyphs.file,
            **kwargs,
        }
        return not self.check_content_forbidden_words_set(set(words), **check_params)

    def check_content_contains_words_set(
        self,
        words_set: set[str],
        msg_ok: str = "content contains required words",
        msg_err: str = "not found required words in content: {words}",
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        if not isinstance(words_set, (list, tuple, set, frozenset)):
            raise ParamMustBeSequenceError("word_set", words_set)
        t = Timer()
        missing_required_words = []
        for word in words_set:
            if word in "\n".join(self.lines):
                continue
            missing_required_words.append(word)
        words = ", ".join(missing_required_words)
        success = not missing_required_words
        msg_err = msg_err.format(words=words)
        t.stop()
        check_params: CheckParams = {
            "category": "content required words set",
            "glyph": Glyphs.input_letters,
            "glyph_space": 1,
            "msg": msg_ok if success else msg_err,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(success, **check_params)

    def check_title_contains_words_set(
        self,
        words_set: set[str],
        msg_ok: str = "title contains required words",
        msg_err: str = "not found required words in title: {words}",
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        if not isinstance(words_set, (list, tuple, set, frozenset)):
            raise ParamMustBeSequenceError("word_set", words_set)
        t = Timer()
        missing_required_words = []
        for word in words_set:
            if word in self.title:
                continue
            missing_required_words.append(word)
        words = ", ".join(missing_required_words)
        success = not missing_required_words
        msg_err = msg_err.format(words=words)
        t.stop()
        check_params: CheckParams = {
            "category": "title required words set",
            "glyph": Glyphs.input_letters,
            "glyph_space": 1,
            "msg": msg_ok if success else msg_err,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(success, **check_params)

    def check_content_forbidden_words_set(
        self,
        forbidden_words_set: set[str] | None = None,
        msg_ok: str = "no forbidden words found",
        msg_err: str = "found forbidden words: {words}",
        whole_words: bool = False,
        invert: bool = False,
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        category = "forbidden words set"
        if forbidden_words_set is None:
            forbidden_words_set = BASE_BLOCK_SET
            category += " using default BASE_BLOCK_SET"

        t = Timer()
        forbidden_words = self.content_find_forbidden_words(
            forbidden_words_set,
            whole_words,
            invert,
        )
        t.stop()
        words = ", ".join(forbidden_words)
        success = not forbidden_words
        msg_err = msg_err.format(words=words)
        check_params: CheckParams = {
            "category": category,
            "glyph": Glyphs.covering_mouth,
            "glyph_space": 1,
            "msg": msg_ok if success else msg_err,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(success, **check_params)

    def check_content_spelling(  # type: ignore[misc]
        self,
        dictionary_file_path: str = "/usr/share/dict/american-english",
        glyph: str = Glyphs.book_open,
        open_fn: Callable[..., Any] = open,
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        with open_fn(dictionary_file_path) as f:
            words = [line.strip() for line in f.readlines()]
        check_params: CheckParams = {
            "category": f"spellcheck ({dictionary_file_path})",
            "glyph": glyph,
            **kwargs,  # type: ignore[typeddict-item]
        }
        return self.check_content_forbidden_words_set(
            set(words),
            whole_words=True,
            invert=True,
            msg_ok="spellcheck ok",
            msg_err="spellcheck unknown words: {words}",
            **check_params,
        )

    def check_title_length(
        self,
        size: int,
        **kwargs: Unpack[CheckParams],
    ) -> bool:
        t = Timer()
        len_title = len(self.title)
        t.stop()
        if success := len_title <= size:
            msg = f"commit title has valid length ({len_title} <= {size})"
        else:
            msg = f"commit title is too long ({len_title} >= {size})"
        check_params: CheckParams = {
            "category": "valid commit message title length",
            "glyph": Glyphs.label,
            "msg": msg,
            "duration": t.elapsed,
            **kwargs,
        }
        return self.validate_check(success, **check_params)
