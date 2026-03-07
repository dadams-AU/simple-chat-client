#!/usr/bin/env python3
"""
Generate a self-signed TLS certificate for the SimpleChat server.

Requires OpenSSL to be installed on the system.

Usage:
    python generate_cert.py [--cert cert.pem] [--key key.pem] [--days 365]

Outputs:
    cert.pem  — public certificate (safe to distribute to clients)
    key.pem   — private key (keep secret, never commit to version control)
"""

import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Generate a self-signed TLS certificate'
    )
    parser.add_argument('--cert', default='cert.pem',
                        help='Output certificate file (default: cert.pem)')
    parser.add_argument('--key', default='key.pem',
                        help='Output private key file (default: key.pem)')
    parser.add_argument('--days', type=int, default=365,
                        help='Certificate validity in days (default: 365)')
    parser.add_argument('--cn', default='simplechat',
                        help='Common name for the certificate (default: simplechat)')
    args = parser.parse_args()

    if os.path.exists(args.cert) or os.path.exists(args.key):
        answer = input(
            f"'{args.cert}' or '{args.key}' already exists. Overwrite? [y/N] "
        ).strip().lower()
        if answer != 'y':
            print('Skipped.')
            sys.exit(0)

    print(f'Generating self-signed certificate (valid {args.days} days)...')
    try:
        subprocess.run(
            [
                'openssl', 'req', '-x509',
                '-newkey', 'rsa:4096',
                '-keyout', args.key,
                '-out', args.cert,
                '-days', str(args.days),
                '-nodes',
                '-subj', f'/CN={args.cn}',
            ],
            check=True,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print('Error: openssl not found.')
        print('Install it with your system package manager:')
        print('  macOS:  brew install openssl')
        print('  Ubuntu: sudo apt install openssl')
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f'Certificate generation failed: {e}')
        sys.exit(1)

    print(f'\nCreated:')
    print(f'  {args.cert}  — share with clients if using --ca-cert')
    print(f'  {args.key}   — keep private, never commit to version control')


if __name__ == '__main__':
    main()
