import unittest
from eth_tool.common import logger

class TestLogger(unittest.TestCase):
    def test_token_info(self):
        ret = logger.log('logger', 'log')
        self.assertEqual(ret[1:4], ['test_logger:6 ', 'logger', 'log'])

    def test_color(self):
        for c in ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']:
            logger.log('logger', getattr(logger, c)(c))
            c1 = 'light_' + c
            logger.log('logger', getattr(logger, c1)(c1))
            c2 = 'on_' + c
            logger.log('logger', getattr(logger, c2)(c2))

    def test_style(self):
        for c in ['reset', 'bold', 'disable', 'underline', 'blink', 'reverse', 'invisible', 'strikethrough']:
            logger.log('logger', getattr(logger, c)(c))

if __name__ == '__main__':
    unittest.main()
