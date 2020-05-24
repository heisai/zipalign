import os
import struct
from log import get_logger
from config import *
import sys
import copy

logger = get_logger("zipentry")


temp_LocalHeaderRelOffse = 0
len_LocalHeader = 0 
bias = 0 
verify_falg = True


class LocalFileHeader(object):
    def __init__(self):

        self.local_file_header_signature = 0                                        # 文件头标识 (固定值0x04034b50)
        # 解压时遵循ZIP规范的最低版本
        self.version_needed_to_extract = 0
        self.general_purpose_bit_flag = 0                                           # 通用标志位
        self.compression_method = 0                                                 # 压缩方式
        # 最后修改时间（MS-DOS格式）
        self.last_mod_file_time = 0
        # 最后修改日期（MS-DOS格式）
        self.last_mod_file_date = 0
        # 冗余校验码
        self.crc_32 = 0
        # 压缩后的大小
        self.compressed_size = 0
        # 未压缩之前的大小
        self.uncompressed_size = 0
        # 文件名长度（n）
        self.file_name_length = 0
        # 扩展区长度（m）
        self.extra_field_length = 0
        self.file_name = ""                                                         # 文件名
        self.extra_field = b""                                                       # 扩展区

    def Read_LocalFile(self, fd):

        database = fd.read(kLFHLen)
        self.local_file_header_signature = struct.unpack("I", database[:4])[0]
        self.version_needed_to_extract = struct.unpack("H", database[4:6])[0]
        self.general_purpose_bit_flag = struct.unpack("H", database[6:8])[0]
        self.compression_method = struct.unpack("H", database[8:10])[0]
        self.last_mod_file_time = struct.unpack("H", database[10:12])[0]
        self.last_mod_file_date = struct.unpack("H", database[12:14])[0]
        self.crc_32 = struct.unpack("I", database[14:18])[0]
        self.compressed_size = struct.unpack("I", database[18:22])[0]
        self.uncompressed_size = struct.unpack("I", database[22:26])[0]
        self.file_name_length = struct.unpack("H", database[26:28])[0]
        self.extra_field_length = struct.unpack("H", database[28:30])[0]
        self.file_name = fd.read(self.file_name_length)
        if self.extra_field_length > 0:
            self.extra_field = fd.read(self.extra_field_length)
        # self.show_message()
        # logger.info("文件名: %s" % self.file_name)
    def write(self, fd):
        pass

    def show_message(self):
        logger.info("***************** Local file header 文件头: *****************")
        logger.info("文件头标识: %s" % hex(self.local_file_header_signature))
        logger.info("解压时遵循ZIP规范的最低版本: %s" % self.version_needed_to_extract)
        logger.info("通用标志位: %s" % self.general_purpose_bit_flag)
        logger.info("压缩方式: %s" % self.compression_method)
        logger.info("最后修改时间（MS-DOS格式）: %s" % self.last_mod_file_time)
        logger.info("最后修改日期（MS-DOS格式）: %s" % self.last_mod_file_date)
        logger.info("冗余校验码: %d:" % self.crc_32)
        logger.info("压缩后的大小: %s" % self.compressed_size)
        logger.info("未压缩之前的大小: %s" % self.uncompressed_size)
        logger.info("文件名长度（n）: %s" % self.file_name_length)
        logger.info("扩展区长度（m）:%s" % self.extra_field_length)
        logger.info("文件名: %s" % self.file_name)
        logger.info("扩展区: %s" % self.extra_field)

    def get_filenamelength(self):
        return self.file_name_length

    def get_extrafieldlength(self):
        return self.file_name_length


