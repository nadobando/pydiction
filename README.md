# Pydiction: Deep Comparison and Assertion Library

Pydiction is a Python library for deep comparisons and assertions on complex data structures. It provides a flexible and customizable way to compare dictionaries and lists while supporting various comparison scenarios, including nested comparisons and negative tests.

## Getting Started

These instructions will help you get started with using Pydiction for comparing data structures in your Python projects.

### Prerequisites

Pydiction has the following prerequisites:

- Python 3.x

### Installation

You can install Pydiction using `pip`:

```shell
pip install pydiction
```

### Usage
#### Simple Usage
Here's a basic example of how to use Pydiction for deep comparisons:

```python
from pydiction import Matcher, Contains

# Create a Matcher instance
matcher = Matcher()

# Define your actual and expected data structures
actual = {"a": 1, "b": 2}
expected = Contains({"a": 1})

# Perform the comparison and handle errors
try:
    matcher.assert_declarative_object(actual, expected)
except AssertionError as e:
    print(f"AssertionError: {e}")

```
#### Advanced
```python
from pydiction import ANY_NOT_NONE, Matcher,ANY,Contains,DoesntContains

matcher = Matcher()
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
    "comments": [{ "text": "Great post!"}],
    "likes": [
        {

            "title": "First Post",
            "content": "This is my first post!",

        },
        { "text": "Great post!"},
    ],
}

expected = {
    "name": "John",
    "age": ANY_NOT_NONE,
    "comments": DoesntContains([{"text": "not existing post!"}]),
    "email": ANY,
    "friends": [
        {
            "age": ANY_NOT_NONE,
            "email": ANY_NOT_NONE,
            "name": "Alice",

        }
    ],
    "likes": Contains(
        [
            {

                "content": "This is my first post!",
                "title": "First Post",

            },
        ]
    ),

}

matcher.assert_declarative_object(actual, expected)
```

### Contributing
If you'd like to contribute to Pydiction or report issues, please follow these guidelines:

1. Fork the repository on GitHub.
2. Clone your forked repository to your local machine.
3. Create a new branch for your feature or bug fix.
4. Make your changes and commit them with clear and concise commit messages.
5. Push your changes to your forked repository.
6. Create a pull request against the main repository.
