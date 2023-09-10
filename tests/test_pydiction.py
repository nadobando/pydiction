import datetime

import pytest

from pydiction import ANY, ANY_NOT_NONE, Contains, DoesntContains
from pydiction.operators import Expect


def test_matcher_with_equal_dicts(matcher):
    actual = {"a": 1, "b": 2}
    expected = {"a": 1, "b": 2}
    matcher.assert_declarative_object(actual, expected)


@pytest.mark.parametrize("expected", ({"a": 1, "b": 3}, {"a": 1}, {"a": 1, "c": 2}))
def test_matcher_with_unequal_dicts(matcher, expected):
    actual = {"a": 1, "b": 2}
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
    "actual, expected",
    [
        (
            {"visited": [{"_key": None, "_rev": None}, {"_id": None, "_key": None, "_rev": None}]},
            Contains({"visited": [Contains({"_key": pytest.approx(1)}), {"_id": None}]}),
        ),
        (
            {"edges": {"visited": [{"_from": None, "_to": None}, {"_from": None, "_to": None}]}},
            Contains({"edges": Contains({"visited": [{"_from": None}, {"_id": None}]})}),
        ),
        ([1], Contains([1, 2])),
        ("1", Contains("ads")),  # type: ignore[arg-type]
        ([1], [1, 2]),
    ],
)
def test_negative_cases(
    matcher,
    actual,
    expected,
):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object(actual, expected, strict_keys=True)


@pytest.mark.parametrize("actual,expected", [([1], [1, 2])])
def test_negative_case_check_order_false(
    matcher,
    actual,
    expected,
):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object(actual, expected, strict_keys=True, check_order=False)


def test_complex_comparison(matcher):
    actual = {
        "name": "John",
        "email": "john@example.com",
        "age": 25,
        "friends": [
            {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 21,
            }
        ],
        "comments": [{"text": "Great post!"}, {"text": "not existing post!"}],
        "likes": [
            {
                "title": "First Post",
                "content": "This is my first post!",
            },
            {"text": "Great post!"},
        ],
    }

    expected = {
        "name": ANY,
        "email": ANY,
        "age": ANY_NOT_NONE,
        "friends": [
            {
                "age": ANY_NOT_NONE,
                "email": ANY_NOT_NONE,
                "name": "Alice",
            }
        ],
        "comments": Expect({"text": "not existing post!"}).__contains__,
        "likes": Contains(
            [
                {
                    "content": ANY,
                    "title": "First Post",
                },
            ]
        ),
    }

    matcher.assert_declarative_object(actual, expected)


@pytest.mark.parametrize(
    "expected", (Expect("a").__contains__, Contains({"a": 1}), Contains({"a": 2}, check_pairs=False))
)
def test_simple_contains(matcher, expected):
    actual = {"a": 1, "b": 2}
    matcher.assert_declarative_object(actual, expected)


def test_recursive_contains(matcher):
    actual = {"a": {"b": 2, "c": {}}, "b": 3}
    expected = Contains(
        {
            "a": {
                "b": 2,
            },
            "b": 3,
        },
        recursive=True,
    )
    matcher.assert_declarative_object(actual, expected)


# def test_inner_recursive_contains(matcher):
#     actual = {"a": {"b": 2, "c": {}}, "b": 3}
#     expected = Contains(
#         Contains({
#             "a": {
#                 "b": 2,
#             },
#             "b": 3,
#         }),
#         # recursive=True,
#     )
#     matcher.assert_declarative_object(actual, expected)


def test_recursive_contains__fails(matcher):
    actual = {"a": {"b": 2, "c": {}}, "b": 3}
    expected = Contains(
        {
            "a": {
                "b": 3,
            },
            "b": 3,
        },
        recursive=True,
    )
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object(actual, expected)


def test_contains_list_with_dicts(matcher):
    actual = {
        "test": [
            {
                "_id": "comments/1091324",
                "_key": "1091324",
                "_rev": "_gmsWn4e--B",
                "text": "Great post!",
            },
            {
                "_id": "posts/1091323",
                "_key": "1091323",
                "_rev": "_gmsWn4e--A",
                "comments": None,
                "content": "This is my first post!",
                "title": "First Post",
            },
        ]
    }
    expected = {
        "test": Contains(
            [
                {"_id": ANY_NOT_NONE, "_key": ANY_NOT_NONE, "_rev": ANY_NOT_NONE, "text": "Great post!"},
                {
                    "_id": ANY_NOT_NONE,
                    "_key": ANY_NOT_NONE,
                    "_rev": ANY_NOT_NONE,
                    "comments": None,
                    "content": "This is my first post!",
                    "title": "First Post",
                },
            ],
        ),
    }

    matcher.assert_declarative_object(actual, expected)


