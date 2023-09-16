import itertools
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

from pydiction.operators import Expectation
from pydiction.utils import sentinel

T = TypeVar("T")

NOT_SET: object = sentinel("NOT_SET")


def is_same_type(actual, expected, type_):
    return isinstance(expected, type_) and isinstance(actual, type_)


class Matcher:
    def match(
        self, actual: Any, expected: Any, path: List[str], *, strict_keys=True, check_order=True
    ) -> list[tuple[Sequence, str, Any, ANY]]:
        # if expected is ANY or (expected is ANY_NOT_NONE and actual == ANY_NOT_NONE):
        #     return []

        if isinstance(expected, Contains):
            errors = expected.match(actual, path, self, strict_keys=strict_keys, check_order=check_order)
        elif isinstance(expected, DoesntContains):
            errors = expected.match(actual, path, self)
        elif is_same_type(actual, expected, dict):
            errors = self._compare_dicts(actual, expected, path, strict_keys)
        elif is_same_type(actual, expected, list):
            errors = self._compare_lists(actual, expected, path, strict_keys=strict_keys, check_order=check_order)
        else:
            errors = self._compare_values(actual, expected, path)

        return errors

    @staticmethod
    def _compare_values(actual: Any, expected: Any, path: Sequence[str]) -> list[tuple[Sequence, str, Any, Any]]:
        errors: list[tuple[Sequence, str, Any, Any]] = []
        if callable(expected):
            if not expected(actual):
                if hasattr(expected, "__self__") and isinstance(expected.__self__, Expectation):
                    errors.append((path, expected.__self__.error_msg or "", actual, expected.__self__.expected))
                else:
                    errors.append((path, expected.__name__ or "", actual, "UNKNOWN"))
        elif actual != expected:
            errors.append((path, "does not match", actual, expected))

        return errors

    def _compare_dicts(
        self, actual: Dict[str, Any], expected: Dict[str, Any], path: List[str], strict_keys=None
    ) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []
        if isinstance(expected, (Contains, DoesntContains)):
            errors.extend(expected.match(actual, path, self))
        else:
            errors.extend(
                [(path + [key], "not expected", actual.get(key), NOT_SET) for key in actual.keys() - expected.keys()]
            )
            for key, expected_value in expected.items():
                actual_value = actual.get(key)
                if key not in actual:
                    errors.append((path + [key], "not found", NOT_SET, expected_value))
                else:
                    errors.extend(
                        self.match(
                            actual_value, expected_value, path + [key], strict_keys=strict_keys, check_order=False
                        )
                    )

        return errors

    def _compare_lists(
        self, actual: List[Any], expected: List[Any], path: List[str], *, strict_keys=True, check_order=True
    ) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []

        if len(actual) != len(expected):
            errors.append((path, "Lists have different lengths", len(actual), len(expected)))
        if check_order:
            for i, (actual_item, expected_item) in enumerate(zip(actual, expected)):
                errors.extend(
                    self.match(
                        actual_item, expected_item, path + [str(i)], strict_keys=strict_keys, check_order=check_order
                    )
                )
        else:
            actual_permutations = itertools.permutations(actual)
            for perm in actual_permutations:
                if list(perm) == expected:
                    return errors

            if actual != expected:
                errors.append((path, "different elements (ignoring order)", actual, expected))
        return errors

    @overload
    def assert_declarative_object(
        self, actual: list, expected: Union[list, "BaseOperator"], strict_keys=True, check_order=True
    ) -> None:  # pragma: no cover
        ...

    @overload
    def assert_declarative_object(
        self,
        actual: Dict[str, Any],
        expected: Union[Dict[str, Any], "BaseOperator"],
        strict_keys=True,
        check_order=True,
    ) -> None:  # pragma: no cover
        ...

    def assert_declarative_object(
        self,
        actual: Union[Dict[str, Any], list],
        expected: Union[Dict[str, Any], list, "BaseOperator"],
        strict_keys=True,
        check_order=True,
    ) -> None:
        errors = self.match(actual, expected, [], strict_keys=strict_keys, check_order=check_order)
        self._raise_errors(errors)

    def get_declarative_diff(
        self,
        actual: Dict[str, Any],
        expected: Union[Dict[str, Any], "BaseOperator"],
        strict_keys=True,
        check_order=True,
    ) -> list:
        return self.match(actual, expected, [], strict_keys=strict_keys, check_order=check_order)

    @staticmethod
    def _raise_errors(errors) -> None:
        if errors:
            raise AssertionError("\n" + "\n".join([str((".".join(i[0]), *i[1:])) for i in errors]))


