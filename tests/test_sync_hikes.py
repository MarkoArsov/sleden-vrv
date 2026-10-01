import copy
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import sync_hikes as sync

NOW = datetime(2026, 9, 26, 10, tzinfo=timezone.utc)


def payload():
    return {
        'generatedAt': '2026-09-26T07:00:00Z', 'today': '2026-09-26',
        'servedAt': '2026-09-26T09:00:00Z', 'count': 1, 'totalCount': 1,
        'filesRead': 30, 'filesSkipped': 0,
        'hikes': [{'id': 'post1', 'club': 'pskh2o', 'date': '2026-09-27',
                   'destination': 'Дупнат Камен', 'past': False}],
    }


class ValidationTests(unittest.TestCase):
    def test_valid_snapshot(self):
        self.assertEqual(sync.validate(payload(), NOW).hour, 7)

    def test_snapshot_older_than_48_hours_is_stale(self):
        data = payload()
        data['generatedAt'] = '2026-09-24T09:59:59Z'
        with self.assertRaisesRegex(sync.SyncError, 'daily digest was saved to hikes-clean'):
            sync.validate(data, NOW)

    def test_snapshot_exactly_48_hours_old_is_valid(self):
        data = payload()
        data['generatedAt'] = '2026-09-24T10:00:00Z'
        sync.validate(data, NOW)

    def test_today_must_match_skopje_date(self):
        data = payload()
        data['today'] = '2026-09-25'
        with self.assertRaisesRegex(sync.SyncError, 'stale'):
            sync.validate(data, NOW)

    def test_bad_timestamps(self):
        for value in (None, 1, '', 'nonsense', '2026-09-26T07:00:00', '2026-09-26T11:00:00Z'):
            with self.subTest(value=value), self.assertRaises(sync.SyncError):
                sync.validate({**payload(), 'generatedAt': value}, NOW)

    def test_skopje_midnight(self):
        data = payload()
        data['generatedAt'] = '2026-09-25T22:30:00Z'
        sync.validate(data, datetime(2026, 9, 25, 23, tzinfo=timezone.utc))

    def test_incomplete_or_malformed_snapshot(self):
        cases = [[], {'hikes': None}, {**payload(), 'totalCount': 2},
                 {**payload(), 'count': True},
                 {**payload(), 'hikes': [None]}, {**payload(), 'filesRead': -1}]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(sync.SyncError):
                sync.validate(data, NOW)

    def test_invalid_hike_and_duplicate(self):
        for field, value in (('id', ''), ('club', None), ('date', ''),
                             ('date', '2026-02-30'), ('past', True)):
            data = payload()
            data['hikes'][0][field] = value
            with self.subTest(field=field), self.assertRaises(sync.SyncError):
                sync.validate(data, NOW)
        data = payload()
        data['hikes'] *= 2
        data.update(count=2, totalCount=2)
        with self.assertRaisesRegex(sync.SyncError, 'duplicate'):
            sync.validate(data, NOW)

    def test_optional_text_fields_may_be_null(self):
        data = payload()
        data['hikes'][0].update(destination=None, meetingPlace=None, notes=None)
        sync.validate(data, NOW)

    def test_skipped_files_emit_warning_and_remain_valid(self):
        data = {**payload(), 'filesSkipped': 2}
        output = io.StringIO()
        with redirect_stdout(output):
            sync.validate(data, NOW)
        self.assertIn('::warning::', output.getvalue())
        self.assertIn('2', output.getvalue())

    def test_empty_feed_is_valid(self):
        data = {**payload(), 'count': 0, 'totalCount': 0, 'hikes': []}
        sync.validate(data, NOW)

    def test_same_timestamp_changed_content_is_not_lost(self):
        previous = payload()
        candidate = copy.deepcopy(previous)
        candidate['hikes'][0]['destination'] = 'Updated destination'
        self.assertTrue(sync.changed(candidate, previous, NOW))

    def test_served_time_and_array_order_do_not_cause_commit(self):
        previous = payload()
        previous['hikes'].append({**previous['hikes'][0], 'id': 'post2'})
        previous.update(count=2, totalCount=2)
        candidate = copy.deepcopy(previous)
        candidate['servedAt'] = '2026-09-26T10:00:00Z'
        candidate['hikes'].reverse()
        self.assertFalse(sync.changed(candidate, previous, NOW))

    def test_reject_rollback(self):
        previous = {**payload(), 'generatedAt': '2026-09-26T08:00:00Z'}
        with self.assertRaisesRegex(sync.SyncError, 'older'):
            sync.changed(payload(), previous, NOW)


class IOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = Path(self.temp.name) / 'hikes.json'
        self.output = Path(self.temp.name) / 'candidate.json'
        self.previous.write_text(json.dumps(payload()))
        real_validate = sync.validate
        self.validation = patch.object(sync, 'validate', side_effect=lambda d, now=None: real_validate(d, NOW))
        self.validation.start()
        self.addCleanup(self.validation.stop)
        self.sleep = patch.object(sync.time, 'sleep').start()
        self.addCleanup(patch.stopall)

    def test_transport_failure_is_retried(self):
        with patch.object(sync, 'fetch_json', side_effect=[sync.TransportError('HTTP failed'), payload()]) as fetch:
            sync.download('https://example.test', self.previous, self.output, attempts=3)
        self.assertEqual(fetch.call_count, 2)
        self.sleep.assert_called_once()
        self.assertEqual(json.loads(self.output.read_text()), payload())

    def test_stale_validation_failure_is_not_retried(self):
        stale = {**payload(), 'generatedAt': '2026-09-24T09:59:59Z'}
        with patch.object(sync, 'fetch_json', return_value=stale) as fetch:
            with self.assertRaisesRegex(sync.SyncError, 'stale'):
                sync.download('https://example.test', self.previous, self.output, attempts=3)
        self.assertEqual(fetch.call_count, 1)
        self.sleep.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_malformed_validation_failure_is_not_retried(self):
        malformed = {**payload(), 'totalCount': 2}
        with patch.object(sync, 'fetch_json', return_value=malformed) as fetch:
            with self.assertRaisesRegex(sync.SyncError, 'totalCount'):
                sync.download('https://example.test', self.previous, self.output, attempts=3)
        self.assertEqual(fetch.call_count, 1)
        self.sleep.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_transport_exhaustion_preserves_last_valid_data_and_no_candidate(self):
        original = self.previous.read_bytes()
        with patch.object(sync, 'fetch_json', side_effect=sync.TransportError('HTTP failed')):
            with self.assertRaises(sync.SyncError):
                sync.download('https://example.test', self.previous, self.output, attempts=2)
        self.assertEqual(self.previous.read_bytes(), original)
        self.assertFalse(self.output.exists())

    def test_apply_checks_updated_main_before_writing(self):
        self.output.write_text(json.dumps(payload()))
        self.previous.write_text(json.dumps({**payload(), 'generatedAt': '2026-09-26T08:00:00Z'}))
        original = self.previous.read_bytes()
        with self.assertRaises(sync.SyncError):
            sync.apply(self.output, self.previous)
        self.assertEqual(self.previous.read_bytes(), original)

    def test_unchanged_apply_preserves_bytes(self):
        self.output.write_text(json.dumps({**payload(), 'servedAt': 'different'}))
        original = self.previous.read_bytes()
        sync.apply(self.output, self.previous)
        self.assertEqual(self.previous.read_bytes(), original)

    def test_changed_apply_writes_complete_snapshot(self):
        data = payload()
        data['hikes'][0]['destination'] = 'Corrected'
        self.output.write_text(json.dumps(data))
        sync.apply(self.output, self.previous)
        self.assertEqual(json.loads(self.previous.read_text()), data)

    def test_publication_mismatch_is_not_retried(self):
        old = payload()
        old['hikes'][0]['destination'] = 'Stale content'
        with patch.object(sync, 'fetch_json', return_value=old) as fetch:
            with self.assertRaisesRegex(sync.SyncError, 'does not yet match'):
                sync.verify('https://example.test', self.previous, attempts=2)
        self.assertEqual(fetch.call_count, 1)
        self.sleep.assert_not_called()

    def test_publication_retries_transport_failure(self):
        with patch.object(sync, 'fetch_json', side_effect=[sync.TransportError('HTTP failed'), payload()]) as fetch:
            sync.verify('https://example.test', self.previous, attempts=2)
        self.assertEqual(fetch.call_count, 2)
        self.sleep.assert_called_once()

    def test_publication_never_matches(self):
        with patch.object(sync, 'fetch_json', return_value={**payload(), 'generatedAt': '2026-09-26T06:00:00Z'}) as fetch:
            with self.assertRaisesRegex(sync.SyncError, 'does not yet match'):
                sync.verify('https://example.test', self.previous, attempts=2)
        self.assertEqual(fetch.call_count, 1)


class TransportTests(unittest.TestCase):
    def test_query_preserves_existing_parameters(self):
        with patch.object(sync.time, 'time_ns', return_value=123):
            result = sync.request_url('https://example.test/exec?token=abc&refresh=0&_=old', True)
        self.assertEqual(result, 'https://example.test/exec?token=abc&refresh=1&_=123')

    def test_errors_do_not_leak_endpoint_or_response(self):
        secret = 'https://example.test/secret-token'
        with patch.object(sync.subprocess, 'run', return_value=subprocess.CompletedProcess([], 22, b'', secret.encode())):
            with self.assertRaises(sync.TransportError) as error:
                sync.fetch_json(secret)
        self.assertNotIn(secret, str(error.exception))

    def test_html_http_success_and_timeout(self):
        with patch.object(sync.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'<html>error</html>', b'')):
            with self.assertRaisesRegex(sync.TransportError, 'invalid JSON'):
                sync.fetch_json('https://example.test')
        with patch.object(sync.subprocess, 'run', side_effect=subprocess.TimeoutExpired('curl', 65)):
            with self.assertRaisesRegex(sync.TransportError, 'timed out'):
                sync.fetch_json('https://example.test')


if __name__ == '__main__':
    unittest.main()
