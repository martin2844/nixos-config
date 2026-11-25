import unittest

import holidays

from generate import generate


class HolidayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate()['dates']

    def regions(self, day):
        return {item['region'] for item in self.data.get(day, [])}

    def test_catalunya_holiday_dates_2026(self):
        days = {day[5:] for day, entries in self.data.items()
                if day.startswith('2026-') and any(e['region'] == 'cat' for e in entries)}
        self.assertEqual(days, {'01-01', '01-06', '04-03', '04-06', '05-01',
            '05-25', '06-24', '08-15', '09-11', '09-24', '10-12', '11-01',
            '12-06', '12-08', '12-25', '12-26'})

    def test_catalunya_holiday_dates_2027_and_local_dates(self):
        days = {day[5:] for day, entries in self.data.items()
                if day.startswith('2027-') and any(e['region'] == 'cat' for e in entries)}
        self.assertEqual(days, {'01-01', '01-06', '03-26', '03-29', '05-01',
            '05-17', '06-24', '08-15', '09-11', '09-24', '10-12', '11-01',
            '12-06', '12-08', '12-25'})

    def test_catalunya_includes_spain_national_holidays(self):
        # python-holidays models Spain/CT as the national calendar plus the
        # Catalan regional days. Guard against accidentally dropping the
        # national set when the subdivision or package version changes.
        for year in range(2020, 2041):
            national = holidays.country_holidays("ES", years=year, observed=False)
            catalunya = {day for day, entries in self.data.items()
                         if day.startswith(f"{year}-")
                         and any(e['region'] == 'cat' for e in entries)}
            missing = sorted(str(day) for day in national if str(day) not in catalunya)
            self.assertEqual(missing, [], f"missing Spanish national holidays for {year}")

    def test_sunday_national_holidays_are_kept(self):
        # 1 November and 6 December 2026 fall on Sunday. They are still
        # national holidays even though no Monday substitute applies in
        # Catalonia.
        self.assertIn('cat', self.regions('2026-11-01'))
        self.assertIn('cat', self.regions('2026-12-06'))
        self.assertNotIn('cat', self.regions('2026-12-07'))

    def test_overlapping_holidays_are_not_overwritten(self):
        self.assertEqual(self.regions('2026-05-25'), {'cat', 'ar', 'us'})
        self.assertEqual(self.regions('2026-12-25'), {'cat', 'ar', 'us'})

    def test_us_observed_date_and_actual_date(self):
        self.assertIn('us', self.regions('2026-07-03'))
        self.assertIn('us', self.regions('2026-07-04'))
        self.assertTrue(any('observed' in x['name'] for x in self.data['2026-07-03']))

    def test_argentina_transfer_and_optional_days(self):
        self.assertIn('ar', self.regions('2026-11-23'))
        self.assertNotIn('ar', self.regions('2026-11-20'))
        for day in ['2026-03-23', '2026-07-10', '2026-12-07']:
            self.assertTrue(any('optional' in x['name'] for x in self.data[day]))

    def test_no_invented_barcelona_future_dates(self):
        self.assertFalse(any('Barcelona:' in entry['name']
            for day, entries in self.data.items() if day.startswith('2028-') for entry in entries))

if __name__ == '__main__':
    unittest.main()
