import copy
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from benchmark import parse, select
from chart_data import merge

FIXTURE = pathlib.Path(__file__).parent / 'fixtures/rapidhash.txt'


class ProtocolTests(unittest.TestCase):
    def test_parse_real_output_uses_fixed_bulk(self):
        metrics = parse(FIXTURE.read_text())
        self.assertEqual(metrics, dict(bulk_bytes_per_cycle=10.66, bulk_gib_s=34.76, small_cycles=27.58))

    def test_partial_output_rejected(self):
        text = FIXTURE.read_text()
        for damaged in [text.split('Verification value')[0], text.replace('   1-byte keys', 'missing'), re.sub(r'Alignment\s+7', 'missing', text)]:
            with self.assertRaises(ValueError):
                parse(damaged)

    def test_xeon_independent_choices_and_gib_tie(self):
        runs = [dict(run=1, bulk_bytes_per_cycle=10, bulk_gib_s=32.60, small_cycles=20),
                dict(run=2, bulk_bytes_per_cycle=10, bulk_gib_s=32.61, small_cycles=22)]
        chosen = select(runs, 'Xeon8375C')
        self.assertEqual((chosen['bulk_selected_run'], chosen['small_selected_run']), (2, 1))
        runs[1]['bulk_gib_s'] = 32.60
        self.assertEqual(select(runs, 'Xeon8375C')['bulk_selected_run'], 1)

    def test_m2_independent_medians_retain_outlier(self):
        runs = [dict(run=1, bulk_bytes_per_cycle=30, bulk_gib_s=97.8, small_cycles=10),
                dict(run=2, bulk_bytes_per_cycle=10, bulk_gib_s=32.6, small_cycles=22),
                dict(run=3, bulk_bytes_per_cycle=11, bulk_gib_s=35.9, small_cycles=24)]
        chosen = select(runs, 'M2Pro')
        self.assertEqual((chosen['bulk_selected_run'], chosen['small_selected_run']), (3, 2))
        self.assertEqual(len(chosen['runs']), 3)
        self.assertTrue(chosen['variation']['bulk_bytes_per_cycle']['flag_over_15_percent'])

    def test_chart_merge_preserves_non_speed_data_and_other_host(self):
        old = {'heuristics': [{'id': 'test', 'claim': {'proof': 'untouched'}, 'speeds': {
            'smh_m2_bulk_Bpc': {'value': 12}, 'smh_xeon_bulk_Bpc': {'value': 9, 'verification': 'stale'},
            'm2_gbps_512': {'value': None}}}], 'benchmark': {'history': 'untouched'}}
        saved = copy.deepcopy(old)
        source = select([dict(run=i, bulk_bytes_per_cycle=10, bulk_gib_s=32.6, small_cycles=20) for i in [1, 2]], 'Xeon8375C')
        source.update(registered_name='test', binary_sha256='new', _record='speeds.json#/test/Xeon8375C', _file='speeds.json')
        manifest = [dict(group='heuristics', row_id='test', name='test', registered_names={'M2Pro': 'test', 'Xeon8375C': 'test'})]
        actual, count = merge(old, {'test': {'Xeon8375C': source}}, manifest)
        self.assertEqual(count, 2)
        self.assertEqual(old, saved)
        self.assertEqual(actual['benchmark'], old['benchmark'])
        self.assertEqual(actual['heuristics'][0]['claim'], old['heuristics'][0]['claim'])
        cells = actual['heuristics'][0]['speeds']
        self.assertEqual(cells['smh_m2_bulk_Bpc'], {'value': 12})
        self.assertEqual(cells['m2_gbps_512'], {'value': None})
        self.assertEqual(cells['smh_xeon_bulk_Bpc']['verification'], {'status': 'not-run'})


if __name__ == '__main__':
    unittest.main()