def test_contains_nested_lists(matcher):
    actual = {
        "test": [
            [
                {
                    "_id": "comments/1091324",
                    "_key": "1091324",
                    "_rev": "_gmsWn4e--B",
                    "text": "Great post!",
                }
            ],
            [
                {
                    "_id": "posts/1091323",
                    "_key": "1091323",
                    "_rev": "_gmsWn4e--A",
                    "comments": None,
                    "content": "This is my first post!",
                    "title": "First Post",
                }
            ],
        ]
    }
    expected = {
        "test": Contains(
            [
                [{"_id": ANY_NOT_NONE, "_key": ANY_NOT_NONE, "_rev": ANY_NOT_NONE, "text": "Great post!"}],
                [
                    {
                        "_id": ANY_NOT_NONE,
                        "_key": ANY_NOT_NONE,
                        "_rev": ANY_NOT_NONE,
                        "comments": None,
                        "content": "This is my first post!",
                        "title": "First Post",
                    }
                ],
            ],
        ),
    }

    matcher.assert_declarative_object(actual, expected)


@pytest.mark.parametrize(
    "actual, expected",
    [
        (
            [[1]],
            DoesntContains([[1]]),
        ),
        ({"test": [{"test": 1}]}, DoesntContains({"test": [{"test": 1}]})),
        ({"test": [{"test": 1}]}, {"test": DoesntContains([{"test": 1}])}),
        ({"test": {"test": [1]}}, DoesntContains({"test": {"test": [1]}})),
    ],
)
def test_not_contains_negative_cases(matcher, actual, expected):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object(actual, expected, strict_keys=True)


def test_not_contains_nested_lists(matcher):
    actual = {
        "test": [
            [
                {
                    "_id": "comments/1091324",
                    "_key": "1091324",
                    "_rev": "_gmsWn4e--B",
                    "text": "Great post!",
                }
            ],
            [
                {
                    "_id": "posts/1091323",
                    "_key": "1091323",
                    "_rev": "_gmsWn4e--A",
                    "comments": None,
                    "content": "This is my first post!",
                    "title": "First Post",
                }
            ],
        ]
    }
    expected = {
        "test": Contains(
            [
                [{"_id": ANY_NOT_NONE, "_key": ANY_NOT_NONE, "_rev": ANY_NOT_NONE, "text": "Great post!"}],
                [
                    {
                        "_id": ANY_NOT_NONE,
                        "_key": ANY_NOT_NONE,
                        "_rev": ANY_NOT_NONE,
                        "comments": None,
                        "content": "This is my first post!",
                        "title": "First Post",
                    }
                ],
            ],
        ),
    }

    matcher.assert_declarative_object(actual, expected)


