"""Small example module used in documentation and smoke tests."""


def normalize_name(name: str) -> str:
    """Normalize user-provided names."""

    return " ".join(name.strip().split()).title()


class GreetingService:
    """Create greetings for normalized names."""

    def greet(self, name: str) -> str:
        return f"Hello, {normalize_name(name)}!"
