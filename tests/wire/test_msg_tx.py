import unittest
from tests.utils import *
from wire.msg_tx import *

noTx = MsgTx(version=1)
noTxEncoded = bytes([
    0x01, 0x00, 0x00, 0x00,  # Version
    0x00,  # Varint for number of input transactions
    0x00,  # Varint for number of output transactions
    0x00, 0x00, 0x00, 0x00,  # Lock time
])

# multiTx is a MsgTx with an input and output and used in various tests.
multiTx = MsgTx(version=1,
                tx_ins=[
                    TxIn(previous_out_point=OutPoint(hash=Hash(), index=0xffffffff),
                         signature_script=bytes([0x04, 0x31, 0xdc, 0x00, 0x1b, 0x01, 0x62]),
                         sequence=0xffffffff)
                ],
                tx_outs=[
                    TxOut(value=0x12a05f200,
                          pk_script=bytes([
                              0x41,  # OP_DATA_65
                              0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
                              0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
                              0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
                              0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
                              0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
                              0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
                              0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
                              0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
                              0xa6,  # 65-byte signature
                              0xac,  # OP_CHECKSIG
                          ])),
                    TxOut(value=0x5f5e100,
                          pk_script=bytes([
                              0x41,  # OP_DATA_65
                              0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
                              0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
                              0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
                              0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
                              0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
                              0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
                              0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
                              0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
                              0xa6,  # 65 - byte signature
                              0xac,  # OP_CHECKSIG
                          ])),
                ],
                lock_time=0)

# multiTxEncoded is the wire encoded bytes for multiTx using protocol version
# 60002 and is used in the various tests.

multiTxEncoded = bytes([
    0x01, 0x00, 0x00, 0x00,  # Version
    0x01,  # Varint for number of input transactions
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Previous output hash
    0xff, 0xff, 0xff, 0xff,  # Prevous output index
    0x07,  # Varint for length of signature script
    0x04, 0x31, 0xdc, 0x00, 0x1b, 0x01, 0x62,  # Signature script
    0xff, 0xff, 0xff, 0xff,  # Sequence
    0x02,  # Varint for number of output transactions
    0x00, 0xf2, 0x05, 0x2a, 0x01, 0x00, 0x00, 0x00,  # Transaction amount
    0x43,  # Varint for length of pk script
    0x41,  # OP_DATA_65
    0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
    0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
    0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
    0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
    0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
    0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
    0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
    0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
    0xa6,  # 65-byte signature
    0xac,  # OP_CHECKSIG
    0x00, 0xe1, 0xf5, 0x05, 0x00, 0x00, 0x00, 0x00,  # Transaction amount
    0x43,  # Varint for length of pk script
    0x41,  # OP_DATA_65
    0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
    0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
    0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
    0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
    0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
    0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
    0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
    0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
    0xa6,  # 65-byte signature
    0xac,  # OP_CHECKSIG
    0x00, 0x00, 0x00, 0x00,  # Lock time
])

# multiTxPkScriptLocs is the location information for the public key scripts
# located in multiTx.
multiTxPkScriptLocs = [63, 139]

