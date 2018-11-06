import unittest
import wire
import os
import bz2
import btcutil
import chaincfg
import database
import copy
import chainhash

# some constant

# blockDataNet is the expected network in the test block data.
blockDataNet = wire.BitcoinNet.MainNet

# blockDataFile is the path to a file containing the first 256 blocks
# of the block chain.
dataDirPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
blockDataFile = os.path.join(dataDirPath, "testdata", "blocks1-256.bz2")


# print("blockDataFile", blockDataFile)


class TestContext:
    def __init__(self, db, bucket_depth=None, is_writeable=None, blocks=None):
        """

        :param database.DB db:
        :param int bucket_depth:
        :param bool is_writeable:
        :param [btcutil.Block] blocks:
        """

        self.db = db
        self.bucket_depth = bucket_depth or 0
        self.is_writeable = is_writeable or False
        self.blocks = blocks or []


class KeyPair:
    def __init__(self, key, value):
        """

        :param bytes key:
        :param bytes or None value:
        """
        self.key = key
        self.value = value


class TestInterface(unittest.TestCase):
    # loadBlocks loads the blocks contained in the testdata directory and returns
    # a slice of them.
    def _load_blocks(self, data_file: str, network: wire.BitcoinNet):
        with bz2.open(data_file, 'rb') as f:
            blocks = []  # for return blocks

            # set the first block as genesis block
            genesis = btcutil.Block(chaincfg.MainNetParams.genesis_block)
            blocks.append(genesis)

            while True:
                # check EOF (not full correct check)
                b = f.read(4)
                if len(b) < 4:
                    break

                # Load the remaining blocks
                net = wire.BitcoinNet.from_int(int.from_bytes(b, byteorder="little"))

                self.assertEqual(net, network)

                # read blockLen(uint32)
                block_len = wire.read_element(f, "uint32")

                # read block bytes
                block_bytes = f.read(block_len)

                block = btcutil.Block.from_bytes(block_bytes)

                blocks.append(block)

            return blocks

    # testGetValues checks that all of the provided key/value pairs can be
    # retrieved from the database and the retrieved values match the provided
    # values.
    def _test_get_values(self, tc, bucket, values):
        for item in values:
            got_value = bucket.get(item.key)
            self.assertEqual(got_value, item.value)
        return

    # testPutValues stores all of the provided key/value pairs in the provided
    # bucket while checking for errors.
    def _test_put_values(self, tc, bucket, values):
        for item in values:
            bucket.put(item.key, item.value)
        return

    def _test_delete_values(self, tc, bucket, values):
        for item in values:
            bucket.delete(item.key, item.value)
        return

    # toGetValues returns a copy of the provided keypairs with all of the nil
    # values set to an empty byte slice.  This is used to ensure that keys set to
    # nil values result in empty byte slices when retrieved instead of nil.
    def _to_get_values(self, values):
        values = copy.deepcopy(values)
        for item in values:
            if item.value is None:
                item.value = bytes()
        return values

    def _roll_back_values(self, values):
        values = copy.deepcopy(values)
        for item in values:
            item.value = None
        return values

    # testCursorKeyPair checks that the provide key and value match the expected
    # keypair at the provided index.  It also ensures the index is in range for the
    # provided slice of expected keypairs.
    def _test_cursor_key_pair(self, tc, k, v, index, values):
        self.assertTrue(index > 0)
        self.assertTrue(index < len(values))

        pair = values[index]
        self.assertEqual(k, pair.key)
        self.assertEqual(v, pair.value)
        return

    # lookupKey is a convenience method to lookup the requested key from the
    # provided keypair slice along with whether or not the key was found.
    def _lookup_key(self, key, values):
        for item in values:
            if key == item.key:
                return item.value, True
        return None, False

    # testNestedBucket reruns the testBucketInterface against a nested bucket along
    # with a counter to only test a couple of level deep.
    def _test_nested_bucket(self, tc, test_bucket):
        # Don't go more than 2 nested levels deep.
        if tc.bucket_depth > 1:
            return True

        tc.bucket_depth += 1
        try:
            return self._test_bucket_inteface(tc, test_bucket)
        finally:
            tc.bucket_depth -= 1

    # testCursorInterface ensures the cursor itnerface is working properly by
    # exercising all of its functions on the passed bucket.
    def _test_cursor_interface(self, tc: TestContext, bucket: database.Bucket):
        # Ensure a cursor can be obtained for the bucket.
        cursor = bucket.cursor()

        # Ensure the cursor returns the same bucket it was created for.
        self.assertEqual(cursor.get_bucket(), bucket)

        if tc.is_writeable:
            unsorted_values = [
                KeyPair(b"cursor", b"val1"),
                KeyPair(b"abcd", b"val2"),
                KeyPair(b"bcd", b"val3"),
                KeyPair(b"defg", None),
            ]

            sorted_values = [
                KeyPair(b"abcd", b"val2"),
                KeyPair(b"bcd", b"val3"),
                KeyPair(b"cursor", b"val1"),
                KeyPair(b"defg", None),
            ]

            # Store the values to be used in the cursor tests in unsorted
            # order and ensure they were actually stored.
            self._test_put_values(tc, bucket, unsorted_values)
            self._test_get_values(tc, bucket, self._to_get_values(unsorted_values))

            # Ensure the cursor returns all items in byte-sorted order when
            # iterating forward.
            cur_idx = 0
            ok = cursor.first()
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx += 1
                ok = cursor.next()

            self.assertEqual(cur_idx, len(unsorted_values))

            # Ensure the cursor returns all items in reverse byte-sorted
            # order when iterating in reverse.
            cur_idx = len(unsorted_values) - 1
            ok = cursor.last()
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx -= 1
                ok = cursor.prev()

            self.assertEqual(cur_idx, -1)

            # Ensure forward iteration works as expected after seeking.
            middle_idx = (len(sorted_values) - 1) // 2
            seek_key = sorted_values[middle_idx].key

            cur_idx = middle_idx
            ok = cursor.seek(seek_key)
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx += 1
                ok = cursor.next()

            self.assertEqual(cur_idx, len(unsorted_values))

            # Ensure reverse iteration works as expected after seeking.
            cur_idx = middle_idx
            ok = cursor.seek(seek_key)
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx -= 1
                ok = cursor.prev()

            self.assertEqual(cur_idx, -1)

            # Ensure the cursor deletes items properly.
            self.assertTrue(cursor.first())

            k = cursor.key()
            cursor.delete()
            self.assertIsNone(bucket.get(k))

        return

    # testBucketInterface ensures the bucket interface is working properly by
    # exercising all of its functions.  This includes the cursor interface for the
    # cursor returned from the bucket.
    def _test_bucket_inteface(self, tc: TestContext, bucket: database.Bucket):
        self.assertEqual(bucket.writable(), tc.is_writeable)

        if tc.is_writeable:
            key_values = [
                KeyPair(b"bucketkey1", b"foo1"),
                KeyPair(b"bucketkey2", b"foo2"),
                KeyPair(b"bucketkey3", b"foo3"),
                KeyPair(b"bucketkey4", None),
            ]
            expected_key_values = self._to_get_values(key_values)
            self._test_put_values(tc, bucket, key_values)
            self._test_get_values(tc, bucket, self._to_get_values(expected_key_values))

            # Iterate all of the keys using ForEach while making sure the
            # stored values are the expected values.
            keys_found = []

            for k, v in bucket.for_each2():
                want_v, found = self._lookup_key(k, expected_key_values)
                self.assertTrue(found)

                self.assertEqual(v, want_v)

                keys_found.append(k)

            # Ensure all keys were iterated.
            for item in key_values:
                self.assertTrue(item.key in keys_found)

            # Delete the keys and ensure they were deleted.
            self._test_delete_values(tc, bucket, key_values)
            self._test_get_values(tc, bucket, self._roll_back_values(key_values))

            # Ensure creating a new bucket works as expected.
            test_bucket_name = b"testbucket"
            test_bucket = bucket.create_bucket(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure creating a bucket that already exists fails with the
            # expected error.
            with self.assertRaises(database.DBError) as cm:
                bucket.create_bucket(test_bucket_name)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrBucketExists)

            # Ensure CreateBucketIfNotExists returns an existing bucket.
            test_bucket = bucket.create_bucket_if_not_exists(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure retrieving an existing bucket works as expected.
            test_bucket = bucket.bucket(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure deleting a bucket works as intended.
            bucket.delete_bucket(test_bucket_name)
            self.assertIsNone(bucket.bucket(test_bucket_name))

            # Ensure deleting a bucket that doesn't exist returns the
            #  expected error.
            with self.assertRaises(database.DBError) as cm:
                bucket.delete_bucket(test_bucket_name)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrBucketNotFound)

            # Ensure CreateBucketIfNotExists creates a new bucket when
            # it doesn't already exist.
            test_bucket = bucket.create_bucket_if_not_exists(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure the cursor interface works as expected.
            self._test_cursor_interface(tc, test_bucket)

            # Delete the test bucket to avoid leaving it around for future
            # calls.
            bucket.delete_bucket(test_bucket_name)
            self.assertIsNone(bucket.bucket(test_bucket_name))
        else:
            # Put should fail with bucket that is not writable.
            fail_bytes = b"fail"
            with self.assertRaises(database.DBError) as cm:
                bucket.put(fail_bytes, fail_bytes)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.delete(fail_bytes)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.create_bucket(fail_bytes)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.create_bucket_if_not_exists(fail_bytes)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.delete_bucket(fail_bytes)
            self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            # Ensure the cursor interface works as expected with read-only
            # buckets.
            self._test_cursor_interface(tc, bucket)

        return

    # testManagedTxPanics ensures calling Rollback of Commit inside a managed
    # transaction panics.
    def _test_managed_tx_panics(self, tc):
        # Ensure calling Commit on a managed read-only transaction panics.
        with self.assertRaises(Exception):
            tc.db.view(lambda tx: tx.commit())

        # Ensure calling Rollback on a managed read-only transaction panics.
        with self.assertRaises(Exception):
            tc.db.view(lambda tx: tx.rollback())

        # Ensure calling Commit on a managed read-write transaction panics.
        with self.assertRaises(Exception):
            tc.db.update(lambda tx: tx.commit())

        # Ensure calling Rollback on a managed read-write transaction panics.
        with self.assertRaises(Exception):
            tc.db.update(lambda tx: tx.rollback())

        return

    # testMetadataManualTxInterface ensures that the manual transactions metadata
    # interface works as expected.
    def _test_metadata_manual_tx_interface(self, tc):
        # populateValues tests that populating values works as expected.
        #
        # When the writable flag is false, a read-only tranasction is created,
        # standard bucket tests for read-only transactions are performed, and
        # the Commit function is checked to ensure it fails as expected.
        #
        # Otherwise, a read-write transaction is created, the values are
        # written, standard bucket tests for read-write transactions are
        # performed, and then the transaction is either committed or rolled
        # back depending on the flag.
        bucket1_name = b"bucket1"

        def populate_values(writable: bool, rollback: bool, put_values: [KeyPair]) -> bool:
            tx = tc.db.begin(writable)

            # TODO rollback on panic

            metadata_bucket = tx.metadata()
            print("metadata bucket", metadata_bucket)
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            tc.is_writeable = writable

            self._test_bucket_inteface(tc, bucket1)

            if not writable:
                # The transaction is not writable, so it should fail
                # the commit.

                # test_name = "unwritable tx commit"
                with self.assertRaises(database.DB) as cm:
                    tx.commit()  # TOCHANGE TODO commit and rollback raise a exception that not catch here
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)
            else:
                self.assertTrue(self._test_put_values(tc, bucket1, put_values))
                if rollback:
                    tx.rollback()
                else:
                    tx.commit()

            return

        # checkValues starts a read-only transaction and checks that all of
        # the key/value pairs specified in the expectedValues parameter match
        # what's in the database.
        def check_values(expected_values: [KeyPair]) -> bool:
            tx = tc.db.begin(False)

            # TODO rollback on panic
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            self._test_get_values(tc, bucket1, expected_values)

            tx.rollback()

            return

        # deleteValues starts a read-write transaction and deletes the keys
        # in the passed key/value pairs.
        def delete_values(values: [KeyPair]) -> bool:
            tx = tc.db.begin(True)

            # TODO rollback on panic

            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            self._test_delete_values(tc, bucket1, values)

            self._test_get_values(tc, bucket1, self._roll_back_values(values))

            return

        # keyValues holds the keys and values to use when putting values into a
        # bucket.
        key_values = [
            KeyPair(b"umtxkey1", b"foo1"),
            KeyPair(b"umtxkey2", b"foo2"),
            KeyPair(b"umtxkey3", b"foo3"),
            KeyPair(b"umtxkey4", None),
        ]

        # Ensure that attempting populating the values using a read-only
        # transaction fails as expected.
        populate_values(False, True, key_values)
        check_values(self._roll_back_values(key_values))

        # Ensure that attempting populating the values using a read-write
        # transaction and then rolling it back yields the expected values.
        populate_values(True, True, key_values)
        check_values(self._roll_back_values(key_values))

        # Ensure that attempting populating the values using a read-write
        # transaction and then committing it stores the expected values.
        populate_values(True, False, key_values)
        check_values(self._roll_back_values(key_values))

        # Clean up the keys.
        delete_values(key_values)

        return

    # testMetadataTxInterface tests all facets of the managed read/write and
    # manual transaction metadata interfaces as well as the bucket interfaces under
    # them.
    def _test_metadata_tx_interface(self, tc):
        self._test_managed_tx_panics(tc)

        bucket1_name = b"bucket1"
        tc.db.update(lambda tx: tx.metadata().create_bucket(bucket1_name))

        self._test_metadata_manual_tx_interface(tc)

        # keyValues holds the keys and values to use when putting values
        # into a bucket.
        key_values = [
            KeyPair(b"mtxkey1", b"foo1"),
            KeyPair(b"mtxkey2", b"foo2"),
            KeyPair(b"mtxkey3", b"foo3"),
            KeyPair(b"mtxkey4", None),
        ]

        # Test the bucket interface via a managed read-only transaction.
        def test_read_only(tx):
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            tc.is_writeable = False
            self._test_bucket_inteface(tc, bucket1)

        tc.db.view(test_read_only)

        # Ensure errors returned from the user-supplied View function are
        # returned.
        class viewError(Exception):
            """example view error"""
            pass

        def test_user_error(tx):
            raise viewError

        with self.assertRaises(viewError) as cm:
            tc.db.view(test_user_error)
        self.assertIsInstance(cm.exception, viewError)  # TOCHECK TOREMOVE

        # # Test the bucket interface via a managed read-write transaction.
        # Also, put a series of values and force a rollback so the following
        # code can ensure the values were not stored.
        class forceRollbackError(Exception):
            pass

        def test_read_write(tx):
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            tc.is_writeable = True
            self._test_bucket_inteface(tc, bucket1)

            self._test_put_values(tc, bucket1, key_values)

            raise forceRollbackError

        with self.assertRaises(forceRollbackError) as cm:
            tc.db.view(test_read_write)
        self.assertIsInstance(cm.exception, viewError)  # TOCHECK TOREMOVE

        # Ensure the values that should not have been stored due to the forced
        # rollback above were not actually stored.
        def test_values_exsits(tx):
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)
            self._test_get_values(tc, metadata_bucket, self._roll_back_values(key_values))

        tc.db.view(test_values_exsits)

        # Store a series of values via a managed read-write transaction.
        def test_read_write_store(tx):
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            self._test_put_values(tc, bucket1, key_values)

        tc.db.update(test_read_write_store)

        # Ensure the values stored above were committed as expected.
        def test_read_write_get(tx):
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            self._test_get_values(tc, bucket1, self._to_get_values(key_values))

        tc.db.view(test_read_write_get)

        # Clean up the values stored above in a managed read-write transaction.
        def test_read_write_clean(tx):
            metadata_bucket = tx.metadata()
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            self._test_delete_values(tc, bucket1, key_values)

        tc.db.update(test_read_write_clean)

        return

    # testFetchBlockIO ensures all of the block retrieval API functions work as
    # expected for the provide set of blocks.  The blocks must already be stored in
    # the database, or at least stored into the the passed transaction.  It also
    # tests several error conditions such as ensuring the expected errors are
    # returned when fetching blocks, headers, and regions that don't exist.
    def _test_fetch_block_io(self, tc: TestContext, tx: database.Tx):
        # ---------------------
        # Non-bulk Block IO API
        # ---------------------

        # Test the individual block APIs one block at a time.  Also, build the
        # data needed to test the bulk APIs below while looping.
        all_block_hashes = []
        all_block_bytes = []
        all_block_tx_loc = []
        all_block_regions = []
        for block in tc.blocks:
            block_hash = block.hash()
            all_block_hashes.append(block_hash)

            block_bytes = block.bytes()
            all_block_bytes.append(block_bytes)

            tx_locs = block.tx_loc()
            all_block_tx_loc.append(tx_locs)

            # Ensure the block data fetched from the database matches the
            # expected bytes.
            got_block_bytes = tx.fetch_block(block_hash)
            self.assertEqual(got_block_bytes, block_bytes)

            # Ensure the block header fetched from the database matches the
            # expected bytes.
            want_header_bytes = block_bytes[0: wire.MaxBlockHeaderPayload]
            got_block_bytes = tx.fetch_block_header(block_hash)
            self.assertEqual(got_block_bytes, want_header_bytes)

            # Ensure the first transaction fetched as a block region from
            # the database matches the expected bytes.
            region = database.BlockRegion(
                hash=block_hash, offset=tx_locs[0].tx_start, len=tx_locs[0].tx_len
            )
            all_block_regions.append(region)

            want_region_bytes = block_bytes[region.offset: region.offset + region.len]
            got_region_bytes = tx.fetch_block_region(region)
            self.assertEqual(got_region_bytes, want_region_bytes)

            # Ensure hash block works as expected
            self.assertTrue(tx.has_block(block_hash))

            # -----------------------
            # Invalid blocks/regions.
            # -----------------------

            # Ensure fetching a block that doesn't exist returns the
            # expected error.
            bad_block_hash = chainhash.Hash()
            want_err_code = database.ErrorCode.ErrBlockNotFound
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block(bad_block_hash)
                self.assertEqual(cm.exception.c, want_err_code)

            # Ensure fetching a block header that doesn't exist returns
            # the expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_header(bad_block_hash)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure fetching a block region in a block that doesn't exist
            # return the expected error.
            region.hash = bad_block_hash
            region.offset = 0
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_region(region)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure fetching a block region that is out of bounds returns
            # the expected error.
            want_err_code = database.ErrorCode.ErrBlockRegionInvalid
            region.hash = block_hash
            region.offset = 0
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_region(region)
                self.assertEqual(cm.exception.c, want_err_code)

        # -----------------
        # Bulk Block IO API
        # -----------------

        # Ensure the bulk block data fetched from the database matches the
        # expected bytes.
        block_data = tx.fetch_blocks(all_block_hashes)
        self.assertListEqual(block_data, all_block_bytes)

        # Ensure the bulk block headers fetched from the database match the
        # expected bytes.
        block_header_data = tx.fetch_block_headers(all_block_hashes)
        self.assertListEqual(block_header_data, [each[0:wire.MaxBlockHeaderPayload] for each in all_block_bytes])

        # Ensure the first transaction of every block fetched in bulk block
        # regions from the database matches the expected bytes.
        all_region_bytes = tx.fetch_block_regions(all_block_regions)
        self.assertEqual(len(all_region_bytes), len(all_block_regions))
        for i, got_region_bytes in enumerate(all_region_bytes):
            region = all_block_regions[i]
            want_region_bytes = block_data[i][region.offset: region.offset + region.len]
            self.assertEqual(got_region_bytes, want_region_bytes)

        # Ensure the bulk determination of whether a set of block hashes are in
        # the database returns true for all loaded blocks.
        has_blocks = tx.has_blocks(all_block_hashes)
        for has_block in has_blocks:
            self.assertTrue(has_block)

        # -----------------------
        # Invalid blocks/regions.
        # -----------------------

        # Ensure fetching blocks for which one doesn't exist returns the
        # expected error.
        bad_block_hashes = copy.deepcopy(all_block_hashes)
        bad_block_hashes.append(chainhash.Hash())
        want_err_code = database.ErrorCode.ErrBlockNotFound
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_blocks(bad_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure fetching block headers for which one doesn't exist returns the
        # expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_headers(bad_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure fetching block regions for which one of blocks doesn't exist
        # returns expected error.
        bad_block_regions = copy.deepcopy(all_block_regions)
        bad_block_regions.append(database.BlockRegion(
            hash=chainhash.Hash(), offset=0, len=0
        ))
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_regions(bad_block_regions)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure fetching block regions that are out of bounds returns the
        # expected error.
        bad_block_regions = bad_block_regions[:-1]
        bad_block_regions[-1].offset = 0
        want_err_code = database.ErrorCode.ErrBlockRegionInvalid
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_regions(bad_block_regions)
        self.assertEqual(cm.exception.c, want_err_code)

        return

    # testFetchBlockIOMissing ensures that all of the block retrieval API functions
    # work as expected when requesting blocks that don't exist.
    def _test_fetch_block_io_missing(self, tc: TestContext, tx: database.Tx):
        want_err_code = database.ErrorCode.ErrBlockNotFound

        # ---------------------
        # Non-bulk Block IO API
        # ---------------------

        # Test the individual block APIs one block at a time to ensure they
        # return the expected error.  Also, build the data needed to test the
        # bulk APIs below while looping.
        all_block_hashes = []
        all_block_regions = []
        for block in tc.blocks:
            block_hash = block.hash()
            all_block_hashes.append(block)

            tx_locs = block.tx_loc()

            # Ensure FetchBlock returns expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block(block_hash)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure FetchBlockHeader returns expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_header(block_hash)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure the first transaction fetched as a block region from
            # the database returns the expected error.
            region = database.BlockRegion(
                hash=block_hash, offset=tx_locs[0].tx_start, len=tx_locs[0].tx_len
            )
            all_block_regions.append(region)

            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_region(region)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure HasBlock returns false.
            self.assertFalse(tx.has_block(block_hash))

        # -----------------
        # Bulk Block IO API
        # -----------------

        # Ensure FetchBlocks returns expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_blocks(all_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure FetchBlockHeaders returns expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_headers(all_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure FetchBlockRegions returns expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_regions(all_block_regions)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure HasBlocks returns false for all blocks.
        has_blocks = tx.has_blocks(all_block_hashes)
        for has_block in has_blocks:
            self.assertFalse(has_block)

        return

    # testBlockIOTxInterface ensures that the block IO interface works as expected
    # for both managed read/write and manual transactions.  This function leaves
    # all of the stored blocks in the database.
    def _test_block_io_tx_interface(self, tc):
        # Ensure attempting to store a block with a read-only transaction fails
        # with the expected error.
        def _sub_test_store_in_read_only(tx):
            want_err_code = database.ErrorCode.ErrTxNotWritable
            for block in tx.blocks:
                with self.assertRaises(database.DBError) as cm:
                    tx.store_block(block)
                self.assertEqual(cm.exception.c, want_err_code)

        tc.db.view(_sub_test_store_in_read_only)

        # Populate the database with loaded blocks and ensure all of the data
        # fetching APIs work properly on them within the transaction before a
        # commit or rollback.  Then, force a rollback so the code below can
        # ensure none of the data actually gets stored.
        class forceRollbackError(Exception):
            """force rollback"""
            pass

        def _sub_test_store_and_rollback_in_read_write(tx):
            # Store all blocks in the same transaction.
            for block in tc.blocks:
                tx.store_block(block)

            # Ensure attempting to store the same block again, before the
            # transaction has been committed, returns the expected error.
            want_err_code = database.ErrorCode.ErrBlockExists
            for block in tx.blocks:
                with self.assertRaises(database.DBError) as cm:
                    tx.store_block(block)
                self.assertEqual(cm.exception.c, want_err_code)

            # Ensure that all data fetches from the stored blocks before
            # the transaction has been committed work as expected
            self._test_fetch_block_io(tc, tx)

            raise forceRollbackError

        with self.assertRaises(forceRollbackError) as cm:
            tc.db.update(_sub_test_store_and_rollback_in_read_write)
        self.assertIsInstance(cm.exception, forceRollbackError)

        # Ensure rollback was successful
        def _sub_test_rollback_successful(tx):
            self._test_fetch_block_io_missing(tc, tx)

        tc.db.view(_sub_test_rollback_successful)

        # Populate the database with loaded blocks and ensure all of the data
        # fetching APIs work properly.
        def _sub_test_populate_with_loaded_blocks(tx):
            # Store a bunch of blocks in the same transaction.
            for block in tc.blocks:
                tx.store_block(block)

            # Ensure attempting to store the same block again while in the
            # same transaction, but before it has been committed, returns
            # the expected error.
            want_err_code = database.ErrorCode.ErrBlockExists
            for block in tc.blocks:
                with self.assertRaises(database.DBError) as cm:
                    tx.store_block(block)
                self.assertEqual(cm.exception.c, want_err_code)

            # Ensure that all data fetches from the stored blocks before
            # the transaction has been committed work as expected.
            self._test_fetch_block_io(tc, tx)

        tc.db.update(_sub_test_populate_with_loaded_blocks)

        # Ensure all data fetch tests work as expected using a managed
        # read-only transaction after the data was successfully committed
        # above.
        def _sub_test_read_only_fetch_successful(tx):
            self._test_fetch_block_io(tc, tx)

        tc.db.view(_sub_test_read_only_fetch_successful)

        # Ensure all data fetch tests work as expected using a managed
        # read-write transaction after the data was successfully committed
        # above.
        def _sub_test_read_write_correct_after_commit(tx):
            self._test_fetch_block_io(tc, tx)

            # Ensure attempting to store existing blocks again returns the
            # expected error.  Note that this is different from the
            # previous version since this is a new transaction after the
            # blocks have been committed.
            want_err_code = database.ErrorCode.ErrBlockExists
            for block in tc.blocks:
                with self.assertRaises(database.DBError) as cm:
                    tx.store_block(block)
                self.assertEqual(cm.exception.c, want_err_code)

        tc.db.update(_sub_test_read_write_correct_after_commit)

        return

    # testClosedTxInterface ensures that both the metadata and block IO API
    # functions behave as expected when attempted against a closed transaction.
    def _test_closed_tx_interface(self, tc: TestContext, tx: database.Tx):
        want_err_code = database.ErrorCode.ErrTxClosed
        bucket = tx.metadata()
        cursor = tx.metadata().cursor()
        bucket_name = b"closedtxbucket"
        key_name = b"closedtxkey"

        # ------------
        # Metadata API
        # ------------

        # Ensure that attempting to get an existing bucket returns nil when the
        # transaction is closed.
        self.assertIsNone(bucket.bucket(bucket_name))

        # Ensure CreateBucket returns expected error.
        with self.assertRaises(database.DBError) as cm:
            bucket.create_bucket(bucket_name)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure CreateBucketIfNotExists returns expected error.
        with self.assertRaises(database.DBError) as cm:
            bucket.create_bucket_if_not_exists(bucket_name)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure Delete returns expected error.
        with self.assertRaises(database.DBError) as cm:
            bucket.delete(key_name)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure DeleteBucket returns expected error.
        with self.assertRaises(database.DBError) as cm:
            bucket.delete_bucket(bucket_name)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure ForEach returns expected error.
        with self.assertRaises(database.DBError) as cm:
            for _, _ in bucket.for_each2():
                pass
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure ForEachBucket returns expected error.
        with self.assertRaises(database.DBError) as cm:
            for _, _ in bucket.for_each_bucket2():
                pass
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure Get returns expected error.
        with self.assertRaises(database.DBError) as cm:
            bucket.get(key_name)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure Put returns expected error.
        with self.assertRaises(database.DBError) as cm:
            bucket.put(key_name, b"test")
        self.assertEqual(cm.exception.c, want_err_code)

        # -------------------
        # Metadata Cursor API
        # -------------------

        # Ensure attempting to get a bucket from a cursor on a closed tx gives
        # back nil.
        self.assertIsNone(cursor.get_bucket())

        # Ensure Cursor.Delete returns expected error.
        with self.assertRaises(database.DBError) as cm:
            cursor.delete()
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure Cursor.First on a closed tx returns false and nil key/value.
        self.assertFalse(cursor.first())
        self.assertIsNone(cursor.key())
        self.assertIsNone(cursor.value())

        # Ensure Cursor.Last on a closed tx returns false and nil key/value.
        self.assertFalse(cursor.last())
        self.assertIsNone(cursor.key())
        self.assertIsNone(cursor.value())

        # Ensure Cursor.Next on a closed tx returns false and nil key/value.
        self.assertFalse(cursor.next())
        self.assertIsNone(cursor.key())
        self.assertIsNone(cursor.value())

        # Ensure Cursor.Prev on a closed tx returns false and nil key/value.
        self.assertFalse(cursor.prev())
        self.assertIsNone(cursor.key())
        self.assertIsNone(cursor.value())

        # Ensure Cursor.Seek on a closed tx returns false and nil key/value.
        self.assertFalse(cursor.seek(b""))
        self.assertIsNone(cursor.key())
        self.assertIsNone(cursor.value())

        # ---------------------
        # Non-bulk Block IO API
        # ---------------------

        # Test the individual block APIs one block at a time to ensure they
        # return the expected error.  Also, build the data needed to test the
        # bulk APIs below while looping.
        all_block_hashes = []
        all_block_regions = []
        for block in tc.blocks:
            block_hash = block.hash()
            all_block_hashes.append(block)

            tx_locs = block.tx_loc()

            # Ensure StoreBlock returns expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.store_block(block)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure FetchBlock returns expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block(block_hash)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure FetchBlockHeader returns expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_header(block_hash)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure the first transaction fetched as a block region from
            # the database returns the expected error.
            region = database.BlockRegion(
                hash=block_hash, offset=tx_locs[0].tx_start, len=tx_locs[0].tx_len
            )
            all_block_regions.append(region)

            with self.assertRaises(database.DBError) as cm:
                tx.fetch_block_region(region)
            self.assertEqual(cm.exception.c, want_err_code)

            # Ensure HasBlock returns expected error.
            with self.assertRaises(database.DBError) as cm:
                tx.has_block(block_hash)
            self.assertEqual(cm.exception.c, want_err_code)

        # -----------------
        # Bulk Block IO API
        # -----------------

        # Ensure FetchBlocks returns expected error.
        # Ensure FetchBlocks returns expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_blocks(all_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure FetchBlockHeaders returns expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_headers(all_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure FetchBlockRegions returns expected error.
        with self.assertRaises(database.DBError) as cm:
            tx.fetch_block_regions(all_block_regions)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure HasBlocks returns false for all blocks.
        with self.assertRaises(database.DBError) as cm:
            tx.has_blocks(all_block_hashes)
        self.assertEqual(cm.exception.c, want_err_code)

        # ---------------
        # Commit/Rollback
        # ---------------

        # Ensure that attempting to rollback or commit a transaction that is
        # already closed returns the expected error.

        with self.assertRaises(database.DBError) as cm:
            tx.rollback()
        self.assertEqual(cm.exception.c, want_err_code)

        with self.assertRaises(database.DBError) as cm:
            tx.commit()
        self.assertEqual(cm.exception.c, want_err_code)

        return

    # testTxClosed ensures that both the metadata and block IO API functions behave
    # as expected when attempted against both read-only and read-write
    # transactions.
    def _test_tx_closed(self, tc: TestContext):
        bucket_name = b"closedtxbucket"
        key_name = b"closedtxkey"

        # Start a transaction, create a bucket and key used for testing, and
        # immediately perform a commit on it so it is closed.
        tx = tc.db.begin(writeable=True)

        # TODO defer rollbackOnPanic

        tx.metadata().create_bucket(bucket_name)
        tx.metadata().put(key_name, b'test')
        tx.commit()

        # Ensure invoking all of the functions on the closed read-write
        # transaction behave as expected.
        self._test_closed_tx_interface(tc, tx)

        # Repeat the tests with a rolled-back read-only transaction.
        tx = tc.db.begin(writeable=False)

        # TODO defer rollbackOnPanic

        tx.rollback()

        # Ensure invoking all of the functions on the closed read-only
        # transaction behave as expected.
        self._test_closed_tx_interface(tc, tx)

        return

    # package which require state in the database for the given database type.
    def test_interface(self, db: database.DB):
        # Create a test context to pass around.
        context = TestContext(db=db)

        # Load the test blocks and store in the test context for use throughout
        # the tests.
        blocks = self._load_blocks(blockDataFile, blockDataNet)
        context.blocks = blocks

        # Test the transaction metadata interface including managed and manual
        # transactions as well as buckets.
        self._test_metadata_tx_interface(context)

        # Test the transaction block IO interface using managed and manual
        # transactions.  This function leaves all of the stored blocks in the
        # database since they're used later.
        self._test_block_io_tx_interface(context)

        # Test all of the transaction interface functions against a closed
        # transaction work as expected.
        self._test_tx_closed(context)

        # TOADD Test the database properly supports concurrency.
        # TOADD testConcurrentClose.

        return
