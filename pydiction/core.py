from functools import partial
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Sequence,
    TypeVar,
    Union,
    cast,
    overload,
)
from unittest.mock import ANY

T = TypeVar("T")


def hash_any(expected, actual):
    """
    Create a hash that takes into consideration 'ANY' and 'ANY_NOT_NONE'.
    """
    if not any(isinstance(obj, (dict, list)) for obj in (expected, actual)):
        return hash((expected, actual))

    item_hashes = []
    for key in zip(expected, actual):
        if key in actual:
            actual_value = actual[key]
        else:
            actual_value = NOT_SET

        if key in expected:
            expected_value = expected[key]
            if isinstance(key, (dict, list)):  # list case
                item_hashes.extend(hash_any(expected_value, actual_value))
        else:
            expected_value = NOT_SET

        # actual_value = actual.get(key)

        if expected_value is ANY:
            item_hashes.append(hash(ANY))
        elif expected_value is ANY_NOT_NONE:
            if actual_value is not None:
                item_hashes.append(hash(ANY_NOT_NONE))
            else:
                item_hashes.append(hash(None))
        else:
            item_hashes.append(
                hash_any(
                    expected_value,
                    actual_value,
                )
            )

    return hash(tuple(item_hashes))


def sentinel(name: str):
    return type(name, (object,), {"__repr__": lambda x: f"<{name}>"})()


class _ANY_NOT_NONE(object):
    "A helper object that compares equal to everything."

    def __eq__(self, other):
        if other is None:
            return False
        return True

    def __ne__(self, other):
        if other is None:
            return True
        return super().__eq__(other)

    def __repr__(self):
        return "<ANY_NOT_NONE>"

    def __hash__(self):
        return hash(repr(self))


NOT_SET = sentinel("NOT_SET")
ANY_NOT_NONE = _ANY_NOT_NONE()


class ComparableList(list):
    def __contains__(self, item):
        if isinstance(item, dict):
            return all([len(Matcher().get_declarative_diff(item, i)) == 0 for i in self])
        if isinstance(item, list):
            return any([item in ComparableList(i) for i in self])
        return super().__contains__(item)