multiWitnessTx = MsgTx(version=1,
                       tx_ins=[
                           TxIn(previous_out_point=OutPoint(
                               hash=Hash(bytes([
                                   0xa5, 0x33, 0x52, 0xd5, 0x13, 0x57, 0x66, 0xf0,
                                   0x30, 0x76, 0x59, 0x74, 0x18, 0x26, 0x3d, 0xa2,
                                   0xd9, 0xc9, 0x58, 0x31, 0x59, 0x68, 0xfe, 0xa8,
                                   0x23, 0x52, 0x94, 0x67, 0x48, 0x1f, 0xf9, 0xcd,
                               ])),
                               index=19),
                               signature_script=bytes([]),
                               witness=TxWitness([
                                   bytes([
                                       # 70-byte signature
                                       0x30, 0x43, 0x02, 0x1f, 0x4d, 0x23, 0x81, 0xdc,
                                       0x97, 0xf1, 0x82, 0xab, 0xd8, 0x18, 0x5f, 0x51,
                                       0x75, 0x30, 0x18, 0x52, 0x32, 0x12, 0xf5, 0xdd,
                                       0xc0, 0x7c, 0xc4, 0xe6, 0x3a, 0x8d, 0xc0, 0x36,
                                       0x58, 0xda, 0x19, 0x02, 0x20, 0x60, 0x8b, 0x5c,
                                       0x4d, 0x92, 0xb8, 0x6b, 0x6d, 0xe7, 0xd7, 0x8e,
                                       0xf2, 0x3a, 0x2f, 0xa7, 0x35, 0xbc, 0xb5, 0x9b,
                                       0x91, 0x4a, 0x48, 0xb0, 0xe1, 0x87, 0xc5, 0xe7,
                                       0x56, 0x9a, 0x18, 0x19, 0x70, 0x01,
                                   ]),
                                   bytes([
                                       # 33-byte serialize pub key
                                       0x03, 0x07, 0xea, 0xd0, 0x84, 0x80, 0x7e, 0xb7,
                                       0x63, 0x46, 0xdf, 0x69, 0x77, 0x00, 0x0c, 0x89,
                                       0x39, 0x2f, 0x45, 0xc7, 0x64, 0x25, 0xb2, 0x61,
                                       0x81, 0xf5, 0x21, 0xd7, 0xf3, 0x70, 0x06, 0x6a,
                                       0x8f,
                                   ])
                               ]),
                               sequence=0xffffffff)
                       ],
                       tx_outs=[
                           TxOut(value=395019,
                                 pk_script=bytes([  # // p2wkh output
                                     0x00,  # Version 0 witness program
                                     0x14,  # OP_DATA_20
                                     0x9d, 0xda, 0xc6, 0xf3, 0x9d, 0x51, 0xe0, 0x39,
                                     0x8e, 0x53, 0x2a, 0x22, 0xc4, 0x1b, 0xa1, 0x89,
                                     0x40, 0x6a, 0x85, 0x23,  # 20-byte pub key hash
                                 ])),

                       ],
                       )

# multiWitnessTxEncoded is the wire encoded bytes for multiWitnessTx including inputs
# with witness data using protocol version 70012 and is used in the various
# tests.
multiWitnessTxEncoded = bytes([
    0x1, 0x0, 0x0, 0x0,  # Version
    0x0,  # Marker byte indicating 0 inputs, or a segwit encoded tx
    0x1,  # Flag byte
    0x1,  # Varint for number of inputs
    0xa5, 0x33, 0x52, 0xd5, 0x13, 0x57, 0x66, 0xf0,
    0x30, 0x76, 0x59, 0x74, 0x18, 0x26, 0x3d, 0xa2,
    0xd9, 0xc9, 0x58, 0x31, 0x59, 0x68, 0xfe, 0xa8,
    0x23, 0x52, 0x94, 0x67, 0x48, 0x1f, 0xf9, 0xcd,  # Previous output hash
    0x13, 0x0, 0x0, 0x0,  # Little endian previous output index
    0x0,  # No sig script (this is a witness input)
    0xff, 0xff, 0xff, 0xff,  # Sequence
    0x1,  # Varint for number of outputs
    0xb, 0x7, 0x6, 0x0, 0x0, 0x0, 0x0, 0x0,  # Output amount
    0x16,  # Varint for length of pk script
    0x0,  # Version 0 witness program
    0x14,  # OP_DATA_20
    0x9d, 0xda, 0xc6, 0xf3, 0x9d, 0x51, 0xe0, 0x39,
    0x8e, 0x53, 0x2a, 0x22, 0xc4, 0x1b, 0xa1, 0x89,
    0x40, 0x6a, 0x85, 0x23,  # 20-byte pub key hash
    0x2,  # Two items on the witness stack
    0x46,  # 70 byte stack item
    0x30, 0x43, 0x2, 0x1f, 0x4d, 0x23, 0x81, 0xdc,
    0x97, 0xf1, 0x82, 0xab, 0xd8, 0x18, 0x5f, 0x51,
    0x75, 0x30, 0x18, 0x52, 0x32, 0x12, 0xf5, 0xdd,
    0xc0, 0x7c, 0xc4, 0xe6, 0x3a, 0x8d, 0xc0, 0x36,
    0x58, 0xda, 0x19, 0x2, 0x20, 0x60, 0x8b, 0x5c,
    0x4d, 0x92, 0xb8, 0x6b, 0x6d, 0xe7, 0xd7, 0x8e,
    0xf2, 0x3a, 0x2f, 0xa7, 0x35, 0xbc, 0xb5, 0x9b,
    0x91, 0x4a, 0x48, 0xb0, 0xe1, 0x87, 0xc5, 0xe7,
    0x56, 0x9a, 0x18, 0x19, 0x70, 0x1,
    0x21,  # 33 byte stack item
    0x3, 0x7, 0xea, 0xd0, 0x84, 0x80, 0x7e, 0xb7,
    0x63, 0x46, 0xdf, 0x69, 0x77, 0x0, 0xc, 0x89,
    0x39, 0x2f, 0x45, 0xc7, 0x64, 0x25, 0xb2, 0x61,
    0x81, 0xf5, 0x21, 0xd7, 0xf3, 0x70, 0x6, 0x6a,
    0x8f,
    0x0, 0x0, 0x0, 0x0,  # Lock time
])

