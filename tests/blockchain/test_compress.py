import unittest
from blockchain.compress import *


# hexToBytes converts the passed hex string into bytes and will panic if there
# is an error.  This is only provided for the hard-coded constants so errors in
# the source code can be detected. It will only (and must only) be called with
# hard-coded values.

def hex_to_bytes(s):
    return bytes.fromhex(s)


# TestVLQ ensures the variable length quantity serialization, deserialization,
# and size calculation works as expected.
class TestVLQ(unittest.TestCase):
    def setUp(self):
        self.tests = [
            {"value": 0, "serialized": hex_to_bytes("00")},
            {"value": 1, "serialized": hex_to_bytes("01")},
            {"value": 127, "serialized": hex_to_bytes("7f")},
            {"value": 128, "serialized": hex_to_bytes("8000")},
            {"value": 129, "serialized": hex_to_bytes("8001")},
            {"value": 255, "serialized": hex_to_bytes("807f")},
            {"value": 256, "serialized": hex_to_bytes("8100")},
            {"value": 16383, "serialized": hex_to_bytes("fe7f")},
            {"value": 16384, "serialized": hex_to_bytes("ff00")},
            {"value": 16511, "serialized": hex_to_bytes("ff7f")},  # Max 2-byte value
            {"value": 16512, "serialized": hex_to_bytes("808000")},
            {"value": 16513, "serialized": hex_to_bytes("808001")},
            {"value": 16639, "serialized": hex_to_bytes("80807f")},
            {"value": 32895, "serialized": hex_to_bytes("80ff7f")},
            {"value": 2113663, "serialized": hex_to_bytes("ffff7f")},  # Max 3-byte value
            {"value": 2113664, "serialized": hex_to_bytes("80808000")},
            {"value": 270549119, "serialized": hex_to_bytes("ffffff7f")},  # Max 4-byte value
            {"value": 270549120, "serialized": hex_to_bytes("8080808000")},
            {"value": 2147483647, "serialized": hex_to_bytes("86fefefe7f")},
            {"value": 2147483648, "serialized": hex_to_bytes("86fefeff00")},
            {"value": 4294967295, "serialized": hex_to_bytes("8efefefe7f")},  # Max uint32, 5 bytes
            # Max uint64, 10 bytes
            {"value": 18446744073709551615, "serialized": hex_to_bytes("80fefefefefefefefe7f")},
        ]

    def test_serialize_size_vlq(self):
        # Ensure the function to calculate the serialized size without
        # actually serializing the value is calculated properly.
        for test in self.tests:
            got_size = serialize_size_vlq(test['value'])
            self.assertEqual(got_size, len(test['serialized']))

    def test_put_vlq(self):
        for test in self.tests:
            got_size = serialize_size_vlq(test['value'])
            got_bytes = bytearray(got_size)
            got_bytes_written = put_vlq(got_bytes, test['value'])
            self.assertEqual(got_bytes, test['serialized'])
            self.assertEqual(got_bytes_written, len(test['serialized']))

    def test_deserialize_vlq(self):
        for test in self.tests:
            got_val, got_bytes_read = deserialize_vlq(test['serialized'])
            self.assertEqual(got_val, test['value'])
            self.assertEqual(got_bytes_read, len(test['serialized']))
