#!/usr/bin/env python3
"""Fetch, validate and verify the hiking feed using only the standard library."""

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

SKOPJE = ZoneInfo('Europe/Skopje')


class SyncError(Exception):
    pass


class TransportError(SyncError):
    pass


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError()
        return parsed
    except (AttributeError, TypeError, ValueError):
        raise SyncError('generatedAt must be an ISO timestamp with a timezone') from None


def validate(payload, now=None):
    if not isinstance(payload, dict) or not isinstance(payload.get('hikes'), list):
        raise SyncError('response must be an object containing a hikes array')
    generated = timestamp(payload.get('generatedAt'))
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(SKOPJE).date().isoformat()
    if generated > now + timedelta(minutes=5):
        raise SyncError('generatedAt is in the future')
    if payload.get('today') != today or now - generated > timedelta(hours=48):
        raise SyncError('upstream snapshot is stale: expected today=' + today
                        + ' and generatedAt no more than 48 hours old; generatedAt=' + generated.isoformat()
                        + '. Check whether the daily digest was saved to hikes-clean.')
    hikes = payload['hikes']
    seen = set()
    upcoming = 0
    for hike in hikes:
        if not isinstance(hike, dict):
            raise SyncError('each hike must be an object')
        for key in ('id', 'club', 'date'):
            if not isinstance(hike.get(key), str) or not hike[key].strip():
                raise SyncError('hike is missing required text field: ' + key)
        try:
            if date.fromisoformat(hike['date']).isoformat() != hike['date']:
                raise ValueError()
        except ValueError:
            raise SyncError('hike date must be YYYY-MM-DD') from None
        identity = (hike['club'], hike['id'])
        if identity in seen:
            raise SyncError('duplicate hike identity in upstream snapshot')
        seen.add(identity)
        upcoming += hike['date'] >= today
        if 'past' in hike and (type(hike['past']) is not bool or hike['past'] != (hike['date'] < today)):
            raise SyncError('hike past flag disagrees with today')
    for key, expected in (('totalCount', len(hikes)), ('count', upcoming)):
        if type(payload.get(key)) is not int or payload[key] != expected:
            raise SyncError(key + ' disagrees with the hikes array')
    for key in ('filesRead', 'filesSkipped'):
        if key in payload and (type(payload[key]) is not int or payload[key] < 0):
            raise SyncError(key + ' must be a nonnegative integer')
    if payload.get('filesSkipped', 0) > 0:
        print(f'::warning::Upstream skipped {payload["filesSkipped"]} input files; continuing with available snapshot.')
    return generated


def fingerprint(payload):
    # servedAt changes on every request, even when the actual snapshot is identical.
    meaningful = {k: v for k, v in payload.items() if k != 'servedAt'}
    meaningful['hikes'] = sorted(payload['hikes'], key=lambda h: (h['club'], h['id']))
    return hashlib.sha256(json.dumps(meaningful, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def changed(candidate, previous, now=None):
    generated = validate(candidate, now)
    if previous is None:
        return True
    if generated < timestamp(previous.get('generatedAt')):
        raise SyncError('upstream snapshot is older than the committed snapshot')
    return fingerprint(candidate) != fingerprint(previous)


def request_url(url, refresh=False):
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.netloc:
        raise SyncError('endpoint URL is missing or invalid')
    params = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != '_' and (not refresh or k != 'refresh')]
    if refresh:
        params.append(('refresh', '1'))
    params.append(('_', str(time.time_ns())))
    return urlunsplit(parts._replace(query=urlencode(params), fragment=''))


def fetch_json(url, refresh=False):
    # Never print curl stderr: redirects or errors may expose the secret endpoint.
    try:
        result = subprocess.run([
            'curl', '--silent', '--show-error', '--location', '--fail',
            '--proto', '=http,https', '--proto-redir', '=http,https',
            '--connect-timeout', '15', '--max-time', '60', request_url(url, refresh),
        ], capture_output=True, timeout=65)
    except subprocess.TimeoutExpired:
        raise TransportError('request timed out') from None
    if result.returncode:
        raise TransportError('HTTP request failed (curl exit ' + str(result.returncode) + ')')
    try:
        return json.loads(result.stdout)
    except (ValueError, UnicodeError):
        raise TransportError('endpoint returned invalid JSON') from None


def retry(operation, attempts, delay):
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except TransportError as error:
            print(f'Attempt {attempt}/{attempts}: {error}', flush=True)
            if attempt == attempts:
                raise
            time.sleep(delay)


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        raise SyncError('cannot read valid JSON from ' + path.name) from None


def write_json(path, payload):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def download(url, previous_path, output_path, attempts=6, delay=30):
    previous = read_json(previous_path) if previous_path.exists() else None

    def attempt():
        candidate = fetch_json(url, refresh=True)
        changed(candidate, previous)
        return candidate

    candidate = retry(attempt, attempts, delay)
    write_json(output_path, candidate)
    print(f'Validated snapshot: {candidate["generatedAt"]}; hikes={len(candidate["hikes"])}; digest={fingerprint(candidate)}')


def apply(candidate_path, destination):
    candidate = read_json(candidate_path)
    previous = read_json(destination) if destination.exists() else None
    if changed(candidate, previous):
        write_json(destination, candidate)
        print('Updated hikes.json with validated content.')
    else:
        print('Snapshot unchanged (ignoring servedAt and hike order).')


def verify(url, expected_path, attempts=20, delay=15):
    expected = read_json(expected_path)
    expected_digest = fingerprint(expected)

    def attempt():
        published = fetch_json(url)
        validate(published)
        if fingerprint(published) != expected_digest:
            raise SyncError('public site does not yet match the committed snapshot')

    retry(attempt, attempts, delay)
    print('Verified public hikes.json: ' + expected_digest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    fetch = sub.add_parser('fetch')
    fetch.add_argument('--previous', type=Path, default=Path('hikes.json'))
    fetch.add_argument('--output', type=Path, required=True)
    update = sub.add_parser('apply')
    update.add_argument('--candidate', type=Path, required=True)
    update.add_argument('--destination', type=Path, default=Path('hikes.json'))
    check = sub.add_parser('verify')
    check.add_argument('--url', required=True)
    check.add_argument('--expected', type=Path, default=Path('hikes.json'))
    args = parser.parse_args()
    try:
        if args.command == 'fetch':
            url = os.environ.get('EXEC_URL', '')
            request_url(url)  # Fail immediately for a missing secret.
            download(url, args.previous, args.output)
        elif args.command == 'apply':
            apply(args.candidate, args.destination)
        else:
            verify(args.url, args.expected)
    except SyncError as error:
        print('Sync failed: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
