import subprocess
import unittest
import os

test_args = ["python",
             "mmbot.py",
             "-as", os.environ['API_KEY_SECRET'],
             "-ak", os.environ['API_KEY_ID'],
             "-t"
             ]

if 'TEST' in os.environ.keys():
    print(os.environ['TEST'])
    if os.environ['TEST'] == 'true':
        test_args.append("-t")


class TestBot(unittest.TestCase):
    def test_something(self):
        r = subprocess.run(test_args)
        self.assertEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
