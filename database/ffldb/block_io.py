# blockLocation identifies a particular block file and location.
class BlockLocation:
    def __init__(self, block_file_num=None, file_offset=None, block_len=None):
        """
        
        :param uint32 block_file_num:
        :param uint32 file_offset:
        :param uint32 block_len:
        """
        self.block_file_num = block_file_num or 0
        self.file_offset = file_offset or 0
        self.block_len = block_len or 0
