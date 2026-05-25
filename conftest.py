class MockFile:
    def __init__(
        self,
        filename: str,
        content: str,
        line_sep: str = "\n",
    ) -> None:
        self.filename = filename
        self.content = content.split(line_sep)

    def __enter__(self) -> list[str]:
        return self.content

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        pass


class MockFilesystem:
    def __init__(self, files: dict[str, str]) -> None:
        self.files = files

    def open(self, path: str) -> MockFile:
        return MockFile(path, self.files[path])
