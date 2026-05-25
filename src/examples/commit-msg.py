#!/usr/bin/env python
from githooks import CommitMsg, Glyphs, Priority

commit_msg = CommitMsg(__file__)
commit_msg.custom_check(
    commit_msg.title == 42,
    glyph=Glyphs.question_mark_white,
    glyph_space=1,
    category="custom check for 'title == 42'",
    msg=f"custom check {'ok' if commit_msg.title == 42 else f"fail '{commit_msg.title}' != 42"}",
    # priority=Priority.HIGH,
    # priority=Priority.MEDIUM,
    priority=Priority.LOW,
)
# commit_msg.check_other_hooks(prefix_in=["commit-msg"], suffix_not_in=["sample"])
commit_msg.check_title_regex_fullmatch(
    r"""^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([\w\-]+\))?(!)?: .+$""",
    priority=Priority.HIGH,
)
commit_msg.check_title_regex_search(r"^(feat|fix)", priority=Priority.MEDIUM)
commit_msg.check_title_regex_match(r"[A-Za-z]+", priority=Priority.MEDIUM)
commit_msg.check_title_contains_words_set({"client"})
commit_msg.check_content_contains_words_set({"fix"})
commit_msg.check_title_conventional_commit()
commit_msg.check_content_forbidden_words_set({":"}, glyph=Glyphs.no_entry, priority=Priority.LOW)
commit_msg.check_content_forbidden_words_set()
commit_msg.check_content_spelling()
commit_msg.check_title_length(60)
commit_msg.insert_into_content(0, 7, "🎯 ")
commit_msg.report(force_return_code=1, include_successful=True)
