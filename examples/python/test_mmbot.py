import unittest
import os

test_args = ["python",
             "mmbot.py",
             "-as", os.environ['API_KEY_SECRET'],
             "-ak", os.environ['API_KEY_ID'],
             "-t",
             "--market-maker"
             ]

if 'TEST' in os.environ.keys():
    print(os.environ['TEST'])
    if os.environ['TEST'] == 'true':
        test_args.append("-t")

def bash_cmd(cmd='ls'):
    with os.popen(cmd) as do:
        output = do.read()
        return output

class TestBot(unittest.TestCase):
    def test_market_maker(self):
        r = bash_cmd(' '.join(test_args))
        self.assertIn('Test passed', r)


if __name__ == '__main__':
    unittest.main()
