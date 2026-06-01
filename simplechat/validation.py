"""Input validation rules shared by the server and client."""

import re


MAX_NICKNAME_CHARS = 32
MAX_MESSAGE_CHARS = 2000

_NICKNAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_RESERVED_NICKNAMES = {"SERVER"}


def nickname_error(nickname):
    """Return an error string for an invalid nickname, otherwise None."""
    if not nickname:
        return "Nickname cannot be empty"
    if len(nickname) > MAX_NICKNAME_CHARS:
        return f"Nickname must be {MAX_NICKNAME_CHARS} characters or fewer"
    if not _NICKNAME_RE.fullmatch(nickname):
        return (
            "Nickname may contain only letters, numbers, underscores, and hyphens"
        )
    if nickname.upper() in _RESERVED_NICKNAMES:
        return "Nickname is reserved"
    return None


def message_error(message):
    """Return an error string for an invalid chat message, otherwise None."""
    if not message:
        return "Message cannot be empty"
    if len(message) > MAX_MESSAGE_CHARS:
        return f"Message must be {MAX_MESSAGE_CHARS} characters or fewer"
    return None