# multiWitnessTxEncodedNonZeroFlag is an incorrect wire encoded bytes for
# multiWitnessTx including inputs with witness data. Instead of the flag byte
# being set to 0x01, the flag is 0x00, which should trigger a decoding error.
multiWitnessTxEncodedNonZeroFlag = bytes([
    0x1, 0x0, 0x0, 0x0,  # Version
    0x0,  # Marker byte indicating 0 inputs, or a segwit encoded tx
    0x0,  # Incorrect flag byte (should be 0x01)
    0x1,  # Varint for number of inputs
    0xa5, 0x33, 0x52, 0xd5, 0x13, 0x57, 0x66, 0xf0,
    0x30, 0x76, 0x59, 0x74, 0x18, 0x26, 0x3d, 0xa2,
    0xd9, 0xc9, 0x58, 0x31, 0x59, 0x68, 0xfe, 0xa8,
    0x23, 0x52, 0x94, 0x67, 0x48, 0x1f, 0xf9, 0xcd,  # Previous output hash
    0x13, 0x0, 0x0, 0x0,  # Little endian previous output index
    0x0,  # No sig script (this is a witness input)
    0xff, 0xff, 0xff, 0xff,  # Sequence
    0x1,  # Varint for number of outputs
    0xb, 0x7, 0x6, 0x0, 0x0, 0x0, 0x0, 0x0,  # Output amount
    0x16,  # Varint for length of pk script
    0x0,  # Version 0 witness program
    0x14,  # OP_DATA_20
    0x9d, 0xda, 0xc6, 0xf3, 0x9d, 0x51, 0xe0, 0x39,
    0x8e, 0x53, 0x2a, 0x22, 0xc4, 0x1b, 0xa1, 0x89,
    0x40, 0x6a, 0x85, 0x23,  # 20-byte pub key hash
    0x2,  # Two items on the witness stack
    0x46,  # 70 byte stack item
    0x30, 0x43, 0x2, 0x1f, 0x4d, 0x23, 0x81, 0xdc,
    0x97, 0xf1, 0x82, 0xab, 0xd8, 0x18, 0x5f, 0x51,
    0x75, 0x30, 0x18, 0x52, 0x32, 0x12, 0xf5, 0xdd,
    0xc0, 0x7c, 0xc4, 0xe6, 0x3a, 0x8d, 0xc0, 0x36,
    0x58, 0xda, 0x19, 0x2, 0x20, 0x60, 0x8b, 0x5c,
    0x4d, 0x92, 0xb8, 0x6b, 0x6d, 0xe7, 0xd7, 0x8e,
    0xf2, 0x3a, 0x2f, 0xa7, 0x35, 0xbc, 0xb5, 0x9b,
    0x91, 0x4a, 0x48, 0xb0, 0xe1, 0x87, 0xc5, 0xe7,
    0x56, 0x9a, 0x18, 0x19, 0x70, 0x1,
    0x21,  # 33 byte stack item
    0x3, 0x7, 0xea, 0xd0, 0x84, 0x80, 0x7e, 0xb7,
    0x63, 0x46, 0xdf, 0x69, 0x77, 0x0, 0xc, 0x89,
    0x39, 0x2f, 0x45, 0xc7, 0x64, 0x25, 0xb2, 0x61,
    0x81, 0xf5, 0x21, 0xd7, 0xf3, 0x70, 0x6, 0x6a,
    0x8f,
    0x0, 0x0, 0x0, 0x0,  # Lock time
])

