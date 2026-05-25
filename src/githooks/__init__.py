from importlib.metadata import PackageNotFoundError, version

from .colors import (
    bg_black,
    bg_blue,
    bg_cyan,
    bg_green,
    bg_light_black,
    bg_light_blue,
    bg_light_cyan,
    bg_light_green,
    bg_light_magenta,
    bg_light_red,
    bg_light_white,
    bg_light_yellow,
    bg_magenta,
    bg_red,
    bg_reset,
    bg_white,
    bg_yellow,
    blink,
    fg_black,
    fg_blue,
    fg_cyan,
    fg_green,
    fg_light_black,
    fg_light_blue,
    fg_light_cyan,
    fg_light_green,
    fg_light_magenta,
    fg_light_red,
    fg_light_white,
    fg_light_yellow,
    fg_magenta,
    fg_red,
    fg_reset,
    fg_white,
    fg_yellow,
    reset,
)
from .constants import BASE_BLOCK_SET, Glyphs
from .hooks import CheckParams, GitHook, HookBaseProtocol, Priority
from .hooks.commit_msg import CommitMsg
from .hooks.pre_commit import PreCommit
from .hooks.pre_push import PrePush

__title__ = "githooks"

try:
    __version__ = version(__title__)
except PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Kamil Cyganowski"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Kamil Cyganowski"
__all__ = [
    "BASE_BLOCK_SET",
    "CheckParams",
    "CommitMsg",
    "GitHook",
    "Glyphs",
    "HookBaseProtocol",
    "PreCommit",
    "PrePush",
    "Priority",
    "bg_black",
    "bg_blue",
    "bg_cyan",
    "bg_green",
    "bg_light_black",
    "bg_light_blue",
    "bg_light_cyan",
    "bg_light_green",
    "bg_light_magenta",
    "bg_light_red",
    "bg_light_white",
    "bg_light_yellow",
    "bg_magenta",
    "bg_red",
    "bg_reset",
    "bg_white",
    "bg_yellow",
    "blink",
    "fg_black",
    "fg_blue",
    "fg_cyan",
    "fg_green",
    "fg_light_black",
    "fg_light_blue",
    "fg_light_cyan",
    "fg_light_green",
    "fg_light_magenta",
    "fg_light_red",
    "fg_light_white",
    "fg_light_yellow",
    "fg_magenta",
    "fg_red",
    "fg_reset",
    "fg_white",
    "fg_yellow",
    "reset",
]
