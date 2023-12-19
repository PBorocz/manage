"""Common test utility stuff."""


class SimpleObj:
    """."""

    def __init__(self, **kwargs):
        """."""
        [setattr(self, attr, value) for (attr, value) in kwargs.items()]