# multiTxPkScriptLocs is the location information for the public key scripts
# located in multiWitnessTx.
multiWitnessTxPkScriptLocs = [58]


class TestOutPoint(unittest.TestCase):
    def setUp(self):
        # Block 100000 hash.
        self.hashStr = "3ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"

    def test_init(self):
        hash = Hash(self.hashStr)
        prev_out_index = 1
        prev_out = OutPoint(hash=hash, index=prev_out_index)
        prev_out_str = "{}:{}".format(hash.to_str(), prev_out_index)

        self.assertEqual(prev_out.hash, hash)
        self.assertEqual(prev_out.index, prev_out_index)
        self.assertEqual(str(prev_out), prev_out_str)

    def test_copy(self):
        hash = Hash(self.hashStr)
        prev_out_index = 1
        prev_out = OutPoint(hash=hash, index=prev_out_index)

        prev_out_copy = prev_out.copy()
        self.assertEqual(prev_out_copy, prev_out)

        prev_out_copy.index = 2
        self.assertNotEqual(prev_out_copy, prev_out)


class TestTxWitness(unittest.TestCase):
    def test_copy(self):
        witness = TxWitness([bytes([0x04, 0x31]),
                             bytes([0x01, 0x43])])
        witness_copy = witness.copy()
        self.assertEqual(witness_copy, witness)

        witness_copy._data[0] = bytes([0x00, 0x00])

        self.assertNotEqual(witness_copy, witness)


class TestTxIn(unittest.TestCase):
    def setUp(self):
        self.hashStr = "3ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"
        self.hash = Hash(self.hashStr)
        self.prev_out_index = 1
        self.signature_script = bytes([0x04, 0x31, 0xdc, 0x00, 0x1b, 0x01, 0x62])

        self.witness = TxWitness([bytes([0x04, 0x31]),
                                  bytes([0x01, 0x43])])

        self.prev_out = OutPoint(hash=self.hash, index=self.prev_out_index)

    def test_init(self):
        tx_in = TxIn(previous_out_point=self.prev_out,
                     signature_script=self.signature_script,
                     witness=self.witness)

        self.assertEqual(tx_in.previous_out_point, self.prev_out)
        self.assertEqual(tx_in.signature_script, self.signature_script)
        self.assertEqual(tx_in.witness, self.witness)

    def test_copy(self):
        tx_in = TxIn(previous_out_point=self.prev_out,
                     signature_script=self.signature_script,
                     witness=self.witness)

        tx_in_copy = tx_in.copy()

        self.assertEqual(tx_in_copy, tx_in)

        tx_in_copy.sequence = 0

        self.assertNotEqual(tx_in_copy, tx_in)


class TestTxOut(unittest.TestCase):
    def setUp(self):
        self.txValue = 5000000000
        self.pkScript = bytes([
            0x41,  # OP_DATA_65
            0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
            0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
            0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
            0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
            0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
            0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
            0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
            0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
            0xa6,  # 65-byte signature
            0xac,  # OP_CHECKSIG
        ])

    def test_init(self):
        tx_out = TxOut(value=self.txValue, pk_script=self.pkScript)
        self.assertEqual(tx_out.value, self.txValue)
        self.assertEqual(tx_out.pk_script, self.pkScript)

    def test_copy(self):
        tx_out = TxOut(value=self.txValue, pk_script=self.pkScript)

        tx_out_copy = tx_out.copy()

        self.assertEqual(tx_out_copy, tx_out)

        tx_out_copy.pk_script = bytes()

        self.assertNotEqual(tx_out_copy, tx_out)


