from dataclasses import dataclass
from typing import Any


@dataclass
class CannotDetectOtherHooksError(Exception):
    def __str__(self) -> str:
        return "Other hooks detection aborted to avoid infinite loop ('hook_file_path' missing)"


@dataclass
class NoOtherHooksMatchedError(Exception):
    def __str__(self) -> str:
        return "No other hooks matched"


@dataclass
class ParamMustBeSequenceError(Exception):
    param_name: str = ""
    value: Any = ""

    def __str__(self) -> str:
        return (
            f"'{self.param_name}' param must be sequence, but provided"
            f" the '{self.value.__class__.__name__}' with value '{self.value}'"
        )


@dataclass
class InvalidPathCommitMsgError(Exception):
    def __str__(self) -> str:
        return "Hook 'commit-msg' got invalid path for 'COMMIT_EDITMSG'"


@dataclass
class InvalidGitPathError(Exception):
    def __str__(self) -> str:
        return "Invalid path for a hook or wrong git folder"
