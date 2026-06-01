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
import ipaddress
import os
import subprocess
import sys


def _normalize_san(value):
    if value.upper().startswith("DNS:") or value.upper().startswith("IP:"):
        kind, name = value.split(":", 1)
        return f"{kind.upper()}:{name}"
    try:
        ipaddress.ip_address(value)
        return f"IP:{value}"
    except ValueError:
        return f"DNS:{value}"


def _subject_alt_names(cn, extra_sans):
    names = ["DNS:localhost", "IP:127.0.0.1", "IP:::1"]
    names.append(_normalize_san(cn))
    names.extend(_normalize_san(value) for value in extra_sans)

    seen = set()
    unique = []
    for name in names:
        if name not in seen:
            unique.append(name)
            seen.add(name)
    return unique


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
    parser.add_argument(
        '--cn',
        default='localhost',
        help='Common name for the certificate (default: localhost)',
    )
    parser.add_argument('--san', action='append', default=[],
                        help='Extra subjectAltName, such as 192.168.1.20')
    args = parser.parse_args()

    if os.path.exists(args.cert) or os.path.exists(args.key):
        answer = input(
            f"'{args.cert}' or '{args.key}' already exists. Overwrite? [y/N] "
        ).strip().lower()
        if answer != 'y':
            print('Skipped.')
            sys.exit(0)

    subject_alt_names = _subject_alt_names(args.cn, args.san)

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
                '-addext', f'subjectAltName = {",".join(subject_alt_names)}',
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print('Error: openssl not found.')
        print('Install it with your system package manager:')
        print('  macOS:  brew install openssl')
        print('  Ubuntu: sudo apt install openssl')
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f'Certificate generation failed: {e}')
        if e.stderr:
            print(e.stderr.strip())
        sys.exit(1)

    try:
        os.chmod(args.key, 0o600)
    except OSError:
        pass

    print(f'\nCreated:')
    print(f'  {args.cert}  — share with clients if using --ca-cert')
    print(f'  {args.key}   — keep private, never commit to version control')
    print(f'  SANs: {", ".join(subject_alt_names)}')


if __name__ == '__main__':
    main()