class TestTx(unittest.TestCase):
    def setUp(self):
        # Make TxIn
        hashStr = "3ba27aa200b1cecaad478d2b00432346c3f1f3986da1afd33e506"
        hash = Hash(hashStr)
        prev_out_index = 1

        signature_script = bytes([0x04, 0x31, 0xdc, 0x00, 0x1b, 0x01, 0x62])

        witness = TxWitness([bytes([0x04, 0x31]),
                             bytes([0x01, 0x43])])

        prev_out = OutPoint(hash=hash, index=prev_out_index)
        self.tx_in = TxIn(previous_out_point=prev_out,
                          signature_script=signature_script,
                          witness=witness)

        # Make Tx out
        txValue = 5000000000
        pkScript = bytes([
            0x41,  # OP_DATA_65
            0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
            0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
            0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
            0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
            0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
            0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
            0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
            0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
            0xa6,  # 65-byte signature
            0xac,  # OP_CHECKSIG
        ])
        self.tx_out = TxOut(value=txValue, pk_script=pkScript)

    def test_command(self):
        msg = MsgTx(version=1)
        self.assertEqual(str(msg.command()), "tx")

    def test_max_payload_length(self):
        msg = MsgTx(version=1)
        want_payload = 1000 * 4000
        self.assertEqual(msg.max_payload_length(ProtocolVersion), want_payload)

    def test_add_tx_in(self):
        msg = MsgTx(version=1)
        msg.add_tx_in(self.tx_in)
        self.assertEqual(msg.tx_ins[0], self.tx_in)

    def test_add_tx_out(self):
        msg = MsgTx(version=1)
        msg.add_tx_out(self.tx_out)
        self.assertEqual(msg.tx_outs[0], self.tx_out)

    def test_copy(self):
        msg = MsgTx(version=1)
        msg.add_tx_in(self.tx_in)
        msg.add_tx_out(self.tx_out)
        msg_copy = msg.copy()
        self.assertEqual(msg_copy, msg)

        msg_copy.tx_ins = []
        self.assertNotEqual(msg_copy, msg)

    def test_tx_hash(self):
        #  Hash of first transaction from block 113875
        hashStr = "f051e59b5e2503ac626d03aaeac8ab7be2d72ba4b7e97119c5852d70d52dcb86"
        wantHash = Hash(hashStr)

        msg = MsgTx(version=1, lock_time=0)

        tx_in = TxIn(previous_out_point=OutPoint(hash=Hash(), index=0xffffffff),
                     signature_script=bytes([0x04, 0x31, 0xdc, 0x00, 0x1b, 0x01, 0x62]),
                     sequence=0xffffffff)

        tx_out = TxOut(value=5000000000,
                       pk_script=bytes([
                           0x41,  # OP_DATA_65
                           0x04, 0xd6, 0x4b, 0xdf, 0xd0, 0x9e, 0xb1, 0xc5,
                           0xfe, 0x29, 0x5a, 0xbd, 0xeb, 0x1d, 0xca, 0x42,
                           0x81, 0xbe, 0x98, 0x8e, 0x2d, 0xa0, 0xb6, 0xc1,
                           0xc6, 0xa5, 0x9d, 0xc2, 0x26, 0xc2, 0x86, 0x24,
                           0xe1, 0x81, 0x75, 0xe8, 0x51, 0xc9, 0x6b, 0x97,
                           0x3d, 0x81, 0xb0, 0x1c, 0xc3, 0x1f, 0x04, 0x78,
                           0x34, 0xbc, 0x06, 0xd6, 0xd6, 0xed, 0xf6, 0x20,
                           0xd1, 0x84, 0x24, 0x1a, 0x6a, 0xed, 0x8b, 0x63,
                           0xa6,  # 65-byte signature
                           0xac,  # OP_CHECKSIG
                       ]))
        msg.add_tx_in(tx_in)
        msg.add_tx_out(tx_out)
        self.assertEqual(msg.tx_hash(), wantHash)

    def test_txid_and_wtxid(self):
        """Test for tx_hash() and witness_hash()"""
        hashStrTxid = "0f167d1385a84d1518cfee208b653fc9163b605ccf1b75347e2850b3e2eb19f3"
        wantHashTxid = Hash(hashStrTxid)

        hashStrWTxid = "0858eab78e77b6b033da30f46699996396cf48fcf625a783c85a51403e175e74"
        wantHashWTxid = Hash(hashStrWTxid)

        msg = MsgTx(version=1, lock_time=0)

        tx_in = TxIn(
            previous_out_point=OutPoint(
                hash=Hash(bytes([
                    0xa5, 0x33, 0x52, 0xd5, 0x13, 0x57, 0x66, 0xf0,
                    0x30, 0x76, 0x59, 0x74, 0x18, 0x26, 0x3d, 0xa2,
                    0xd9, 0xc9, 0x58, 0x31, 0x59, 0x68, 0xfe, 0xa8,
                    0x23, 0x52, 0x94, 0x67, 0x48, 0x1f, 0xf9, 0xcd,
                ])),
                index=19),
            witness=TxWitness([
                bytes([
                    # 70-byte signature
                    0x30, 0x43, 0x02, 0x1f, 0x4d, 0x23, 0x81, 0xdc,
                    0x97, 0xf1, 0x82, 0xab, 0xd8, 0x18, 0x5f, 0x51,
                    0x75, 0x30, 0x18, 0x52, 0x32, 0x12, 0xf5, 0xdd,
                    0xc0, 0x7c, 0xc4, 0xe6, 0x3a, 0x8d, 0xc0, 0x36,
                    0x58, 0xda, 0x19, 0x02, 0x20, 0x60, 0x8b, 0x5c,
                    0x4d, 0x92, 0xb8, 0x6b, 0x6d, 0xe7, 0xd7, 0x8e,
                    0xf2, 0x3a, 0x2f, 0xa7, 0x35, 0xbc, 0xb5, 0x9b,
                    0x91, 0x4a, 0x48, 0xb0, 0xe1, 0x87, 0xc5, 0xe7,
                    0x56, 0x9a, 0x18, 0x19, 0x70, 0x01,
                ]),
                bytes([
                    # 33 - byte serialize pub key
                    0x03, 0x07, 0xea, 0xd0, 0x84, 0x80, 0x7e, 0xb7,
                    0x63, 0x46, 0xdf, 0x69, 0x77, 0x00, 0x0c, 0x89,
                    0x39, 0x2f, 0x45, 0xc7, 0x64, 0x25, 0xb2, 0x61,
                    0x81, 0xf5, 0x21, 0xd7, 0xf3, 0x70, 0x06, 0x6a,
                    0x8f,
                ]),
            ]),

            sequence=0xffffffff)

        tx_out = TxOut(value=395019,
                       pk_script=bytes([
                           0x00,  # Version 0 witness program
                           0x14,  # OP_DATA_20
                           0x9d, 0xda, 0xc6, 0xf3, 0x9d, 0x51, 0xe0, 0x39,
                           0x8e, 0x53, 0x2a, 0x22, 0xc4, 0x1b, 0xa1, 0x89,
                           0x40, 0x6a, 0x85, 0x23,  # 20-byte pub key hash
                       ]))
        msg.add_tx_in(tx_in)
        msg.add_tx_out(tx_out)

        self.assertEqual(msg.tx_hash(), wantHashTxid)
        self.assertEqual(msg.witness_hash(), wantHashWTxid)


