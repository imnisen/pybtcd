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
    # TOADD parallel

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
            self.assertEqual(bytes(got_bytes), test['serialized'])
            self.assertEqual(got_bytes_written, len(test['serialized']))

    def test_deserialize_vlq(self):
        for test in self.tests:
            got_val, got_bytes_read = deserialize_vlq(test['serialized'])
            self.assertEqual(got_val, test['value'])
            self.assertEqual(got_bytes_read, len(test['serialized']))


# TestScriptCompression ensures the domain-specific script compression and
# decompression works as expected.
class TestScriptCompression(unittest.TestCase):
    # TOADD parallel

    def setUp(self):
        self.tests = [
            {
                "name": "None",
                "uncompressed": bytes(),
                "compressed": hex_to_bytes("06"),
            },
            {
                "name": "pay-to-pubkey-hash 1",
                "uncompressed": hex_to_bytes("76a9141018853670f9f3b0582c5b9ee8ce93764ac32b9388ac"),
                "compressed": hex_to_bytes("001018853670f9f3b0582c5b9ee8ce93764ac32b93"),
            },
            {
                "name": "pay-to-pubkey-hash 2",
                "uncompressed": hex_to_bytes("76a914e34cce70c86373273efcc54ce7d2a491bb4a0e8488ac"),
                "compressed": hex_to_bytes("00e34cce70c86373273efcc54ce7d2a491bb4a0e84"),
            },
            {
                "name": "pay-to-script-hash 1",
                "uncompressed": hex_to_bytes("a914da1745e9b549bd0bfa1a569971c77eba30cd5a4b87"),
                "compressed": hex_to_bytes("01da1745e9b549bd0bfa1a569971c77eba30cd5a4b"),
            },
            {
                "name": "pay-to-script-hash 2",
                "uncompressed": hex_to_bytes("a914f815b036d9bbbce5e9f2a00abd1bf3dc91e9551087"),
                "compressed": hex_to_bytes("01f815b036d9bbbce5e9f2a00abd1bf3dc91e95510"),
            },
            {
                "name": "pay-to-pubkey compressed 0x02",
                "uncompressed": hex_to_bytes("2102192d74d0cb94344c9569c2e77901573d8d7903c3ebec3a957724895dca52c6b4ac"),
                "compressed": hex_to_bytes("02192d74d0cb94344c9569c2e77901573d8d7903c3ebec3a957724895dca52c6b4"),
            },
            {
                "name": "pay-to-pubkey compressed 0x03",
                "uncompressed": hex_to_bytes("2103b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65ac"),
                "compressed": hex_to_bytes("03b0bd634234abbb1ba1e986e884185c61cf43e001f9137f23c2c409273eb16e65"),
            },
            {
                "name": "pay-to-pubkey uncompressed 0x04 even",
                "uncompressed": hex_to_bytes(
                    "4104192d74d0cb94344c9569c2e77901573d8d7903c3ebec3a957724895dca52c6b40d45264838c0bd96852662ce6a847b197376830160c6d2eb5e6a4c44d33f453eac"),
                "compressed": hex_to_bytes("04192d74d0cb94344c9569c2e77901573d8d7903c3ebec3a957724895dca52c6b4"),
            },
            {
                "name": "pay-to-pubkey uncompressed 0x04 odd",
                "uncompressed": hex_to_bytes(
                    "410411db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddfb84ccf9744464f82e160bfa9b8b64f9d4c03f999b8643f656b412a3ac"),
                "compressed": hex_to_bytes("0511db93e1dcdb8a016b49840f8c53bc1eb68a382e97b1482ecad7b148a6909a5c"),
            },
            {
                "name": "pay-to-pubkey invalid pubkey",
                "uncompressed": hex_to_bytes("3302aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaac"),
                "compressed": hex_to_bytes("293302aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaac"),
            },
            {
                "name": "null data",
                "uncompressed": hex_to_bytes("6a200102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20"),
                "compressed": hex_to_bytes("286a200102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20"),
            },
            {
                "name": "requires 2 size bytes - data push 200 bytes",
                "uncompressed": hex_to_bytes("4cc8") + bytes(200),
                # [0x80, 0x50] = 208 as a variable length quantity
                # [0x4c, 0xc8] = OP_PUSHDATA1 200
                "compressed": hex_to_bytes("80504cc8") + bytes(200),
            },
        ]

    def test_compressed_script_size(self):
        for test in self.tests:
            got_size = compressed_script_size(test['uncompressed'])
            self.assertEqual(got_size, len(test['compressed']))

    def test_put_compressed_script(self):
        for test in self.tests:
            got_size = compressed_script_size(test['uncompressed'])
            got_compressed = bytearray(got_size)
            got_bytes_written = put_compressed_script(got_compressed, test['uncompressed'])
            self.assertEqual(bytes(got_compressed), test['compressed'])
            self.assertEqual(got_bytes_written, len(test['compressed']))

    def test_decode_compressed_script_size(self):
        for test in self.tests:
            got_decoded_size = decode_compressed_script_size(test['compressed'])
            self.assertEqual(got_decoded_size, len(test['compressed']))

        # Error case
        # A nil script must result in a decoded size of 0.
        got_size = decode_compressed_script_size(bytes())
        self.assertEqual(got_size, 0)

    def test_decompress_script(self):
        for test in self.tests:
            got_decompressed = decompress_script(test['compressed'])
            self.assertEqual(got_decompressed, test['uncompressed'])

        # Error case
        # A nil script must result in a nil decompressed script.
        got_script = decompress_script(bytes())
        self.assertEqual(got_script, bytes())

        # A compressed script for a pay-to-pubkey (uncompressed) that results
        # in an invalid pubkey must result in a nil decompressed script.
        compressed_script = hex_to_bytes("04012d74d0cb94344c9569c2e77901573d8d" +
                                         "7903c3ebec3a957724895dca52c6b4")
        got_script = decompress_script(compressed_script)
        self.assertEqual(got_script, bytes())


