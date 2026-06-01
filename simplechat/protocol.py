"""Length-prefixed text framing for SimpleChat sockets."""

import struct


HEADER_SIZE = 4
MAX_FRAME_BYTES = 64 * 1024


class ProtocolError(Exception):
    """Raised when a peer sends malformed protocol data."""


class FrameTooLarge(ProtocolError):
    """Raised when a peer sends a frame larger than the configured limit."""


def _recv_exactly(sock, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            if chunks:
                raise ProtocolError("connection closed mid-frame")
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_frame(sock, message):
    """Send one UTF-8 text frame."""
    payload = message.encode("utf-8")
    if len(payload) > MAX_FRAME_BYTES:
        raise FrameTooLarge(
            f"frame is {len(payload)} bytes; limit is {MAX_FRAME_BYTES}"
        )
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def recv_frame(sock):
    """Receive one UTF-8 text frame, or None on clean EOF before a frame."""
    header = _recv_exactly(sock, HEADER_SIZE)
    if header is None:
        return None

    (length,) = struct.unpack("!I", header)
    if length > MAX_FRAME_BYTES:
        raise FrameTooLarge(
            f"frame is {length} bytes; limit is {MAX_FRAME_BYTES}"
        )

    payload = _recv_exactly(sock, length)
    if payload is None:
        raise ProtocolError("connection closed mid-frame")

    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProtocolError("frame payload is not valid UTF-8") from exc
