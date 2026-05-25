import sys

__all__ = [
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

reset = ""
blink = ""
fg_black = ""
fg_red = ""
fg_green = ""
fg_yellow = ""
fg_blue = ""
fg_magenta = ""
fg_cyan = ""
fg_white = ""
fg_reset = ""
bg_black = ""
bg_red = ""
bg_green = ""
bg_yellow = ""
bg_blue = ""
bg_magenta = ""
bg_cyan = ""
bg_white = ""
bg_reset = ""
fg_light_black = ""
fg_light_red = ""
fg_light_green = ""
fg_light_yellow = ""
fg_light_blue = ""
fg_light_magenta = ""
fg_light_cyan = ""
fg_light_white = ""
bg_light_black = ""
bg_light_red = ""
bg_light_green = ""
bg_light_yellow = ""
bg_light_blue = ""
bg_light_magenta = ""
bg_light_cyan = ""
bg_light_white = ""


def is_cli() -> bool:
    return bool(sys.stdin.isatty() or sys.stdout.isatty())


if is_cli():
    reset = "\x1b[0m"
    blink = "\x1b[5m"
    fg_black = "\x1b[30m"
    fg_red = "\x1b[31m"
    fg_green = "\x1b[32m"
    fg_yellow = "\x1b[33m"
    fg_blue = "\x1b[34m"
    fg_magenta = "\x1b[35m"
    fg_cyan = "\x1b[36m"
    fg_white = "\x1b[37m"
    fg_reset = "\x1b[39m"
    bg_black = "\x1b[40m"
    bg_red = "\x1b[41m"
    bg_green = "\x1b[42m"
    bg_yellow = "\x1b[43m"
    bg_blue = "\x1b[44m"
    bg_magenta = "\x1b[45m"
    bg_cyan = "\x1b[46m"
    bg_white = "\x1b[47m"
    bg_reset = "\x1b[49m"
    fg_light_black = "\x1b[90m"
    fg_light_red = "\x1b[91m"
    fg_light_green = "\x1b[92m"
    fg_light_yellow = "\x1b[93m"
    fg_light_blue = "\x1b[94m"
    fg_light_magenta = "\x1b[95m"
    fg_light_cyan = "\x1b[96m"
    fg_light_white = "\x1b[97m"
    bg_light_black = "\x1b[100m"
    bg_light_red = "\x1b[101m"
    bg_light_green = "\x1b[102m"
    bg_light_yellow = "\x1b[103m"
    bg_light_blue = "\x1b[104m"
    bg_light_magenta = "\x1b[105m"
    bg_light_cyan = "\x1b[106m"
    bg_light_white = "\x1b[107m"
