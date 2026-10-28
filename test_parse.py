import csv
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class ParserTests(unittest.TestCase):
    def run_case(self, rows, *args):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'input.csv'
            report = Path(tmp) / 'out.csv'
            fields = ['task_id', 'outcome', 'attempt_no', 'input_tokens',
                      'cached_tokens', 'output_tokens', 'tool_calls',
                      'duration_min', 'cost_usd', 'review_minutes']
            with source.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            result = subprocess.run([sys.executable, str(ROOT / 'parse.py'), str(source),
                                     '--out', str(report), *args], capture_output=True, text=True)
            return result, list(csv.DictReader(io.StringIO(report.read_text()))) if report.exists() else []

    def row(self, task, outcome, cost, review='2', duration='60'):
        return dict(task_id=task, outcome=outcome, attempt_no='1', input_tokens='100',
                    cached_tokens='50', output_tokens='10', tool_calls='1',
                    duration_min=duration, cost_usd=cost, review_minutes=review)

    def test_review_uses_only_measured_human_review_time(self):
        result, _ = self.run_case([self.row('a', 'success', '1', '2', '60')], '--review-rate', '60')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Review cost:      $2.0000', result.stdout)
        self.assertIn('Cost per successful task: $3.0000', result.stdout)

    def test_missing_review_time_rejects_cost_estimate(self):
        result, _ = self.run_case([self.row('a', 'success', '1', '')], '--review-rate', '60')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('review_minutes', result.stderr)

    def test_incomplete_cost_is_visible_in_percentages_and_csv(self):
        result, report = self.run_case([self.row('a', 'success', ''), self.row('b', 'fail', '2')])
        self.assertEqual(result.returncode, 0, result.stderr)
        for label in ('Failed attempts:', 'Retry tax:'):
            self.assertIn('PARTIAL', next(line for line in result.stdout.splitlines() if label in line))
        self.assertEqual(report[0]['cost_usd'], '')
        self.assertEqual(report[0]['cost_complete'], 'no')
        self.assertEqual(report[1]['cost_complete'], 'yes')

    def test_zero_success_remains_undefined(self):
        result, _ = self.run_case([self.row('a', 'fail', '1')])
        self.assertIn('undefined', result.stdout)


if __name__ == '__main__':
    unittest.main()
