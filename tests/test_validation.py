import unittest

from simplechat.validation import (
    MAX_MESSAGE_CHARS,
    MAX_NICKNAME_CHARS,
    message_error,
    nickname_error,
)


class ValidationTests(unittest.TestCase):
    def test_valid_nickname(self):
        self.assertIsNone(nickname_error("Alice_123-test"))

    def test_invalid_nicknames(self):
        self.assertIsNotNone(nickname_error(""))
        self.assertIsNotNone(nickname_error("Alice Smith"))
        self.assertIsNotNone(nickname_error("Alice:"))
        self.assertIsNotNone(nickname_error("SERVER"))
        self.assertIsNotNone(nickname_error("a" * (MAX_NICKNAME_CHARS + 1)))

    def test_message_size_limit(self):
        self.assertIsNone(message_error("hello"))
        self.assertIsNotNone(message_error(""))
        self.assertIsNotNone(message_error("x" * (MAX_MESSAGE_CHARS + 1)))


if __name__ == "__main__":
    unittest.main()
