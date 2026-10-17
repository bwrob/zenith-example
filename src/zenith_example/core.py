"""Core functions for zenith-example."""


def get_greeting(name: str) -> str:
    """Return a personalized greeting message.

    Parameters
    ----------
    name : str
        The name of the entity to greet.

    Returns
    -------
    str
        The formatted greeting message.

    Examples
    --------
    >>> get_greeting("World")
    'Hello, World!'

    """
    clean_name = name.strip()
    if not clean_name:
        clean_name = "World"
    return f"Hello, {clean_name}!"
