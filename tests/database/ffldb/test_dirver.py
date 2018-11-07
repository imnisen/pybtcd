import unittest
import database
from database.ffldb import *
from tests.database.ffldb.test_interface import *
import tempfile

dbType = "ffldb"


class TestCreateOpenFail(unittest.TestCase):
    def test_create_open_fail(self):
        # TOADD parapllel

        # Ensure that attempting to open a database that doesn't exist returns
        # the expected error.
        want_err_code = database.ErrorCode.ErrDbDoesNotExist

        with self.assertRaises(database.DBError) as cm:
            database.open(dbType, "noexist", blockDataNet)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure that attempting to open a database with the wrong number of
        # parameters returns the expected error.
        with self.assertRaises(InvalidArgNumErr):
            database.open(dbType, 1, 2, 3)

        # Ensure that attempting to open a database with an invalid type for
        # the first parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.open(dbType, 1, blockDataNet)

        # Ensure that attempting to open a database with an invalid type for
        # the second parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.open(dbType, "noexist", "invalid")

        # Ensure that attempting to create a database with the wrong number of
        # parameters returns the expected error.
        with self.assertRaises(InvalidArgNumErr):
            database.create(dbType, 1, 2, 3)

        # Ensure that attempting to create a database with an invalid type for
        # the first parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.create(dbType, 1, blockDataNet)

        # Ensure that attempting to create a database with an invalid type for
        # the second parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.create(dbType, "noexist", "invalid")

        # Ensure operations against a closed database return the expected
        # error.
        tmp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(tmp_dir.name, "ffldb-createfail")
        tmp_dir.cleanup()
        db = database.create(dbType, db_path, blockDataNet)
        db.close()

        want_err_code = database.ErrorCode.ErrDbNotOpen
        with self.assertRaises(database.DBError) as cm:
            db.view(lambda tx: None)
        self.assertEqual(cm.exception.c, want_err_code)

        want_err_code = database.ErrorCode.ErrDbNotOpen
        with self.assertRaises(database.DBError) as cm:
            db.update(lambda tx: None)
        self.assertEqual(cm.exception.c, want_err_code)

        want_err_code = database.ErrorCode.ErrDbNotOpen
        with self.assertRaises(database.DBError) as cm:
            db.begin(False)
        self.assertEqual(cm.exception.c, want_err_code)

        want_err_code = database.ErrorCode.ErrDbNotOpen
        with self.assertRaises(database.DBError) as cm:
            db.begin(True)
        self.assertEqual(cm.exception.c, want_err_code)

        want_err_code = database.ErrorCode.ErrDbNotOpen
        with self.assertRaises(database.DBError) as cm:
            db.close()
        self.assertEqual(cm.exception.c, want_err_code)
