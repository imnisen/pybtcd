import unittest
from wire.common import *
from chainhash import *

class TestElementWire(unittest.TestCase):
    pass

class TestElementWireErrors(unittest.TestCase):
    pass

class TestVarIntWire(unittest.TestCase):
    pass

class TestVarIntWireErrors(unittest.TestCase):
    pass

class TestVarIntNonCanonicat(unittest.TestCase):
    pass

class TestVarIntSerializeSize(unittest.TestCase):
    pass

class TestVarStringWire(unittest.TestCase):
    pass

class TestVarStringWireErrors(unittest.TestCase):
    pass

class TestVarStringOverflowErrors(unittest.TestCase):
    pass

class TestVarBytesWire(unittest.TestCase):
    pass

class TestVarBytesWireErrors(unittest.TestCase):
    pass

class TestVarBytesOverflowErrors(unittest.TestCase):
    pass

class TestRandomUint64(unittest.TestCase):
    pass

class TestRandomUint64Errors(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
