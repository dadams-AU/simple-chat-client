import unittest

from generate_cert import _subject_alt_names


class GenerateCertTests(unittest.TestCase):
    def test_subject_alt_names_include_defaults_and_extras(self):
        names = _subject_alt_names("chat.local", ["192.168.1.20", "DNS:chat"])

        self.assertIn("DNS:localhost", names)
        self.assertIn("IP:127.0.0.1", names)
        self.assertIn("IP:::1", names)
        self.assertIn("DNS:chat.local", names)
        self.assertIn("IP:192.168.1.20", names)
        self.assertIn("DNS:chat", names)

    def test_subject_alt_names_are_deduplicated(self):
        names = _subject_alt_names("localhost", ["DNS:localhost"])

        self.assertEqual(names.count("DNS:localhost"), 1)


if __name__ == "__main__":
    unittest.main()