class HashableDict(dict):
    def __init__(self, *args, custom_hash=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_hash = custom_hash

    def __eq__(self, other):
        return Matcher().assert_declarative_object(other, self)

    def __hash__(self):
        if self.custom_hash:
            return self.custom_hash(self)
        else:
            return hash(frozenset(self.items()))

    def __contains__(self, item):
        return super().__contains__(item)


class Matcher:
    def __init__(self, check_order: bool = True, strict_keys: bool = True):
        self.check_order = check_order
        self.strict_keys = strict_keys

    def match(
        self, actual: Any, expected: Any, path: List[str], *, strict_keys=None
    ) -> list[tuple[Sequence, str, Any, ANY]]:
        strict_keys = strict_keys if strict_keys is not None else self.strict_keys
        errors = []
        if isinstance(expected, Contains):
            errors += expected.match(actual, path, self, strict_keys=strict_keys)
        elif isinstance(expected, DoesntContains):
            errors += expected.match(actual, path, self)
        elif expected is ANY:
            return errors
        elif expected is ANY_NOT_NONE and actual is not None:
            return errors
        elif isinstance(expected, dict) and isinstance(actual, dict):
            actual = HashableDict(actual.items(), custom_hash=partial(hash_any, expected))
            expected = HashableDict(expected.items(), custom_hash=partial(hash_any, expected))
            errors += self._compare_dicts(actual, expected, path, strict_keys)
        elif isinstance(expected, list) and isinstance(actual, list):
            errors += self._compare_lists(actual, expected, path, strict_keys=strict_keys)
        else:
            errors += self._compare_values(actual, expected, path)
        return errors

    @staticmethod
    def _compare_values(actual: Any, expected: Any, path: List[str]) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []
        if expected is ANY:
            return errors
        elif expected is ANY_NOT_NONE and actual is not None:
            return errors
        elif expected != actual:
            errors.append((path, "does not match", actual, expected))
        return errors

    def _compare_dicts(
        self, actual: Dict[str, Any], expected: Dict[str, Any], path: List[str], strict_keys
    ) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []

        strict_keys = strict_keys or self.strict_keys
        if isinstance(expected, (Contains, DoesntContains)):
            errors.extend(expected.match(actual, path, self))
        else:
            for key, expected_value in expected.items():
                actual_value = actual.get(key)
                if key not in actual:
                    errors.append((path + [key], "not found", actual, expected_value))
                else:
                    errors.extend(self.match(actual_value, expected_value, path + [key], strict_keys=strict_keys))
        return errors

    def _compare_lists(
        self, actual: List[Any], expected: List[Any], path: List[str], *, strict_keys
    ) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []

        strict_keys = strict_keys or self.strict_keys

        expected = isinstance(expected, list) and ComparableList(expected)
        actual = isinstance(actual, list) and ComparableList(actual)

        if len(actual) != len(expected):
            errors.append((path, "Lists have different lengths", len(actual), len(expected)))

        if self.check_order:
            for i, (actual_item, expected_item) in enumerate(zip(actual, expected)):
                errors.extend(self.match(actual_item, expected_item, path + [str(i)], strict_keys=strict_keys))
        else:
            expected_set = set(expected)
            actual_set = set(actual)

            if expected_set != actual_set:
                errors.append((path, "different elements (ignoring order)", actual_set, expected_set))
        return errors

    @overload
    def assert_declarative_object(
        self, actual: list, expected: Union[list, "BaseOperator"], strict_keys=True, check_order=True
    ) -> None: ...

    @overload
    def assert_declarative_object(
        self,
        actual: Dict[str, Any],
        expected: Union[Dict[str, Any], "BaseOperator"],
        strict_keys=True,
        check_order=True,
    ) -> None: ...

    def assert_declarative_object(
        self,
        actual: Union[Dict[str, Any], list],
        expected: Union[Dict[str, Any], list, "BaseOperator"],
        strict_keys=True,
        check_order=True,
    ) -> None:
        errors = self.match(actual, expected, [], strict_keys=strict_keys)
        self.errors = errors
        self._raise_errors()

    def get_declarative_diff(
        self,
        actual: Dict[str, Any],
        expected: Union[Dict[str, Any], "BaseOperator"],
        strict_keys=True,
        check_order=True,
    ) -> list:
        return self.match(actual, expected, [], strict_keys=strict_keys)
        # return self.errors.to_object()

    def _raise_errors(self) -> None:
        # assert self.errors == {},
        if self.errors:
            raise AssertionError("\n" + "\n".join([str((".".join(i[0]), *i[1:])) for i in self.errors]))


class BaseOperator:
    pass


class Contains(Generic[T], Iterable, BaseOperator):
    def __init__(self, iterable: Union[Dict[str, T], List[T]], *, recursive=False, check_pairs=True):
        if isinstance(iterable, list):
            iterable = ComparableList(iterable)
        elif isinstance(iterable, dict):
            iterable = HashableDict(iterable)
        self.iterable = iterable

        self.recursive = recursive
        self.check_pairs = check_pairs

    def __iter__(self):
        return iter(self.iterable)

    def match(self, actual, path, matcher: Matcher, *, strict_keys=True) -> list[tuple[Sequence, str, Any, ANY]]:
        strict_keys = strict_keys if strict_keys is not None else matcher.strict_keys
        errors: list[tuple[Sequence, str, Any, ANY]] = []

        if isinstance(self.iterable, (Contains, DoesntContains)):
            return self.iterable.match(actual, path, matcher, strict_keys=strict_keys)
        elif isinstance(actual, dict):
            for key, expected_value in cast(HashableDict, self.iterable).items():
                actual_value = actual.get(key)
                key_ = path + [key]
                if self.recursive and isinstance(actual_value, (list, dict)):
                    errors += Contains(expected_value, recursive=self.recursive).match(actual_value, key_, matcher)
                else:
                    if isinstance(expected_value, (Contains, DoesntContains)):
                        errors += expected_value.match(actual_value, key_, matcher)
                    else:
                        if key not in actual:
                            errors.append((key_, "not found", actual_value, expected_value))
                        elif self.check_pairs:
                            errors += matcher.match(
                                actual_value, expected_value, key_, strict_keys=strict_keys or matcher.strict_keys
                            )

        elif isinstance(actual, list):
            if len(actual) < len(self.iterable):
                errors.append((path, "List is too short", actual, self.iterable))
            else:
                for i, expected_item in enumerate(self.iterable):
                    tmp_path = path + [str(i)]
                    to_be_found = True
                    for actual_item in actual:
                        if not to_be_found:
                            continue
                        if isinstance(actual_item, dict):
                            if self.recursive and not isinstance(self.iterable, (Contains, DoesntContains)):
                                expected_item = Contains(expected_item, recursive=self.recursive)

                            if isinstance(expected_item, (Contains, DoesntContains)):
                                diff = expected_item.match(actual_item, tmp_path, matcher)
                                if not diff:
                                    to_be_found = False
                                    continue

                            else:
                                diff = matcher.match(actual_item, expected_item, tmp_path)
                                if not diff:
                                    to_be_found = False
                                    continue

                        elif isinstance(actual_item, list):
                            raise NotImplementedError("Should add this")
                            # return any([actual_item in ComparableList(i) for i in expected_item])
                        elif list.__contains__(cast(ComparableList, self.iterable), actual_item):
                            continue
                        else:
                            errors.append((tmp_path, "not_found", actual_item, expected_item))
                    if to_be_found:
                        errors += [(tmp_path, "not found", NOT_SET, expected_item)]
        else:
            errors.append((path, "Contains can only be used with dictionaries or lists", actual, self.iterable))

        return errors

    def __repr__(self):
        return f"<Contains: {repr(self.iterable)}>"


class DoesntContains(Generic[T], Iterable, BaseOperator):
    def __init__(
        self,
        iterable: Union[Dict[str, T], List[T]],
    ):
        if isinstance(iterable, list):
            iterable = ComparableList(iterable)
        elif isinstance(iterable, dict):
            iterable = HashableDict(iterable)

        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable)

    def match(self, actual, path, _: Matcher, **kwargs) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []
        if isinstance(actual, dict):
            for key, expected_value in cast(HashableDict, self.iterable).items():
                actual_value = actual.get(key)
                if actual_value is not None:
                    errors.append((path, f"should not contain {key}", actual_value, NOT_SET))

        elif isinstance(actual, list):
            if len(actual) < len(self.iterable):
                errors.append((path, "list is too short", len(actual), len(self.iterable)))

            else:
                for i, expected_item in enumerate(self.iterable):
                    actual_item = actual[i]
                    if isinstance(actual_item, dict):
                        if expected_item in actual:
                            errors.append((path, f"list should not contain {expected_item}", actual_item, NOT_SET))

                    elif actual_item in self.iterable:
                        errors.append((path, f"list should not contain {expected_item}", actual_item, NOT_SET))

        return errors

    def __repr__(self):
        return repr(self.iterable)
