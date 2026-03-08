#!/usr/bin/env python3
"""
Backwards-compatibility shim.

The client has moved to the `simplechat` package.
Run directly with:  python chat.py
Or after pip install: chat-client
"""
from simplechat.client import main

if __name__ == '__main__':
    main()
