import copy
import unittest

from vlmrca.log_calendar import calendar_free_log_row


def row(template, values, omitted=0):
    return {'template': template, 'template_id': 'LT03', 'entity_id': '222', 'relative_bin': 4,
                'count': 23, 'level': 'error', 'template_full_sha256': 'source-template-identity',
                'numeric_preview': {k: {'first': v, 'last': v, 'sample_count': 23}
                                 for k, v in values.items()}, 'omitted_numeric_variables': omitted}


class CalendarProjectionTest(unittest.TestCase):
    def test_embedded_iso_keeps_status_and_latency(self):
        template = 'time="{num1}-{num2}-26T19:{num3}:{num4}.709Z" status={num5} latency={num6}ms'
        original = row(template, {'{num1}': '2025', '{num5}': '504', '{num6}': '1200'}, 3)
        frozen = copy.deepcopy(original)
        clean = calendar_free_log_row(original, template)
        self.assertEqual(clean['template'], 'time="" status={num5} latency={num6}ms')
        self.assertEqual(set(clean['numeric_preview']), {'{num5}', '{num6}'})
        self.assertEqual(clean['omitted_numeric_variables'], 0)
        self.assertEqual(original, frozen)

    def test_hidden_date_does_not_leak_through_preview(self):
        full = 'request completed ' + 'x' * 160 + ' time="{num1}-{num2}-26T19:{num3}:{num4}.709Z"'
        display = full[:130] + ' … [sha256=0123456789ab]'
        original = row(display, {'{num1}': '2025', '{num2}': '06', '{num3}': '59'}, 1)
        clean = calendar_free_log_row(original, full)
        self.assertEqual(clean['template'], display)
        self.assertEqual(clean['numeric_preview'], {})
        self.assertEqual(clean['omitted_numeric_variables'], 0)

    def test_redis_month_date_leaves_memory_measurements(self):
        template = '{num1}:C {num2} Jun {num3} {num4}:{num5}:{num6} * Fork CoW current {num7} MB'
        clean = calendar_free_log_row(row(template, {'{num1}': '7093', '{num2}': '09', '{num3}': '2025'}, 4), template)
        self.assertEqual(clean['template'], '{num1}:C * Fork CoW current {num7} MB')
        self.assertEqual(set(clean['numeric_preview']), {'{num1}'})
        self.assertEqual(clean['omitted_numeric_variables'], 1)

    def test_version_triples_and_year_valued_counts_are_not_dates(self):
        for template in ('version {num1}-{num2}-{num3} failed', 'status={num1} latency=2025ms', 'count 2025'):
            original = row(template, {'{num1}': '3', '{num2}': '2', '{num3}': '1'})
            self.assertIs(calendar_free_log_row(original, template), original)

    def test_relative_bins_units_count_and_identity_unchanged(self):
        template = '2025-06-26T19:59:10Z timeout 504 after 1200ms'
        original = row(template, {})
        clean = calendar_free_log_row(original, template)
        self.assertEqual(clean['template'], 'timeout 504 after 1200ms')
        for field in ('template_id', 'entity_id', 'relative_bin', 'count', 'level', 'template_full_sha256'):
            self.assertEqual(clean[field], original[field])

    def test_date_crosses_display_cutoff(self):
        full = 'save 09 Jun 2025 19:59:10 size=200MB'
        display = full[:12] + ' … [sha256=0123456789ab]'
        clean = calendar_free_log_row(row(display, {}), full)
        self.assertEqual(clean['template'], 'save … [sha256=0123456789ab]')

    def test_full_template_mismatch_fails(self):
        with self.assertRaises(ValueError):
            calendar_free_log_row(row('wrong source', {}), '2025-06-26T19:59:10Z actual source')

    def test_explicit_calendar_components(self):
        template = '[today date][y: {num1}][m:{num2}][d: {num3}]'
        clean = calendar_free_log_row(row(template, {'{num1}': '2025', '{num2}': '6', '{num3}': '23'}), template)
        self.assertEqual(clean['template'], '[today date]')
        self.assertEqual(clean['numeric_preview'], {})

    def test_java_date_keeps_duration_not_calendar(self):
        template = 'duration:{num1} time: Sat Jul {num2} {num3}:{num4}:{num5} HKT {num6}'
        clean = calendar_free_log_row(row(template, {'{num1}': '60', '{num2}': '18', '{num3}': '00'}, 3), template)
        self.assertEqual(clean['template'], 'duration:{num1} time:')
        self.assertEqual(set(clean['numeric_preview']), {'{num1}'})
        self.assertEqual(clean['omitted_numeric_variables'], 0)


if __name__ == '__main__':
    unittest.main()
