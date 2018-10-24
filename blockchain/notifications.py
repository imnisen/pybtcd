from enum import IntEnum, auto


# NotificationType represents the type of a notification message.
class NotificationType(IntEnum):
    # NTBlockAccepted indicates the associated block was accepted into
    # the block chain.  Note that this does not necessarily mean it was
    # added to the main chain.  For that, use NTBlockConnected.
    NTBlockAccepted = 0

    # NTBlockConnected indicates the associated block was connected to the
    # main chain.
    NTBlockConnected = auto()

    # NTBlockDisconnected indicates the associated block was disconnected
    # from the main chain.
    NTBlockDisconnected = auto()

    def __str__(self):
        return self.name



# TODO  NotificationCallback
class NotificationCallback:
    pass


# Notification defines notification that is sent to the caller via the callback
# function provided during the call to New and consists of a notification type
# as well as associated data that depends on the type as follows:
# 	- NTBlockAccepted:     *btcutil.Block
# 	- NTBlockConnected:    *btcutil.Block
# 	- NTBlockDisconnected: *btcutil.Block
class Notification:
    def __init__(self, type, data):
        """

        :param NotificationType type:
        :param data:
        """
        self.type = type
        self.data = data


# TOADD TODO Add some methods to blockchain