class BaseOperator:
    pass


class Contains(Generic[T], Iterable, BaseOperator):
    def __init__(self, iterable: Union[Dict[str, T], List[T]], *, recursive=False, check_pairs=True):
        self.iterable = iterable
        self.recursive = recursive
        self.check_pairs = check_pairs

    def __iter__(self):  # pragma: no cover
        return iter(self.iterable)

    def match(self, actual, path, matcher: Matcher, *, strict_keys=True, **_) -> list[tuple[Sequence, str, Any, ANY]]:
        if is_same_type(actual, self.iterable, dict):
            errors = self._match_dict(actual, matcher, path, strict_keys)
        elif is_same_type(actual, self.iterable, list):
            errors = self._match_list(actual, matcher, path, strict_keys)
        else:
            errors = [(path, "Contains can only be used with dictionaries or lists", actual, self.iterable)]

        return errors

    def _match_dict(self, actual, matcher, path, strict_keys):
        errors = []
        for key, expected_value in self.iterable.items():
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
                            actual_value, expected_value, key_, strict_keys=strict_keys, check_order=False
                        )
        return errors

    def _match_list(self, actual, matcher, path, strict_keys):
        errors = []
        if len(actual) < len(self.iterable):
            errors.append((path, "List is too short", actual, self.iterable))
        else:
            for i, expected_item in enumerate(self.iterable):
                actual_copy = actual.copy()
                tmp_path = path + [str(i)]
                found = False
                for j, actual_item in enumerate(actual_copy):
                    if actual_item in self.iterable:
                        found = True
                        actual.pop(j)
                        break
                    elif isinstance(actual_item, (dict, list)):
                        if self.recursive and not isinstance(self.iterable, (Contains, DoesntContains)):
                            expected_item = Contains(expected_item, recursive=self.recursive)

                        if isinstance(expected_item, (Contains, DoesntContains)):
                            inner_errors = expected_item.match(actual_item, tmp_path, matcher)
                        else:
                            inner_errors = matcher.match(
                                actual_item, expected_item, tmp_path, strict_keys=strict_keys, check_order=False
                            )
                        if not inner_errors:
                            found = True
                            actual.pop(j)
                            break

                if found:
                    break
                else:
                    errors.append((tmp_path, "not_found", actual_item, expected_item))

        return errors

    def __repr__(self):  # pragma: no cover
        return f"<Contains: {repr(self.iterable)}>"

    def __eq__(self, other):
        match = self.match(other, [], Matcher())
        return len(match) == 0


class DoesntContains(Generic[T], Iterable, BaseOperator):
    def __init__(
        self,
        iterable: Union[Dict[str, T], List[T]],
    ):
        self.iterable = iterable

    def __iter__(self):  # pragma: no cover
        return iter(self.iterable)

    def match(self, actual, path, _: Matcher, **kwargs) -> list[tuple[Sequence, str, Any, ANY]]:
        errors: list[tuple[Sequence, str, Any, ANY]] = []
        if isinstance(actual, dict):
            for key, expected_value in cast(dict, self.iterable).items():
                actual_value = actual.get(key)
                # todo:
                #   if expected_value is not ANY:
                #       continue
                #   if not (expected_value is ANY_NOT_NONE and actual_value is not None):
                #       continue

                if actual_value == expected_value:
                    errors.append((path, f"should not contain {key}", actual_value, expected_value))

        elif isinstance(actual, list):
            for i, expected_item in enumerate(self.iterable):
                actual_item = actual[i]
                if isinstance(actual_item, dict):
                    if expected_item in actual:
                        errors.append(
                            (path + [str(i)], f"list should not contain {expected_item}", actual_item, expected_item)
                        )

                elif actual_item in self.iterable:
                    errors.append((path + [str(i)], f"list should not contain {expected_item}", actual, expected_item))

        return errors

    def __repr__(self):  # pragma: no cover
        return repr(self.iterable)