# TestAmountCompression ensures the domain-specific transaction output amount
# compression and decompression works as expected.
class TestAmountCompression(unittest.TestCase):
    # TOADD parallel

    def setUp(self):
        self.tests = [
            {
                "name": "0 BTC (sometimes used in nulldata)",
                "uncompressed": 0,
                "compressed": 0,
            },
            {
                "name": "546 Satoshi (current network dust value)",
                "uncompressed": 546,
                "compressed": 4911,
            },
            {
                "name": "0.00001 BTC (typical transaction fee)",
                "uncompressed": 1000,
                "compressed": 4,
            },
            {
                "name": "0.0001 BTC (typical transaction fee)",
                "uncompressed": 10000,
                "compressed": 5,
            },
            {
                "name": "0.12345678 BTC",
                "uncompressed": 12345678,
                "compressed": 111111101,
            },
            {
                "name": "0.5 BTC",
                "uncompressed": 50000000,
                "compressed": 48,
            },
            {
                "name": "1 BTC",
                "uncompressed": 100000000,
                "compressed": 9,
            },
            {
                "name": "5 BTC",
                "uncompressed": 500000000,
                "compressed": 49,
            },
            {
                "name": "21000000 BTC (max minted coins)",
                "uncompressed": 2100000000000000,
                "compressed": 21000000,
            },
        ]

    def test_compress_tx_out_amount(self):
        for test in self.tests:
            got_compressed = compress_tx_out_amount(test['uncompressed'])
            self.assertEqual(got_compressed, test['compressed'])

    def test_decompress_tx_out_amount(self):
        for test in self.tests:
            got_decompressed = decompress_tx_out_amount(test['compressed'])
            self.assertEqual(got_decompressed, test['uncompressed'])


# TestCompressedTxOut ensures the transaction output serialization and
# deserialization works as expected.
class TestCompressedTxOut(unittest.TestCase):
    # TOADD parallel

    def setUp(self):
        self.tests = [
            {
                "name": "nulldata with 0 BTC",
                "amount": 0,
                "pk_script": hex_to_bytes("6a200102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20"),
                "compressed": hex_to_bytes("00286a200102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20"),
            },
            {
                "name": "pay-to-pubkey-hash dust",
                "amount": 546,
                "pk_script": hex_to_bytes("76a9141018853670f9f3b0582c5b9ee8ce93764ac32b9388ac"),
                "compressed": hex_to_bytes("a52f001018853670f9f3b0582c5b9ee8ce93764ac32b93"),
            },
            {
                "name": "pay-to-pubkey uncompressed 1 BTC",
                "amount": 100000000,
                "pk_script": hex_to_bytes(
                    "4104192d74d0cb94344c9569c2e77901573d8d7903c3ebec3a957724895dca52c6b40d45264838c0bd96852662ce6a847b197376830160c6d2eb5e6a4c44d33f453eac"),
                "compressed": hex_to_bytes("0904192d74d0cb94344c9569c2e77901573d8d7903c3ebec3a957724895dca52c6b4"),
            },
        ]

    def test_compress_tx_out_size(self):
        for test in self.tests:
            got_size = compress_tx_out_size(test['amount'], test['pk_script'])
            self.assertEqual(got_size, len(test['compressed']))

    def test_put_compressed_tx_out(self):
        for test in self.tests:
            got_size = compress_tx_out_size(test['amount'], test['pk_script'])
            got_compressed = bytearray(got_size)
            got_bytes_written = put_compressed_tx_out(got_compressed, test['amount'], test['pk_script'])
            self.assertEqual(bytes(got_compressed), test['compressed'])
            self.assertEqual(got_bytes_written, len(test['compressed']))

    def test_decode_compressed_tx_out(self):
        for test in self.tests:
            got_amount, got_script, got_bytes_written = decode_compressed_tx_out(test['compressed'])
            self.assertEqual(got_amount, test['amount'])
            self.assertEqual(got_script, test['pk_script'])
            self.assertEqual(got_bytes_written, len(test['compressed']))

        # Error conditions
        compressed_tx_out = hex_to_bytes("00")
        with self.assertRaises(DeserializeError):
            decode_compressed_tx_out(compressed_tx_out)

        compressed_tx_out = hex_to_bytes("0010")
        with self.assertRaises(DeserializeError):
            decode_compressed_tx_out(compressed_tx_out)
