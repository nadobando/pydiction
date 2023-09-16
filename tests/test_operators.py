import pytest

from pydiction.operators import ANY_NOT_NONE, Expect, ExpectNot

TEST_KEY = "test"


@pytest.mark.parametrize(
    "actual,expected",
    (
        (1, Expect(1).__eq__),
        (1, Expect(0).__ne__),
        (1, Expect(0).__gt__),
        (1, Expect(0).__ge__),
        (1, Expect(1).__ge__),
        (0, Expect(1).__lt__),
        (0, Expect(0).__le__),
        (0, Expect(1).__le__),
        ("abc", Expect("b").__contains__),
        (0, lambda x: x < 1),
    ),
)
def test_expect_operators(matcher, actual, expected):
    matcher.assert_declarative_object({TEST_KEY: actual}, {TEST_KEY: expected})


@pytest.mark.parametrize(
    "actual,expected",
    (
        (0, ExpectNot(1).__eq__),
        (0, ExpectNot(0).__ne__),
        (0, ExpectNot(0).__gt__),
        (0, ExpectNot(1).__gt__),
        (0, ExpectNot(1).__ge__),
        (1, ExpectNot(0).__lt__),
        (1, ExpectNot(1).__lt__),
        (1, ExpectNot(0).__le__),
        ("abc", ExpectNot("z").__contains__),
    ),
)
def test_does_not_expect(matcher, actual, expected):
    matcher.assert_declarative_object({TEST_KEY: actual}, {TEST_KEY: expected})


@pytest.mark.parametrize(
    "actual, expected",
    (
        (1, Expect(0).__eq__),
        (1, Expect(1).__ne__),
        (0, Expect(1).__gt__),
        (0, Expect(0).__gt__),
        (0, Expect(1).__ge__),
        (1, Expect(1).__lt__),
        (1, Expect(0).__lt__),
        (1, Expect(0).__le__),
        ("abc", Expect("d").__contains__),
        (0, lambda x: x < 0),
    ),
)
def test_expect_negative(matcher, actual, expected):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object({TEST_KEY: actual}, {TEST_KEY: expected})


@pytest.mark.parametrize(
    "actual, expected",
    (
        (1, ExpectNot(1).__eq__),
        (1, ExpectNot(0).__ne__),
        (1, ExpectNot(0).__gt__),
        (1, ExpectNot(0).__ge__),
        (1, ExpectNot(2).__lt__),
        (1, ExpectNot(1).__le__),
        ("abc", ExpectNot("b").__contains__),
    ),
)
def test_does_not_expect_negative(matcher, actual, expected):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object({TEST_KEY: actual}, {TEST_KEY: expected})


@pytest.mark.parametrize(
    "actual, expected",
    (
        (1, ANY_NOT_NONE),
        ("abc", ANY_NOT_NONE),
    ),
)
def test_any_not_none_eq_positive(matcher, actual, expected):
    matcher.assert_declarative_object({TEST_KEY: actual}, {TEST_KEY: expected})


def test_any_not_none_eq_negative(matcher):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object({TEST_KEY: None}, {TEST_KEY: ANY_NOT_NONE})


@pytest.mark.parametrize(
    "actual, expected",
    (
        (1, ANY_NOT_NONE),
        ("abc", ANY_NOT_NONE),
    ),
)
def test_any_not_none_ne_positive(matcher, actual, expected):
    matcher.assert_declarative_object({TEST_KEY: actual}, {TEST_KEY: expected})


def test_any_not_none_ne_negative(matcher):
    with pytest.raises(AssertionError):
        matcher.assert_declarative_object({TEST_KEY: None}, {TEST_KEY: ANY_NOT_NONE})


def test_any_not_none():
    assert ANY_NOT_NONE is not None
    assert 1 == ANY_NOT_NONE
    assert ANY_NOT_NONE == 1
