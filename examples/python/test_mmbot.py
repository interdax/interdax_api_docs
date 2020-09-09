import unittest
import os
import subprocess

class TestBot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_args = ["python",
                     "mmbot.py",
                     "-as", os.environ['API_KEY_SECRET'],
                     "-ak", os.environ['API_KEY_ID'],
                     "-t",
                     "--market-maker"
                     ]
        if 'TEST' in os.environ.keys():
            print(os.environ['TEST'])
            if os.environ['TEST'] == 'true':
                cls.test_args.append("-t")

    def test_market_maker(self):
        r = subprocess.run(self.test_args)
        self.assertEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
