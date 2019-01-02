import time
import threading
import logging

_logger = logging.getLogger(__name__)


# This is an interface
# MedianTimeSource provides a mechanism to add several time samples which are
# used to determine a median time which is then used as an offset to the local
# clock.
class MedianTimeSource:
    # AdjustedTime returns the current time adjusted by the median time
    # offset as calculated from the time samples added by AddTimeSample.
    def adjusted_time(self) -> int:
        raise NotImplementedError

    # AddTimeSample adds a time sample that is used when determining the
    # median time of the added samples.
    def add_time_sample(self, id, time_val):
        raise NotImplementedError

    # Offset returns the number of seconds to adjust the local clock based
    # upon the median of the time samples added by AddTimeData.
    def offset(self) -> int:
        raise NotImplementedError


#
# # TODO
# # int64Sorter implements sort.Interface to allow a slice of 64-bit integers to
# # be sorted.
# class Int64Sorter(int):
#     pass


# maxAllowedOffsetSeconds is the maximum number of seconds in either
# direction that local clock will be adjusted.  When the median time
# of the network is outside of this range, no offset will be applied.
maxAllowedOffsetSecs = 70 * 60  # 1 hour 10 minutes

# similarTimeSecs is the number of seconds in either direction from the
# local clock that is used to determine that it is likley wrong and
# hence to show a warning.
similarTimeSecs = 5 * 60  # 5 minutes

# maxMedianTimeEntries is the maximum number of entries allowed in the
# median time data.  This is a variable as opposed to a constant so the
# test code can modify it.
maxMedianTimeEntries = 200


# medianTime provides an implementation of the MedianTimeSource interface.
# It is limited to maxMedianTimeEntries includes the same buggy behavior as
# the time offset mechanism in Bitcoin Core.  This is necessary because it is
# used in the consensus code.
class MedianTime(MedianTimeSource):
    def __init__(self, lock=None, known_ids=None, offsets=None, offset_secs=None, invalid_time_checked=None, ):
        """

        :param RWLOCK lock:
        :param map[string]struct{} known_ids:
        :param []int64 offsets:
        :param int64 offset_secs:
        :param bool invalid_time_checked:
        """
        self.lock = lock or threading.Lock()
        self.known_ids = known_ids or {}
        self.offsets = offsets or []
        self.offset_secs = offset_secs or 0
        self.invalid_time_checked = invalid_time_checked or False

    # AddTimeSample adds a time sample that is used when determining the median
    # time of the added samples.
    #
    # This function is safe for concurrent access and is part of the
    # MedianTimeSource interface implementation.
    def adjusted_time(self):
        with self.lock:
            now = int(time.time())
            return now + self.offset_secs

    # AddTimeSample adds a time sample that is used when determining the median
    # time of the added samples.
    #
    # This function is safe for concurrent access and is part of the
    # MedianTimeSource interface implementation.
    def add_time_sample(self, source_id, time_val):
        with self.lock:
            # Don't add time data from the same source.
            if source_id is self.known_ids:
                return
            self.known_ids[source_id] = {}

            now = int(time.time())
            offset_seconds = time_val - now
            num_offsets = len(self.offsets)

            # Check if the offsets if full
            if num_offsets == maxMedianTimeEntries and maxMedianTimeEntries > 0:
                self.offsets = self.offsets[1:]
                num_offsets -= 1

            # append this offset seconds
            self.offsets.append(offset_seconds)
            num_offsets += 1

            # sort offset seconds
            sorted_offsets = sorted(self.offsets)

            offset_duration = offset_seconds
            _logger.debug("Added time sample of %s (total: %s)" % (offset_duration, num_offsets))

            # NOTE: The following code intentionally has a bug to mirror the
            # buggy behavior in Bitcoin Core since the median time is used in the
            # consensus rules.
            #
            # In particular, the offset is only updated when the number of entries
            # is odd, but the max number of entries is 200, an even number.  Thus,
            # the offset will never be updated again once the max number of entries
            # is reached.

            # The median offset is only updated when there are enough offsets and
            # the number of offsets is odd so the middle value is the true median.
            # Thus, there is nothing to do when those conditions are not met.
            if num_offsets < 5 or num_offsets & 0x01 != 1:
                return

            # At this point the number of offsets in the list is odd, so the
            # middle value of the sorted offsets is the median.
            median = sorted_offsets[num_offsets // 2]

            # Set the new offset when the median offset is within the allowed
            # offset range.
            if abs(median) < maxAllowedOffsetSecs:
                self.offset_secs = median
            else:
                # The median offset of all added time data is larger than the
                # maximum allowed offset, so don't use an offset.  This
                # effectively limits how far the local clock can be skewed.
                self.offset_secs = 0

                if not self.invalid_time_checked:
                    self.invalid_time_checked = True

                    # Find if any time samples have a time that is close
                    # to the local time.
                    remote_hash_close_time = False
                    for offset in sorted_offsets:
                        if abs(offset) < similarTimeSecs:
                            remote_hash_close_time = True
                            break

                    if not remote_hash_close_time:
                        _logger.debug("Please check your date and time are correct!  btcd will not work " +
                                      "properly with an invalid time")

            _logger.debug("New time offset: %s" % self.offset_secs)
            return

            # Offset returns the number of seconds to adjust the local clock based upon the

    # median of the time samples added by AddTimeData.
    #
    # This function is safe for concurrent access and is part of the
    # MedianTimeSource interface implementation.
    def offset(self):
        with self.lock:
            return self.offset_secs
