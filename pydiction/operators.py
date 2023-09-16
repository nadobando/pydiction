from typing import Optional, TypeVar
from unittest.mock import ANY


class _ANY_NOT_NONE(ANY.__class__):
    "A helper object that compares equal to everything."

    def __eq__(self, other):
        if other is None:
            return False
        return True

    def __ne__(self, other):
        if other is None:
            return True
        return False

    def __repr__(self):
        return "<ANY_NOT_NONE>"

    def __hash__(self):
        return hash(repr(self))


T = TypeVar("T")


class Expectation:
    """
    class to inverse the left operand with the right operand so the expectation are applied on the actual value
    """

    __error_mapping__: dict[str, str] = {}

    def __init__(self, expected: T, error_msg: Optional[str] = None):
        self.error_msg = error_msg
        self.expected: T = expected

    def __eq__(self, other: T) -> bool:
        return other.__eq__(self.expected)

    def __ne__(self, other: T) -> bool:
        return other.__ne__(self.expected)

    def __ge__(self, other: T) -> bool:
        return other.__ge__(self.expected)  # type: ignore[operator]

    def __gt__(self, other: T) -> bool:
        return other.__gt__(self.expected)  # type: ignore[operator]

    def __le__(self, other: T) -> bool:
        return other.__le__(self.expected)  # type: ignore[operator]

    def __lt__(self, other: T) -> bool:
        return other.__lt__(self.expected)  # type: ignore[operator]

    def __contains__(self, other: T) -> bool:
        return other.__contains__(self.expected)  # type: ignore[operator]

    def __getattribute__(self, item):
        error_mapping = object.__getattribute__(self, "__error_mapping__")
        if item in error_mapping:
            item_ = error_mapping[item]
            setattr(self, "error_msg", item_)
        #
        return object.__getattribute__(self, item)


class Expect(Expectation):
    __error_mapping__: dict[str, str] = {
        "__eq__": "not equals",
        "__ne__": "equals",
        "__ge__": "not greater or equal",
        "__gt__": "not greater than (expected)",
        "__le__": "greater (expected)",
        "__lt__": "greater or equal (expected)",
        "__contains__": "should contain",
    }


class ExpectNot(Expectation):
    __error_mapping__: dict[str, str] = {
        "__eq__": "equals (not expected)",
        "__ne__": "not equals (expected)",
        "__ge__": "lower or equal (not expected)",
        "__gt__": "lower (not expected)",
        "__le__": "greater (not expected)",
        "__lt__": "greater or equal (not expected)",
        "__contains__": "contains (not expected)",
    }

    def __eq__(self, other: T) -> bool:
        return not super().__eq__(other)

    def __ne__(self, other: T) -> bool:
        return not super().__ne__(other)

    def __ge__(self, other: T) -> bool:
        return not super().__ge__(other)

    def __gt__(self, other: T) -> bool:
        return not super().__gt__(other)

    def __le__(self, other: T) -> bool:
        return not super().__le__(other)

    def __lt__(self, other: T) -> bool:
        return not super().__lt__(other)

    def __contains__(self, other: T) -> bool:
        return not super().__contains__(other)


ANY_NOT_NONE = _ANY_NOT_NONE()
