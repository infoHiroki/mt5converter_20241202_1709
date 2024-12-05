import unittest
from datetime import datetime
from time_utils import round_time_to_nearest_15min

class TestTimeUtils(unittest.TestCase):
    def test_round_time_to_nearest_15min(self):
        # テストケース: 時刻と期待される丸め結果のペア
        test_cases = [
            # 15分未満のケース（近い方に丸める）
            (datetime(2023, 12, 1, 10, 7), datetime(2023, 12, 1, 10, 0)),  # 10:07 → 10:00
            (datetime(2023, 12, 1, 10, 8), datetime(2023, 12, 1, 10, 15)), # 10:08 → 10:15
            
            # 15分付近のケース
            (datetime(2023, 12, 1, 10, 14), datetime(2023, 12, 1, 10, 15)), # 10:14 → 10:15
            (datetime(2023, 12, 1, 10, 15), datetime(2023, 12, 1, 10, 15)), # 10:15 → 10:15
            (datetime(2023, 12, 1, 10, 16), datetime(2023, 12, 1, 10, 15)), # 10:16 → 10:15
            
            # 30分付近のケース
            (datetime(2023, 12, 1, 10, 29), datetime(2023, 12, 1, 10, 30)), # 10:29 → 10:30
            (datetime(2023, 12, 1, 10, 30), datetime(2023, 12, 1, 10, 30)), # 10:30 → 10:30
            (datetime(2023, 12, 1, 10, 31), datetime(2023, 12, 1, 10, 30)), # 10:31 → 10:30
            
            # 45分付近のケース
            (datetime(2023, 12, 1, 10, 44), datetime(2023, 12, 1, 10, 45)), # 10:44 → 10:45
            (datetime(2023, 12, 1, 10, 45), datetime(2023, 12, 1, 10, 45)), # 10:45 → 10:45
            (datetime(2023, 12, 1, 10, 46), datetime(2023, 12, 1, 10, 45)), # 10:46 → 10:45
            
            # 時間切り替わりのケース
            (datetime(2023, 12, 1, 10, 52), datetime(2023, 12, 1, 11, 0)),  # 10:52 → 11:00
            (datetime(2023, 12, 1, 10, 59), datetime(2023, 12, 1, 11, 0)),  # 10:59 → 11:00
            
            # 秒とマイクロ秒を含むケース
            (datetime(2023, 12, 1, 10, 7, 30), datetime(2023, 12, 1, 10, 0)),  # 10:07:30 → 10:00
            (datetime(2023, 12, 1, 10, 8, 45), datetime(2023, 12, 1, 10, 15)), # 10:08:45 → 10:15
        ]

        for input_time, expected_time in test_cases:
            with self.subTest(input_time=input_time):
                rounded_time = round_time_to_nearest_15min(input_time)
                self.assertEqual(rounded_time, expected_time)

if __name__ == '__main__':
    unittest.main()
