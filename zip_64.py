'''
@Author: heisai
@Date: 2020-04-07 23:12:22
@LastEditTime: 2020-05-23 17:07:43
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \zipalign\zip_64.py
'''
import struct
import os
from log import get_logger

logger = get_logger("zip_64")

class Zip_Record(object):
    def __init__(self):
        self.signature = 0              #4 bytes
        self.size_dirrecord = 0         #8 bytes
        self.version = 0                #2 bytes
        self.version_extract = 0        # 2 bytes
        self.number_disk = 0            #4 bytes
        self.start_central = 0          # 4 bytes
        self.central_directory = 0      # 8 bytes
        self.totalfiles = 0             # 8 bytes
        self.size_central = 0           # 8 bytes
        self.central_offet = 0          # 8 bytes
        self.extensible_data = b""       
        






        # self.totalfiles = 0   # 文件总数
        # self.central_offet = 0  # 中心目录偏移量
        
    def read_record(self,data):

        self.signature = struct.unpack("I", data[:4])[0]
        self.size_dirrecord = struct.unpack("Q", data[4:12])[0]
        self.version = struct.unpack("H", data[12:14])[0]
        self.version_extract = struct.unpack("H", data[14:16])[0]
        self.number_disk = struct.unpack("I", data[16:20])[0]
        self.start_central = struct.unpack("I", data[20:24])[0]
        self.central_directory = struct.unpack("Q", data[24:32])[0]
        self.totalfiles   = struct.unpack("Q", data[32:40])[0]
        self.size_central = struct.unpack("Q", data[40:48])[0]
        self.central_offet = struct.unpack("Q", data[48:])[0]
       
       
        self.showmessage()

        return (self.central_offet, self.totalfiles, self.size_central)

    def write_record(self,fd):
        data = struct.pack('<IQHHIIQQQQ', self.signature,
                           self.size_dirrecord,
                           self.version,
                           self.version_extract,
                           self.number_disk,
                           self.start_central,
                           self.central_directory,
                           self.totalfiles,
                           self.size_central,
                           self.central_offet)
        fd.write(data)
        if len(self.extensible_data) >0:
            fd.write(self.extensible_data)
    def showmessage(self):
        logger.info("**************************Zip64中央目录记录的结尾********************")
        logger.info("文件总数%d" % self.totalfiles)
        logger.info("中心目录偏移量%d" % self.central_offet)
        print(
            self.signature,
            self.size_dirrecord,
            self.version,
            self.version_extract,
            self.number_disk,
            self.start_central,
            self.central_directory,
            self.totalfiles,
            self.size_central,
            self.central_offet
        )

class  Zip_Locator(object):
    def __init__(self):
        self.signature = 0  
        self.size_dirrecord = 0         
        self.start_central = 0               
        self.total_disk = 0      
    def read_locator(self,data):
        database = struct.unpack("IIQI", data)
        (self.signature,
        self.size_dirrecord,
        self.start_central,
        self.total_disk) = struct.unpack("IIQI",data)

        
        self.sowmessage()

    def set_start_central(self,size_central,central_offet):
        self.start_central = size_central + central_offet

    def write_locator(self,fd):
        data = struct.pack('<IIQI', self.signature,
                           self.size_dirrecord,
                           self.start_central,
                           self.total_disk)
        fd.write(data)


    def sowmessage(self):
        print("\n*********************Zip64 end of central directory locator:*********************\n")
        print(
            self.signature,
            self.size_dirrecord,
            self.start_central,
            self.total_disk
        )
