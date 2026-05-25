import pytest

from conftest import MockFilesystem
from githooks.hooks.commit_msg import CommitMsg


class TestCommitMsg:
    def test_parse_title_none(self) -> None: ...

    def test_parse_title_with_arg(self) -> None:
        commit_msg = CommitMsg(__file__)

        commit_msg.parse_title("general improvement")
        assert commit_msg.title == "general improvement"
        assert commit_msg.type == "general improvement"
        assert commit_msg.scope == ""
        assert commit_msg.subject == ""
        assert not commit_msg.breaking

        commit_msg.parse_title("fix: something was improved")
        assert commit_msg.title == "fix: something was improved"
        assert commit_msg.type == "fix"
        assert commit_msg.scope == ""
        assert commit_msg.subject == "something was improved"
        assert not commit_msg.breaking

        commit_msg.parse_title("fix(api): something was improved")
        assert commit_msg.title == "fix(api): something was improved"
        assert commit_msg.type == "fix"
        assert commit_msg.scope == "api"
        assert commit_msg.subject == "something was improved"
        assert not commit_msg.breaking

        commit_msg.parse_title("fix(api)!: something was improved")
        assert commit_msg.title == "fix(api)!: something was improved"
        assert commit_msg.type == "fix"
        assert commit_msg.scope == "api"
        assert commit_msg.subject == "something was improved"
        assert commit_msg.breaking

    def test_load_message_file(self) -> None:
        mfs = MockFilesystem({".git/COMMIT_EDITMSG": "fake file"})
        commit_msg = CommitMsg(__file__)
        commit_msg.message_file_path = ".git/COMMIT_EDITMSG"
        commit_msg.load_message_file(open_fn=mfs.open)
        assert commit_msg.title == "fake file"

    # def insert_into_content(self) -> None:
    #     commit_msg = CommitMsg(__file__)
    #     commit_msg.lines = ["test title"]
    #     commit_msg.title = "test title"
    #     commit_msg.insert_into_content(0, 0, "🗸")


@pytest.mark.xfail(reason="This test should fail", strict=True)
def test_force_fail() -> None:
    pytest.fail(reason="development purpose")