class TestTxWire(unittest.TestCase):
    def setUp(self):

        self.tests = [
            #  Latest protocol version with no transactions.
            {
                "in": noTx,
                "out": noTx,
                "buf": noTxEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,

            },

            #  Latest protocol version with multiple transactions.
            {
                "in": multiTx,
                "out": multiTx,
                "buf": multiTxEncoded,
                "pver": ProtocolVersion,
                "enc": BaseEncoding,

            },

            #  Protocol version BIP0035Version with no transactions.
            {
                "in": noTx,
                "out": noTx,
                "buf": noTxEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding,

            },

            #  Protocol version BIP0035Version with multiple transactions.
            {
                "in": multiTx,
                "out": multiTx,
                "buf": multiTxEncoded,
                "pver": BIP0035Version,
                "enc": BaseEncoding,

            },

            #  Protocol version BIP0031Version with no transactions.
            {
                "in": noTx,
                "out": noTx,
                "buf": noTxEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding,

            },

            #  Protocol version BIP0031Version with multiple transactions.
            {
                "in": multiTx,
                "out": multiTx,
                "buf": multiTxEncoded,
                "pver": BIP0031Version,
                "enc": BaseEncoding,

            },

            #  Protocol version NetAddressTimeVersion with no transactions.
            {
                "in": noTx,
                "out": noTx,
                "buf": noTxEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding,

            },

            #  Protocol version NetAddressTimeVersion with multiple transactions.
            {
                "in": multiTx,
                "out": multiTx,
                "buf": multiTxEncoded,
                "pver": NetAddressTimeVersion,
                "enc": BaseEncoding,

            },

            #  Protocol version MultipleAddressVersion with no transactions.
            {
                "in": noTx,
                "out": noTx,
                "buf": noTxEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding,

            },

            #  Protocol version MultipleAddressVersion with multiple transactions.
            {
                "in": multiTx,
                "out": multiTx,
                "buf": multiTxEncoded,
                "pver": MultipleAddressVersion,
                "enc": BaseEncoding,

            },
        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].btc_encode(s, c['pver'], c['enc'])
            self.assertEqual(s.getvalue(), c['buf'])

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgTx()
            msg.btc_decode(s, c['pver'], c['enc'])
            self.assertEqual(msg, c['out'])


