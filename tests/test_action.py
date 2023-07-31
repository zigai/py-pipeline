from pypipeline.action import parse_action
from pypipeline.filter import GlobFilter, TextPatternFilter


def test_to_dict():
    txt_filter = TextPatternFilter("*.py")
    print(txt_filter.dict())
    assert txt_filter.dict() == {
        "name": "text-pattern-filter",
        "type": "filter",
        "args": {"pattern": "*.py"},
    }

    glob_filter = GlobFilter("*.py")
    assert glob_filter.dict() == {
        "name": "glob-filter",
        "type": "filter",
        "args": {"pattern": "*.py"},
    }


def test_parse_action():
    actions = {"text-pattern-filter": TextPatternFilter, "glob-filter": GlobFilter}
    assert (
        parse_action(
            {
                "name": "text-pattern-filter",
                "type": "filter",
                "args": {"pattern": "*.py"},
            },
            actions,
        ).dict()
        == TextPatternFilter("*.py").dict()
    )
    assert (
        parse_action(
            {
                "name": "glob-filter",
                "type": "filter",
                "args": {"pattern": "*.py"},
            },
            actions,
        ).dict()
        == GlobFilter("*.py").dict()
    )
