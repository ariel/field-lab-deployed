"""Exercise card selection without touching real volumes or OffShoot."""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'deploy'))
import ingest_cards


class IngestCardsTests(unittest.TestCase):
    def setUp(self):
        self.config = {'volume_mount': '/Volumes/T7', 'volume_uuid': 'target-uuid'}
        self.card = Path('/Volumes/Card')
        self.second = Path('/Volumes/Card 1')

    def record(self, path, identity='card-uuid'):
        return f'{path}\t{identity}\tdisk9s1'

    def test_only_a_mounted_removable_volume_with_a_distinct_uuid_is_eligible(self):
        info = {
            'MountPoint': str(self.card),
            'VolumeUUID': 'card-uuid',
            'DeviceIdentifier': 'disk9s1',
            'RemovableMedia': True,
        }
        self.assertEqual(ingest_cards.candidate(self.card, self.config, lambda _: info), self.record(self.card))
        for override in (
            {'MountPoint': None},
            {'VolumeUUID': 'TARGET-UUID'},
            {'OSInternalMedia': True},
            {'BusProtocol': 'Disk Image'},
            {'VirtualOrPhysical': 'Virtual'},
        ):
            with self.subTest(override=override):
                self.assertIsNone(ingest_cards.candidate(self.card, self.config, lambda _: {**info, **override}))
        inspect = Mock()
        self.assertIsNone(ingest_cards.candidate(Path('/Volumes/T7'), self.config, inspect))
        inspect.assert_not_called()

    def test_timed_out_volume_is_skipped(self):
        inspect = Mock(side_effect=subprocess.TimeoutExpired('diskutil', 5))
        self.assertIsNone(ingest_cards.candidate(self.card, self.config, inspect))

    def test_rechecks_selected_identities_and_sends_one_batch(self):
        api = Mock()
        missing = Path('/Volumes/Removed')
        skipped = ingest_cards.add_sources(
            [self.record(p) for p in (self.card, missing, self.second, self.card)],
            self.config, api,
            inspect_candidate=lambda path, _: self.record(path) if path != missing else None,
        )
        self.assertEqual(skipped, [str(missing)])
        api.assert_called_once_with('setSource', paths=[str(self.card), str(self.second)])

    def test_replacement_at_same_mount_path_leaves_offshoot_unchanged(self):
        api = Mock()
        skipped = ingest_cards.add_sources(
            [self.record(self.card)], self.config, api,
            inspect_candidate=lambda path, _: self.record(path, 'replacement'),
        )
        self.assertEqual(skipped, [str(self.card)])
        api.assert_not_called()

    def test_offshoot_failure_is_reported_without_retrying(self):
        api = Mock(side_effect=RuntimeError('OffShoot rejected setSource'))
        with self.assertRaisesRegex(RuntimeError, 'rejected setSource'):
            ingest_cards.add_sources(
                [self.record(self.card)], self.config, api,
                inspect_candidate=lambda path, _: self.record(path),
            )
        api.assert_called_once()