class TestTxWireErrors(unittest.TestCase):
    def setUp(self):
        pver = 60002
        self.tests = [
            # Force error in version.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 0, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in number of transaction inputs.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 4, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input previous block hash.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 5, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input previous block output index.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 37, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input signature script length.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 41, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input signature script.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 42, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input sequence.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 49, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in number of transaction outputs.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 53, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction output value.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 54, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction output pk script length.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 62, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction output lock time.
            {
                "in": multiTx, "buf": multiTxEncoded, "pver": pver, "enc": BaseEncoding,
                "max": 206, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].btc_encode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        for c in self.tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgTx()
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])


class TestTxSerialize(unittest.TestCase):
    def setUp(self):
        self.tests = [
            # No transactions.
            {
                "in": noTx,
                "out": noTx,
                "buf": noTxEncoded,
                "pkScriptLocs": [],
                "witness": False
            },

            # Multiple transactions.
            {
                "in": multiTx,
                "out": multiTx,
                "buf": multiTxEncoded,
                "pkScriptLocs": multiTxPkScriptLocs,
                "witness": False
            },

            # Multiple outputs witness transaction.
            {
                "in": multiWitnessTx,
                "out": multiWitnessTx,
                "buf": multiWitnessTxEncoded,
                "pkScriptLocs": multiWitnessTxPkScriptLocs,
                "witness": True
            },

        ]

    def test_serialize(self):
        for c in self.tests:
            s = io.BytesIO()
            c['in'].serialize(s)
            self.assertEqual(s.getvalue(), c['buf'])

    def test_deserialize(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgTx()
            if c['witness']:
                msg.deserialize(s)
            else:
                msg.deserialize_no_witness(s)
            self.assertEqual(msg, c['out'])

    def test_pk_script_locs(self):
        for c in self.tests:
            pkScriptLocs = c['in'].pk_script_locs()
            self.assertEqual(pkScriptLocs, c['pkScriptLocs'])

            for j, loc in enumerate(pkScriptLocs):
                wantPkScript = c['in'].tx_outs[j].pk_script
                gotPkScript = c['buf'][loc: loc + len(wantPkScript)]
                self.assertEqual(gotPkScript, wantPkScript)


class TestTxSerializeErrors(unittest.TestCase):
    def setUp(self):
        self.tests = [
            # Force error in version.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 0, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in number of transaction inputs.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 4, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input previous block hash.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 5, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input previous block output index.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 37, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input signature script length.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 41, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input signature script.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 42, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction input sequence.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 49, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in number of transaction outputs.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 53, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction output value.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 54, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction output pk script length.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 62, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },

            # Force error in transaction output lock time.
            {
                "in": multiTx, "buf": multiTxEncoded,
                "max": 206, "write_err": FixedBytesShortWriteErr, "read_err": FixedBytesUnexpectedEOFErr,
            },
        ]

    def test_btc_encode(self):
        for c in self.tests:
            s = FixedBytesWriter(c['max'])
            try:
                c['in'].serialize(s)
            except Exception as e:
                self.assertEqual(type(e), c['write_err'])

    def test_btc_decode(self):
        for c in self.tests:
            s = FixedBytesReader(c['max'], c['buf'])
            try:
                msg = MsgTx()
                msg.deserialize(s)
            except Exception as e:
                self.assertEqual(type(e), c['read_err'])


class TestTxOverflowErrors(unittest.TestCase):
    def setUp(self):
        # Use protocol version 70001 and transaction version 1 specifically
        # here instead of the latest values because the test data is using
        # bytes encoded with those versions.
        pver = 70001
        txVer = 1

        self.tests = [
            # Transaction that claims to have ~uint64(0) inputs.
            {
                "buf": bytes([
                    0x00, 0x00, 0x00, 0x01,  # Version
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                    0xff,  # Varint for number of input transactions
                ]),
                "pver": pver,
                "enc": BaseEncoding,
                "version": txVer,
                "decode_err": MaxTxInPerMessageMsgErr,
                "deserialize_err": MaxTxInPerMessageMsgErr
            },

            # Transaction that claims to have ~uint64(0) outputs.
            {
                "buf": bytes([
                    0x00, 0x00, 0x00, 0x01,  # Version
                    0x00,
                    # Varint for number of input transactions    # TOCHECK according to https://en.bitcoin.it/wiki/Protocol_documentation#tx, tx_in count should't be zero
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                    0xff,  # Varint for number of output transactions
                ]),
                "pver": pver,
                "enc": BaseEncoding,
                "version": txVer,
                "decode_err": MaxTxOutPerMessageMsgErr,
                "deserialize_err": WitnessTxFlagByteMsgErr
            },

            # Transaction that has an input with a signature script that
            # claims to have ~uint64(0) length.
            {
                "buf": bytes([
                    0x00, 0x00, 0x00, 0x01,  # Version
                    0x01,  # Varint for number of input transactions
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Previous output hash
                    0xff, 0xff, 0xff, 0xff,  # Prevous output index
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                    0xff,  # Varint for length of signature script
                ]),
                "pver": pver,
                "enc": BaseEncoding,
                "version": txVer,
                "decode_err": ReadScriptTooLongMsgErr,
                "deserialize_err": ReadScriptTooLongMsgErr
            },

            # Transaction that has an output with a public key script
            # that claims to have ~uint64(0) length.
            {
                "buf": bytes([
                    0x00, 0x00, 0x00, 0x01,  # Version
                    0x01,  # Varint for number of input transactions
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Previous output hash
                    0xff, 0xff, 0xff, 0xff,  # Prevous output index
                    0x00,  # Varint for length of signature script
                    0xff, 0xff, 0xff, 0xff,  # Sequence
                    0x01,  # Varint for number of output transactions
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # Transaction amount
                    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
                    0xff,  # Varint for length of public key script
                ]),
                "pver": pver,
                "enc": BaseEncoding,
                "version": txVer,
                "decode_err": ReadScriptTooLongMsgErr,
                "deserialize_err": ReadScriptTooLongMsgErr,
            },

        ]

    def test_btc_decode(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgTx()
            try:
                msg.btc_decode(s, c['pver'], c['enc'])
            except Exception as e:
                self.assertEqual(type(e), c['decode_err'])

    def test_deserialize(self):
        for c in self.tests:
            s = io.BytesIO(c['buf'])
            msg = MsgTx()
            try:
                msg.deserialize(s)
            except Exception as e:
                self.assertEqual(type(e), c['deserialize_err'])


class TestTxSerializeSizeStripped(unittest.TestCase):
    def test_serialize_size_stripped(self):
        tests = [
            # No inputs or outpus.
            {
                "in": noTx,
                "size": 10
            },

            # Transcaction with an input and an output.
            {
                "in": multiTx,
                "size": 210
            },

            # Transaction with an input which includes witness data, and
            # one output. Note that this uses SerializeSizeStripped which
            # excludes the additional bytes due to witness data encoding.
            {
                "in": multiWitnessTx,
                "size": 82
            }
        ]

        for c in tests:
            self.assertEqual(c['in'].serialize_size_stripped(), c['size'])


class TestTxWitnessSize(unittest.TestCase):
    def test_serialize_size(self):
        tests = [

            # Transaction with an input which includes witness data, and
            # one output.
            {
                "in": multiWitnessTx,
                "size": 190
            },
        ]

        for c in tests:
            self.assertEqual(c['in'].serialize_size(), c['size'])
