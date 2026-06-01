import struct
import unittest

from simplechat.protocol import FrameTooLarge, MAX_FRAME_BYTES, recv_frame, send_frame


class FakeSocket:
    def __init__(self, recv_chunks=None):
        self.recv_chunks = list(recv_chunks or [])
        self.sent = bytearray()

    def sendall(self, data):
        self.sent.extend(data)

    def recv(self, size):
        if not self.recv_chunks:
            return b""
        chunk = self.recv_chunks.pop(0)
        if len(chunk) > size:
            self.recv_chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk


class ProtocolTests(unittest.TestCase):
    def test_round_trip_text_frame(self):
        sender = FakeSocket()

        send_frame(sender, "hello")

        receiver = FakeSocket([bytes(sender.sent)])
        self.assertEqual(recv_frame(receiver), "hello")

    def test_multiple_frames_stay_separate(self):
        sender = FakeSocket()

        send_frame(sender, "one")
        send_frame(sender, "two")

        receiver = FakeSocket([bytes(sender.sent)])
        self.assertEqual(recv_frame(receiver), "one")
        self.assertEqual(recv_frame(receiver), "two")

    def test_split_frame_is_reassembled(self):
        payload = "split message".encode("utf-8")
        header = struct.pack("!I", len(payload))
        receiver = FakeSocket([
            header[:2],
            header[2:],
            payload[:3],
            payload[3:],
        ])

        self.assertEqual(recv_frame(receiver), "split message")

    def test_clean_eof_before_header_returns_none(self):
        receiver = FakeSocket()

        self.assertIsNone(recv_frame(receiver))

    def test_oversized_frame_is_rejected(self):
        receiver = FakeSocket([struct.pack("!I", MAX_FRAME_BYTES + 1)])

        with self.assertRaises(FrameTooLarge):
            recv_frame(receiver)


if __name__ == "__main__":
    unittest.main()
