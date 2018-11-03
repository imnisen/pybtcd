from .error import *
from .inteface import *


# Driver defines a structure for backend drivers to use when they registered
# themselves as a backend which implements the DB interface.
class Driver:
    def __init__(self, db_type, ):
        # DbType is the identifier used to uniquely identify a specific
        # database driver.  There can be only one driver with the same name.
        self.db_type = db_type

    # Create is the function that will be invoked with all user-specified
    # arguments to create the database.  This function must return
    # ErrDbExists if the database already exists.
    def create(self, *args) -> DB:
        pass

    # Open is the function that will be invoked with all user-specified
    # arguments to open the database.  This function must return
    # ErrDbDoesNotExist if the database has not already been created.
    def open(self, *args) -> DB:
        pass

    # UseLogger uses a specified Logger to output package logging info.
    def use_logger(self, logger):
        pass


# driverList holds all of the registered database backends.
drivers = {}


# RegisterDriver adds a backend database driver to available interfaces.
# ErrDbTypeRegistered will be returned if the database type for the driver has
# already been registered.
def register_driver(driver: Driver):
    if driver.db_type in drivers:
        msg = "driver %s is already registered" % driver.db_type
        raise DBError(ErrorCode.ErrDbTypeRegistered, msg)

    drivers[driver.db_type] = driver
    return


# SupportedDrivers returns a slice of strings that represent the database
# drivers that have been registered and are therefore supported.
def supported_drivers():
    supported_db = []
    for drv in drivers:
        supported_db.append(drv.db_type)
    return supported_db


# Create initializes and opens a database for the specified type.  The
# arguments are specific to the database type driver.  See the documentation
# for the database driver for further details.
#
# ErrDbUnknownType will be returned if the the database type is not registered.
def create(db_type: str, *args) -> DB:
    if db_type not in drivers:
        msg = "driver %s is not registered" % db_type
        raise DBError(ErrorCode.ErrDbUnknownType, msg)

    drv = drivers[db_type]
    return drv.create(*args)


# Open opens an existing database for the specified type.  The arguments are
# specific to the database type driver.  See the documentation for the database
# driver for further details.
#
# ErrDbUnknownType will be returned if the the database type is not registered.
def open(db_type: str, *args) -> DB:
    if db_type not in drivers:
        msg = "driver %s is not registered" % db_type
        raise DBError(ErrorCode.ErrDbUnknownType, msg)

    drv = drivers[db_type]
    return drv.open(*args)
