#!/usr/bin/env python3
"""
Backwards-compatibility shim.

The server has moved to the `simplechat` package.
Run directly with:  python server.py
Or after pip install: chat-server
"""
from simplechat.server import main

if __name__ == '__main__':
    main()
