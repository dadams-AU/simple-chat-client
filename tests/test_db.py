import os
import tempfile
import threading
import unittest

from simplechat.db import (
    authenticate_user,
    get_recent_messages,
    init_db,
    register_user,
    save_message,
    user_exists,
)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tempdir.name, "chat.db")
        self.db = init_db(self.db_path)

    def tearDown(self):
        self.db.close()
        self.tempdir.cleanup()

    def test_register_and_authenticate_user(self):
        self.assertFalse(user_exists(self.db, "Alice"))
        self.assertTrue(register_user(self.db, "Alice", "secret"))

        self.assertTrue(user_exists(self.db, "Alice"))
        self.assertTrue(authenticate_user(self.db, "Alice", "secret"))
        self.assertFalse(authenticate_user(self.db, "Alice", "wrong"))
        self.assertFalse(register_user(self.db, "Alice", "new-secret"))

    def test_recent_messages_are_oldest_first_with_limit(self):
        for index in range(5):
            save_message(self.db, "Alice", f"message {index}")

        rows = get_recent_messages(self.db, limit=3)

        self.assertEqual([row[1] for row in rows], [
            "message 2",
            "message 3",
            "message 4",
        ])

    def test_concurrent_message_writes(self):
        def write_messages(worker):
            for index in range(20):
                save_message(self.db, f"user-{worker}", f"{worker}:{index}")

        threads = [
            threading.Thread(target=write_messages, args=(worker,))
            for worker in range(5)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(get_recent_messages(self.db, limit=200)), 100)


if __name__ == "__main__":
    unittest.main()
