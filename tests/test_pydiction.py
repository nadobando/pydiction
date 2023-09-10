import pytest

from pydiction import Contains, DoesntContains, Matcher


@pytest.fixture
def matcher():
    return Matcher()


def test_matcher_with_equal_dicts(matcher):
    actual = {"a": 1, "b": 2}
    expected = {"a": 1, "b": 2}
    matcher.assert_declarative_object(actual, expected)


def test_matcher_with_unequal_dicts(matcher):
    actual = {"a": 1, "b": 2}
    expected = {"a": 1, "b": 3}
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object(actual, expected)


def test_matcher_with_contains(matcher):
    actual = {"a": 1, "b": 2}
    expected = Contains({"a": 1})
    matcher.assert_declarative_object(actual, expected)


def test_matcher_with_doesnt_contains(matcher):
    actual = {"a": 1, "b": 2}
    expected = DoesntContains({"c": 3})
    matcher.assert_declarative_object(actual, expected)


# More complex test cases with nested operators.
def test_nested_contains_dict(matcher):
    actual = {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}}
    expected = Contains({"a": Contains({"x": 1}), "b": Contains({"x": 3})})
    matcher.assert_declarative_object(actual, expected)


def test_nested_doesnt_contains_dict(matcher):
    actual = {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}}
    expected = {"a": DoesntContains({"z": 5}), "b": Contains({"y": 4})}

    matcher.assert_declarative_object(actual, expected)


def test_nested_contains_list(matcher):
    actual = {"items": [{"name": "item1"}, {"name": "item2"}]}
    expected = Contains({"items": [Contains({"name": "item1"}), Contains({"name": "item2"})]})
    matcher.assert_declarative_object(actual, expected)


def test_nested_doesnt_contains_list(matcher):
    actual = {"items": [{"name": "item1"}, {"name": "item2"}]}
    expected = {"items": DoesntContains([{"name": "item3"}])}
    matcher.assert_declarative_object(actual, expected)


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}},
            Contains({"a": Contains({"x": 1}), "b": Contains({"x": 3})}),
        ),
        (
            {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}},
            Contains({"a": DoesntContains({"z": 5}), "b": Contains({"y": 4})}),
        ),
        (
            {"items": [{"name": "item1"}, {"name": "item2"}]},
            Contains({"items": Contains([{"name": "item1"}, {"name": "item2"}])}),
        ),
        (
            {"items": [{"name": "item1"}, {"name": "item2"}]},
            {"items": DoesntContains([{"name": "item3"}])},
        ),
    ],
    ids=["Nested Contains", "Nested Doesnt Contains", "Nested Contains List", "Nested Doesnt Contains List"],
)
def test_nested_cases(matcher, actual, expected):
    matcher.assert_declarative_object(actual, expected)


@pytest.mark.parametrize(
    "actual, expected, error_message",
    [
        (
            {"visited": [{"_key": None, "_rev": None}, {"_id": None, "_key": None, "_rev": None}]},
            Contains({"visited": [Contains({"_key": pytest.approx(1)}), {"_id": None}]}),
            (
                "\nKeys in dictionaries do not match: {'_rev', '_id', '_key'} != {'_id'}\nValue at path visited.0._key"
                " does not match: 1 ± 1.0e-06 != None"
            ),
        ),
        (
            {"edges": {"visited": [{"_from": None, "_to": None}, {"_from": None, "_to": None}]}},
            Contains({"edges": Contains({"visited": [{"_from": None}, {"_id": None}]})}),
            "\nKey '_id' not found at path edges.visited.1",
        ),
    ],
)
def test_negative_cases(matcher, actual, expected, error_message):
    with pytest.raises(AssertionError) as e:
        matcher.assert_declarative_object(actual, expected, strict_keys=True)

    assert str(e.value) == error_message
