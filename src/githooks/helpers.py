import os
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from fcntl import ioctl
from pty import openpty
from shutil import get_terminal_size
from struct import pack
from subprocess import Popen
from termios import TIOCSWINSZ
from time import perf_counter
from typing import Any, Self


def list_get_or[T](sequence: Sequence[T], index: int, default: T) -> T:
    return sequence[index] if index < len(sequence) else default


def file_put(
    file_path: str,
    lines: list[str],
    line_end: str = "\n",
    open_fn: Callable[..., Any] = open,
) -> None:
    with open_fn(file_path, "w") as f:
        f.writelines(f"{line}{line_end}" for line in lines)


def remove_ansi(text: str) -> str:
    chars: list[str] = []
    skip = False
    osc_sequence: bool = False
    prev_char: str = ""
    for char in text:
        if char == "\x1b":
            skip = True
            prev_char = char
            continue
        if char == "8" and prev_char == "]":
            osc_sequence = not osc_sequence
        if char == "\\" and prev_char == "\x1b":
            skip = False
            continue
        if skip:
            if char == "m" and not osc_sequence:
                skip = False
            prev_char = char
            continue
        prev_char = char
        chars.append(char)
    return "".join(chars)


def run_with_pty(command: str) -> tuple[int, str]:
    cols, rows = get_terminal_size()
    master_fd, slave_fd = openpty()
    ioctl(slave_fd, TIOCSWINSZ, pack("HHHH", rows, cols - 4, 0, 0))
    proc = Popen(  # noqa: S603
        ["bash", "-c", command],  # noqa: S607
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)
    output = bytearray()
    while True:
        try:
            data = os.read(master_fd, 1024)
            if not data:
                break
            output.extend(data)
        except OSError:
            break
    rc = proc.wait()
    text = output.decode(errors="replace")
    return rc, text


def split_words(text: str, words_only: bool = False) -> list[str]:
    words: list[str] = []
    word: str = ""
    for char in text:
        if char.isalnum():
            word += char
        else:
            if word:
                words.append(word)
                word = ""
            if char.strip():
                words.append(char)
    if word.strip():
        words.append(word)
    if words_only:
        words = [w for w in words if w.isalnum()]
    return words


def wrap(text: str, length: int = 70) -> list[str]:
    # unfortunately textwrap.wrap is not working
    chunks: list[str] = []
    chars: list[str] = []
    skip = False
    i = 0
    for char in text:
        chars.append(char)
        if char == "\x1b":
            skip = True
        if skip:
            if char == "m":
                skip = False
        else:
            i += 1
        if i == length:
            chunks.append("".join(chars))
            chars = []
            i = 0
    if chars:
        chunks.append("".join(chars))
    return chunks


@dataclass
class BuildMixin:
    @classmethod
    def build(cls, *args: Any) -> Self:
        allowed = cls.__dataclass_fields__.keys()
        d = {}
        for arg in args:
            if is_dataclass(arg):
                arg = asdict(arg)  # type: ignore[arg-type]
            d.update({k: v for k, v in arg.items() if k in allowed})
        return cls(**d)


class Timer:
    def __init__(self) -> None:
        self._begin = perf_counter()

    def __enter__(self) -> Self:
        self._begin = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        self.stop()

    def stop(self) -> None:
        self._end = perf_counter()
        self.elapsed = self._end - self._begin
