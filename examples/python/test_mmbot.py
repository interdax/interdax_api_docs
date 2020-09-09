import unittest
import os


def bash_cmd(cmd='ls'):
    with os.popen(cmd) as do:
        output = do.read()
        return output


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
        r = bash_cmd(' '.join(self.test_args))
        print(r)
        self.assertIn('Test passed', r)


if __name__ == '__main__':
    unittest.main()