def test_1(matcher):
    datetime.datetime.now()
    e = {
        # "_id": ANY_NOT_NONE,
        # "_key": ANY_NOT_NONE,
        # "_rev": ANY_NOT_NONE,
        # "name": "John",
        # "age": 25,
        # "comments": [{"_id": ANY_NOT_NONE, "_key": ANY_NOT_NONE, "_rev": ANY_NOT_NONE, "text": "Great post!"}],
        # "edges": {
        #     "comments": [
        #         {
        #             "_from": ANY_NOT_NONE,
        #             "_id": ANY_NOT_NONE,
        #             "_key": ANY_NOT_NONE,
        #             "_rev": ANY_NOT_NONE,
        #             "_to": ANY_NOT_NONE,
        #             "commented_at": now,
        #         },
        #     ],
        #     "friends": [
        #         {
        #             "_from": ANY_NOT_NONE,
        #             "_id": ANY_NOT_NONE,
        #             "_key": ANY_NOT_NONE,
        #             "_rev": ANY_NOT_NONE,
        #             "_to": ANY_NOT_NONE,
        #             "since": now,
        #         }
        #     ],
        #     "likes": [
        #         {
        #             "_from": ANY_NOT_NONE,
        #             "_id": ANY_NOT_NONE,
        #             "_key": ANY_NOT_NONE,
        #             "_rev": ANY_NOT_NONE,
        #             "_to": ANY_NOT_NONE,
        #             "liked_at": now,
        #         },
        #         {
        #             "_from": ANY_NOT_NONE,
        #             "_id": ANY_NOT_NONE,
        #             "_key": ANY_NOT_NONE,
        #             "_rev": ANY_NOT_NONE,
        #             "_to": ANY_NOT_NONE,
        #             "liked_at": now,
        #         },
        #     ],
        #     "posts": [
        #         {
        #             "_from": ANY_NOT_NONE,
        #             "_id": ANY_NOT_NONE,
        #             "_key": ANY_NOT_NONE,
        #             "_rev": ANY_NOT_NONE,
        #             "_to": ANY_NOT_NONE,
        #             "created_at": now,
        #         }
        #     ],
        # },
        # "email": "john@example.com",
        # "friends": [
        #     {
        #         "_id": ANY_NOT_NONE,
        #         "_key": ANY_NOT_NONE,
        #         "_rev": ANY_NOT_NONE,
        #         "age": 21,
        #         "comments": None,
        #         "edges": None,
        #         "email": "alice@example.com",
        #         "friends": None,
        #         "likes": None,
        #         "name": "Alice",
        #         "posts": None,
        #     }
        # ],
        "likes": Contains(
            [
                {"_id": ANY_NOT_NONE, "_key": ANY_NOT_NONE, "_rev": ANY_NOT_NONE, "text": "Great post!"},
                {
                    "_id": ANY_NOT_NONE,
                    "_key": ANY_NOT_NONE,
                    "_rev": ANY_NOT_NONE,
                    "content": "This is my first post!",
                    "title": "First Post",
                },
            ]
        ),
        # "posts": [
        #     {
        #         "_id": ANY_NOT_NONE,
        #         "_key": ANY_NOT_NONE,
        #         "_rev": ANY_NOT_NONE,
        #         "comments": None,
        #         "content": "This is my first post!",
        #         "title": "First Post",
        #     }
        # ],
    }
    a = {
        # "_id": "users/1191704",
        # "_key": "1191704",
        # "_rev": "_gn91JF2---",
        # "name": "John",
        # "email": "john@example.com",
        # "age": 25,
        # "friends": [
        #     {
        #         "_id": "users/1191705",
        #         "_key": "1191705",
        #         "_rev": "_gn91JF2--_",
        #         "name": "Alice",
        #         "email": "alice@example.com",
        #         "age": 21,
        #         "friends": None,
        #         "posts": None,
        #         "comments": None,
        #         "likes": None,
        #         "edges": None,
        #     }
        # ],
        # "posts": [
        #     {
        #         "_id": "posts/1191706",
        #         "_key": "1191706",
        #         "_rev": "_gn91JF6---",
        #         "title": "First Post",
        #         "content": "This is my first post!",
        #         "comments": [
        #             {"_id": "comments/1191707", "_key": "1191707", "_rev": "_gn91JF6--_", "text": "Great post!"}
        #         ],
        #     }
        # ],
        # "comments": [{"_id": "comments/1191707", "_key": "1191707", "_rev": "_gn91JF6--_", "text": "Great post!"}],
        "likes": [
            {
                "_id": "posts/1191706",
                "_key": "1191706",
                "_rev": "_gn91JF6---",
                "title": "First Post",
                "content": "This is my first post!",
                "comments": [
                    {"_id": "comments/1191707", "_key": "1191707", "_rev": "_gn91JF6--_", "text": "Great post!"}
                ],
            },
            {"_id": "comments/1191707", "_key": "1191707", "_rev": "_gn91JF6--_", "text": "Great post!"},
        ],
        # "edges": {
        #     "friends": [
        #         {
        #             "_id": "friendships/1191708",
        #             "_key": "1191708",
        #             "_rev": "_gn91JG----",
        #             "_from": "users/1191704",
        #             "_to": "users/1191705",
        #             "since": now,
        #         }
        #     ],
        #     "posts": [
        #         {
        #             "_id": "authorships/1191709",
        #             "_key": "1191709",
        #             "_rev": "_gn91JGC---",
        #             "_from": "users/1191704",
        #             "_to": "posts/1191706",
        #             "created_at": now,
        #         }
        #     ],
        #     "comments": [
        #         {
        #             "_id": "commentaries/1191711",
        #             "_key": "1191711",
        #             "_rev": "_gn91JGK---",
        #             "_from": "users/1191704",
        #             "_to": "comments/1191707",
        #             "commented_at": now,
        #         }
        #     ],
        #     "likes": [
        #         {
        #             "_id": "likes/1191713",
        #             "_key": "1191713",
        #             "_rev": "_gn91JGS---",
        #             "_from": "users/1191704",
        #             "_to": "posts/1191706",
        #             "liked_at": now,
        #         },
        #         {
        #             "_id": "likes/1191712",
        #             "_key": "1191712",
        #             "_rev": "_gn91JGO---",
        #             "_from": "users/1191704",
        #             "_to": "comments/1191707",
        #             "liked_at": now,
        #         },
        #     ],
        # },
    }
    matcher.assert_declarative_object(a, e)