class CentralDirEntry(object):
    def __init__(self):
        #0x02014b50
        self.central_file_header_signature = 0  # 文件头标识 (固定值0x02014b50)
        self.mVersionMadeBy = 0                     # 高位字节表示文件属性信息的兼容性，低位字节表示压缩软件支持的ZIP规范版本
        self.mVersionToExtract = 0  # 解压时遵循ZIP规范的最低版本
        self.mGPBitFlag = 0  # 通用标志位
        self.mCompressionMethod = 0  # 压缩方式
        self.mLastModFileTime = 0  # 最后修改时间（MS-DOS格式）
        self.mLastModFileDate = 0  # 最后修改日期（MS-DOS格式）
        self.mCRC32 = 0  # 冗余校验码
        self.mCompressedSize = 0  # 压缩后的大小
        self.mUncompressedSize = 0  # 未压缩之前的大小
        self.mFileNameLength = 0  # 文件名长度（n）
        self.mExtraFieldLength = 0  # 扩展区长度（m）
        self.mFileCommentLength = 0  # 文件注释长度（k）
        self.mDiskNumberStart = 0  # 文件开始位置的磁盘编号
        self.mInternalAttrs = 0  # 内部文件属性
        self.mExternalAttrs = 0  # 外部文件属性
        self.mLocalHeaderRelOffset = 0  # 对应 [local file header] 的偏移位置
        self.mFileName = ""  # 目录文件名
        self.mExtraField = ""  # 扩展域
        self.mFileComment = ""  # 文件注释内容

    def isCompressed(self):
        # print(self.Central_Dir.get_CompressionMethod())
        # print(kCompressStored)
        return self.mCompressionMethod != kCompressStored

    def __decodeExtra(self):
        # Try to decode the extra field.
        extra = self.mExtraField
       
        while len(extra) >= 4:
            tp, ln = struct.unpack('<HH', extra[:4])
            if ln+4 > len(extra):
                raise Exception(
                    "Corrupt extra field %04x (size=%d)" % (tp, ln))
            if tp == 0x0001:
                if ln >= 24:
                    counts = struct.unpack('<QQQ', extra[4:28])
                elif ln == 16:
                    counts = struct.unpack('<QQ', extra[4:20])
                elif ln == 8:
                    counts = struct.unpack('<Q', extra[4:12])
                elif ln == 0:
                    counts = ()
                else:
                    raise Exception(
                        "Corrupt extra field %04x (size=%d)" % (tp, ln))

                idx = 0

                # ZIP64 extension (large files and/or large archives)
                # print(counts[idx])
                if self.mUncompressedSize in (0xffffffffffffffff, 0xffffffff):
                    self.mUncompressedSize = counts[idx]
                    idx += 1

                if self.mCompressedSize == 0xFFFFFFFF:
                    self.mCompressedSize = counts[idx]
                    idx += 1

                if self.mLocalHeaderRelOffset == 0xffffffff:
                    # old = self.mLocalHeaderRelOffset
                    self.mLocalHeaderRelOffset = counts[idx]
                    idx += 1

            extra = extra[ln+4:]


           

    def Read_CentralDir(self, fd):
    
        padding = 0 

        database = fd.read(FileheaderLen)
        
        (   self.central_file_header_signature, 
            self.mVersionMadeBy, 
            self.mVersionToExtract, 
            self.mGPBitFlag, 
            self.mCompressionMethod,
            self.mLastModFileTime, 
            self.mLastModFileDate ) = struct.unpack("IHHHHHH", database[:16])
        (   self.mCRC32, 
            self.mCompressedSize,
            self.mUncompressedSize,
            self.mFileNameLength, 
            self.mExtraFieldLength, 
            self.mFileCommentLength,
            self.mDiskNumberStart, 
            self.mInternalAttrs ) = struct.unpack("IIIHHHHH", database[16:38])
        (   self.mExternalAttrs, 
            self.mLocalHeaderRelOffset )= struct.unpack("II", database[38:46])

      
        self.mFileName = fd.read(self.mFileNameLength)
        self.mExtraField = fd.read(self.mExtraFieldLength)
        self.mFileComment = fd.read(self.mFileCommentLength)
        # print("*******************************************")
        # print(self.mLocalHeaderRelOffset)
        # if self.mLocalHeaderRelOffset == 4294967295:
        #     sys.exit(1)
        
        self.__decodeExtra()
        # print("*******************************************")

       
    def get_CompressionMethod(self):
        return self.mCompressionMethod

    def show_message(self):
        logger.info( "************************* 中心目录区:***************************")
        logger.info("文件头标识 : %s" % hex(self.central_file_header_signature))
        logger.info("文件注释长度（k） : %s" % self.mFileCommentLength)
        logger.info("文件开始位置的磁盘编号: %s" % self.mDiskNumberStart)
        logger.info("内部文件属性: %s" % self.mInternalAttrs)
        logger.info("外部文件属性: %s" % self.mExternalAttrs)
        logger.info("对应 [local file header] 的偏移位置: %s" %
                    self.mLocalHeaderRelOffset)
        logger.info("目录文件名: %s" % self.mFileName)
        logger.info("扩展域: %s" % self.mExtraField)
        logger.info("文件注释内容 : %s" % self.mFileComment)

class zip_entry(object):
    def __init__(self):
        self.Central_Dir = CentralDirEntry()
        self.LocalFileHeader = LocalFileHeader()
        self.localoffet_out32 = 0
 
       
#  zipentry.initFromCDE(self.fd, self.localoffet_out32)

    def initFromCDE(self, fd):
        # 读取中心目录区数据
        global temp_LocalHeaderRelOffse, len_LocalHeader
        # (temp_LocalHeaderRelOffse, len_LocalHeader,padding) = self.Central_Dir.Read_CentralDir(fd,verify_falg)
        self.Central_Dir.Read_CentralDir(fd)
        
        # 记录当前中心目录区的偏移量
        offset = fd.tell()
        #根据中心目录区数据 获取 Local file header 数据
        fd.seek(self.Central_Dir.mLocalHeaderRelOffset, 0)
        self.LocalFileHeader.Read_LocalFile(fd)
        fd.seek(offset, 0)
      
    def getfilename(self):
        return self.LocalFileHeader.file_name
    def isCompressed(self):
        return self.Central_Dir.get_CompressionMethod() != kCompressStored

    def getFileOffset(self):
        # print(self.Central_Dir.mLocalHeaderRelOffset, kLFHLen,
        #       self.LocalFileHeader.file_name_length, self.LocalFileHeader.extra_field_length)
        return self.Central_Dir.mLocalHeaderRelOffset + kLFHLen + self.LocalFileHeader.file_name_length + self.LocalFileHeader.extra_field_length

    def setLFHOffset(self, offset):
        self.Central_Dir.mLocalHeaderRelOffset = offset

    def addPadding(self, padding):
        if padding <= 0:
            return False
        if self.LocalFileHeader.extra_field_length > 0:
            self.extra_field += ('0' * padding)
            self.LocalFileHeader.extra_field_length += padding
        else:
            self.extra_field = '0' * padding
            self.LocalFileHeader.extra_field_length = padding
        return True

    def getCompressedLen(self):
        return self.Central_Dir.mCompressedSize
