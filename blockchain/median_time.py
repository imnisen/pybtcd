import time

# This is an interface
# MedianTimeSource provides a mechanism to add several time samples which are
# used to determine a median time which is then used as an offset to the local
# clock.
class MedianTimeSource:
    # AdjustedTime returns the current time adjusted by the median time
    # offset as calculated from the time samples added by AddTimeSample.
    def adjusted_time(self):
        pass

    # AddTimeSample adds a time sample that is used when determining the
    # median time of the added samples.
    def add_time_sample(self, id, time_val):
        pass

    # Offset returns the number of seconds to adjust the local clock based
    # upon the median of the time samples added by AddTimeData.
    def offset(self):
        pass

#
# # TODO
# # int64Sorter implements sort.Interface to allow a slice of 64-bit integers to
# # be sorted.
# class Int64Sorter(int):
#     pass


# medianTime provides an implementation of the MedianTimeSource interface.
# It is limited to maxMedianTimeEntries includes the same buggy behavior as
# the time offset mechanism in Bitcoin Core.  This is necessary because it is
# used in the consensus code.
class MedianTime(MedianTimeSource):
    def __init__(self, lock, known_ids, offsets, offset_secs, invalid_time_checked):
        """

        :param RWLOCK lock:
        :param map[string]struct{} known_ids:
        :param []int64 offsets:
        :param int64 offset_secs:
        :param bool invalid_time_checked:
        """
        self.lock = lock
        self.known_ids = known_ids
        self.offsets = offsets
        self.offset_secs = offset_secs
        self.invalid_time_checked = invalid_time_checked

    # AddTimeSample adds a time sample that is used when determining the median
    # time of the added samples.
    #
    # This function is safe for concurrent access and is part of the
    # MedianTimeSource interface implementation.
    def adjusted_time(self):
        with self.lock:
            now = int(time.time)
            return now + self.offset_secs


    # AddTimeSample adds a time sample that is used when determining the median
    # time of the added samples.
    #
    # This function is safe for concurrent access and is part of the
    # MedianTimeSource interface implementation.
    def add_time_sample(self, id, time_val):
        pass

    # Offset returns the number of seconds to adjust the local clock based upon the
    # median of the time samples added by AddTimeData.
    #
    # This function is safe for concurrent access and is part of the
    # MedianTimeSource interface implementation.
    def offset(self):
        pass
