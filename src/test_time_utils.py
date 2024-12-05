import unittest
from datetime import datetime
from time_utils import round_time_to_nearest_15min

class TestTimeUtils(unittest.TestCase):
    def test_round_time_to_nearest_15min(self):
        # テストケース: 時刻と期待される丸め結果のペア
        test_cases = [
            # 切り捨てのケース
            (datetime(2023, 12, 1, 10, 7), datetime(2023, 12, 1, 10, 0)),
            # 切り上げのケース
            (datetime(2023, 12, 1, 10, 8), datetime(2023, 12, 1, 10, 15)),
            # 15分ちょうどのケース
            (datetime(2023, 12, 1, 10, 15), datetime(2023, 12, 1, 10, 15)),
            # 30分のケース
            (datetime(2023, 12, 1, 10, 30), datetime(2023, 12, 1, 10, 30)),
            # 45分のケース
            (datetime(2023, 12, 1, 10, 45), datetime(2023, 12, 1, 10, 45)),
            # 時間切り替わりのケース
            (datetime(2023, 12, 1, 10, 52), datetime(2023, 12, 1, 11, 0)),
        ]

        for input_time, expected_time in test_cases:
            with self.subTest(input_time=input_time):
                rounded_time = round_time_to_nearest_15min(input_time)
                self.assertEqual(rounded_time, expected_time)

if __name__ == '__main__':
    unittest.main()
