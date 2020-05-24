

import os 
import struct

from  log import get_logger
import traceback
from config import *
import sys
import  copy
from zip_64 import* 
from zipentry import *
logger = get_logger("zipalign")

def track_error():
    error_message=""
    (type,value,trace) = sys.exc_info()
    logger.error("**************************************************************")
    logger.error("Error_Type:\t%s\n"%type)
    logger.error("Error_Value:\t%s\n"%value)
    logger.error("%-40s %-20s %-20s %-20s\n"%("Filename", "Function","Linenum", "Source"))
    for filename, linenum, funcname, source in traceback.extract_tb(trace):
        logger.info("%-40s %-20s %-20s%-20s" % (os.path.basename(filename),funcname,linenum, source))
    logger.error("**************************************************************")




    
    
class End_Central_Dir(object):
    def __init__(self):
        self.dir_signtrue = 0               #中心目录结束标识 (固定值0x06054b50)
        self.number_disk = 0                #当前磁盘编号
        self.number_disk_start = 0          #中心目录开始位置的磁盘编号
        self.total_entry_disk = 0           #中心目录开始位置的磁盘编号
        self.total_entry_central = 0        #该磁盘上所记录的中心目录数量
        self.size_central = 0               #中心目录大小
        self.offset_central_disk = 0        #中心目录开始位置相对于.ZIP archive开始的位移
        self.comment_length = 0             #ZIP文件注释内容长度（n）
        self.comment = ""                   #ZIP文件注释内容
    def init_data(self,data):
      
        
        database = struct.unpack('iHHHHiiH',data[:22])

        self.dir_signtrue, self.number_disk, self.number_disk_start, self.total_entry_disk ,self.total_entry_central, self.size_central, self.offset_central_disk, self.comment_length = database    
        if self.comment_length > 0:
            self.comment = struct.unpack('%ds'%self.comment_length, data[22:self.comment_length])
        #  将负数转换成 整数
        self.offset_central_disk &= 0xFFFFFFFF
        # print("******************************************")
        # print(database)
        # print("******************************************")
        # self.showmessage()
    #获取中心目录开始位置（对于.ZIP archive开始的位移）
    def start_central(self):
        return  self.offset_central_disk
    def total_entry_num(self):
        return self.total_entry_central

    def showmessage(self):
        logger.info("**************************中心目录结束标识*************************************")
        logger.info("中心目录结束标识 (固定值0x06054b50):%s" % hex(self.dir_signtrue))
        logger.info("当前磁盘编号 :%s" % self.number_disk)
        logger.info("中心目录开始位置的磁盘编号:%s"%self.number_disk_start)
        logger.info("中心目录开始位置的磁盘编号:%s" % self.total_entry_disk)
        logger.info("该磁盘上所记录的中心目录数量:%s" % self.total_entry_central)
        logger.info("中心目录大小:%s" % self.size_central)
        logger.info("中心目录开始位置相对于.ZIP archive开始的位移:%s" %self.offset_central_disk)
        logger.info("ZIP文件注释内容长度（n）:%s" % self.comment_length)
        logger.info(" ZIP文件注释内容 %s" % self.comment)
    

def copyAndAlign(zipin, zipout, alignment):
    bias = 0 
    for index ,entry in  enumerate(zipin.Entry_List):
        padding = 0
        if entry.isCompressed():
            pass
        else:
            newOffset = entry.getFileOffset() + bias
            # logger.info("newOffset: %d"% newOffset)
            # logger.info((alignment - (newOffset % alignment)) % alignment)
            padding = (alignment - (newOffset % alignment)) % alignment
        #将 zipin 的 Local file header 信息 以及 数据区 写入文件
        # logger.info("文件索引: %s" %(index))
        zipout.addpartentry(zipin, entry, padding)
        bias += padding

    
    #  初始化 中心目录结束记录 数据
    zipout.init_enddir(zipin,zipout.fd.tell())
    # zipout.zip_blockdata = zipin.zip_blockdata
    zipout.flushdata(zipin)




class M_Zipfile(object):
    def __init__(self, filename, mode="rb", verify_falg = True):
        self.fd = open(filename, mode)
        self.ECD = End_Central_Dir()
        self.zip_record = None
        self.zip_locator = None 
        self.start_central = 0                  #获取中心目录开始位置
        self.total_entry_central = 0            # 该磁盘上所记录的中心目录数量

        self.Zip_64 = False   # True: 2G以上  False: 2G 以下
        self.zip64_blocklen = 0
        self.zip_blockdata = None
        self.verify_falg = verify_falg
        

        self.Entry_List = list()
        if mode == "rb":
            self.readmode()
        else:
            self.zip_record = Zip_Record()
            self.zip_locator = Zip_Locator()
            self.writemode()
            

    def __del__(self):
        self.fd.close()

    def readmode(self):
        self.__StartCentralDir()
        self.zip64_32()
        self.__read_central_dir()
    '''

    '''
    def writemode(self):
       pass



    '''
        找到中心目录结束记录, 以及中心目录偏移量, 
        这里大于2G的包会存在, 中心目录数 大于66535, 所以获取中心目录数据 不能依据 这个 为准. 

    '''

    def __StartCentralDir(self):

        seekStart = 0
        readAmount = 0
        self.fd.seek(0,2)  # 获取文件大小
        fileLength = self.fd.tell()
        logger.info(fileLength)

        if fileLength > Zip64CenSearch:
            seekStart = fileLength - Zip64CenSearch
            readAmount = Zip64CenSearch
        else:
            seekStart = 0
            readAmount = fileLength
        self.fd.seek(seekStart, 0)
        buf = self.fd.read(readAmount)

        for  offset, data  in enumerate(buf):
            if offset + 4 > len(buf)-1:
                break
            signature = struct.unpack('i', buf[offset:offset+4])[0]
            if signature == Zip64Record_Signature:
                self.zip_record = Zip_Record()
                data = buf[offset:offset+56]
                (temp_start_central ,  temp_total_entry_central, temp_central_size) = self.zip_record.read_record(data)

            elif signature == Zip64Locator_Signature:
                data = buf[offset:offset+20]
                self.zip_locator = Zip_Locator()
                self.zip_locator.read_locator(data)
                self.zip_locator.set_start_central(
                self.zip_record.size_central, self.zip_record.central_offet)
            elif signature == kSignature:
                data = buf[offset:]
                self.ECD.init_data(data)
                self.start_central = self.ECD.start_central()              
                self.total_entry_central = self.ECD.total_entry_num()
                break
           
        
        if self.zip_record != None:
            # 计算 [archive decryption header]  [archive extra data record]  归档大小
            concat = fileLength - 22 - temp_central_size - temp_start_central - 56 - 20
            self.start_central = temp_start_central + concat
            self.total_entry_central = temp_total_entry_central
    def zip64_32(self):
        if  self.zip_record:
            logger.error("zip_64的zip结构:")
            self.zip_record.showmessage()
        else:
            # print("zip_32的zip结构")
            logger.info("zip_32的zip结构")
    def __Zip64ECD(self,data):
        total_files = struct.unpack('Q', data[24:32])
        central_offset = struct.unpack('Q', data[48:56])
        # print("文件总数:", total_files)
        # print("中心目录偏移:", central_offset)

        

    def __read_central_dir(self):

        '''
        将中心目录区数据, 以及 Local file header  数据 保存到zipentry 对象中
        '''
        # self.total_entry_central  文件总数
        # self.start_central 偏移量
        self.fd.seek(self.start_central, 0)
        filenum = 0 
        for entry in range(self.total_entry_central):
            zipentry = zip_entry()
            padding = zipentry.initFromCDE(self.fd)
            self.Entry_List.append(zipentry)
            # print(entry)
            filenum = entry

        
        
        logger.info("文件总数:%d" %filenum)
        buf = self.fd.read()
       
        self.zip_blockdata = copy.deepcopy(buf)
      
        for index, data  in enumerate(buf):
            if index + 4 > len(buf)-1:
                break
            head = struct.unpack('i', buf[index:index+4])[0]
            if head == kSignature:
                self.zip64_blocklen = index
                # logger.info("zip 解析成功. 中心目录结束标识:%s" % hex(head))
                # logger.info("文件结束距离Zip64偏移: %d" % index)

        # Signature = struct.unpack('I', self.fd.read(4))[0]
        # if Signature != kSignature:
        #     raise Exception("zip 解析失败")
        # else:
        #     logger.info("zip 解析成功. 中心目录结束标识:%s" % hex(Signature))

       

    '''
    将中心目录区的数据, 以及中心目录结束记录 的数据写入
    '''

    def flushdata(self, zipin):
        for entry in self.Entry_List:
            self.Write_Central_Dir(entry)

        logger.info("------------------------------------------")
        logger.info("当前索引")
        



        '''
        写入 Zip64 end of central directory record   56个字节(不包括扩展区)
            解析 该段数据
           

        写入 Zip64 end of central directory locator  20个字节 固定

        写入 End of central directory record         22个字节 (不包括注释)
            修改的数据有四个:
                1:该磁盘上所记录的核心目录数量
                2:核心目录结构总数
                3:核心目录的大小
                4:核心目录开始位置相对位移
            (1): 小于2G:
                以上4个不变化
            (2): 大于2G:
                 1:该磁盘上所记录的核心目录数量   默认是 66535
                 2:核心目录结构总数              默认是 66535
                 3:核心目录的大小                4个字节 基本不会超过
                 4:核心目录开始位置相对位移       基本是一个 负数



        '''
        current_pos = self.fd.tell()
        # 获取中心你目录的大小
        self.ECD.size_central = current_pos - self.ECD.offset_central_disk
        if zipin.zip_record !=None:
            self.zip_record.size_central = current_pos - self.zip_record.central_offet
             # 获取Zip64 end of central directory locator 的偏移量
            self.zip_locator.start_central = current_pos
            # logger.info("-------------------------------------------")
            # logger.info(self.ECD.size_central)
            # logger.info(self.zip_record.size_central)
            # logger.info(self.ECD.offset_central_disk)
            # logger.info(self.zip_record.central_offet)
            # logger.info(self.zip_locator.start_central)
            # logger.info("-------------------------------------------")
            # self.Write_EndCentral_Dir()
       
            self.zip_record.write_record(self.fd)
            self.zip_locator.write_locator(self.fd)
        # logger.info("-------------------------------------------")
        # logger.info(self.ECD.size_central)
        # logger.info(self.ECD.offset_central_disk)
        # logger.info("-------------------------------------------")
        self.Write_EndCentral_Dir()
        self.fd.flush()

    def Write_Central_Dir(self,entry):


        '''
        以上三项数据大于 pow(2,31) 默认记录为 0xffffffff, 真实数据写入 mExtraField 扩展区
        1: mUncompressedSize                文件不压缩的大小
        2: mCompressedSize                  文件压缩后的大小
        3: mLocalHeaderRelOffset            LocalHeader 的偏移量
        结构如下:
        Value                   Size                 Description
        -----                   ----                    -----------
        (ZIP64) 0x0001          2 bytes             Tag for this "extra" block type(zip 64 默认)

        Size                    2 bytes             Size of this "extra" block  Original (扩展区的大小,是以上三项数据的大下)

        Size                    8 bytes             Original uncompressed file size   Compressed (文件压缩前的大小)
     
        Size                    8 bytes             Size of compressed data   Relative Header   (文件压缩前的大小)
      
        Offset                  8 bytes             Offset of local header record Disk Start    (文件的偏移量)

        Number                  4 bytes             Number of the disk on which this file starts 
        
        '''
        data = list()
        mExtraField = b""
        if entry.Central_Dir.mUncompressedSize >= pow(2,31):
            data.append(entry.Central_Dir.mUncompressedSize)
            entry.Central_Dir.mUncompressedSize = 0xffffffff
        if entry.Central_Dir.mCompressedSize >= pow(2,31):
            data.append(entry.Central_Dir.mCompressedSize)
            entry.Central_Dir.mCompressedSize = 0xffffffff
        if entry.Central_Dir.mLocalHeaderRelOffset >=pow(2,31):
            data.append(entry.Central_Dir.mLocalHeaderRelOffset)
            entry.Central_Dir.mLocalHeaderRelOffset = 0xffffffff
        if len(data) == 1:
            mExtraField = central_data = struct.pack('<HHQ', 1, 8, data[0])
        elif len(data) == 2:
            mExtraField = central_data = struct.pack('<HHQQ', 1, 16, data[0],data[1])
        elif len(data) == 3:
            mExtraField = central_data = struct.pack('<HHQQQ', 1, 24, data[0], data[1],data[2])
        else:
            mExtraField = b""
        entry.Central_Dir.mExtraFieldLength = len(mExtraField)
        central_data = struct.pack('<IHHHHHHIIIHHHHHII', entry.Central_Dir.central_file_header_signature,
                                   entry.Central_Dir.mVersionMadeBy,
                                   entry.Central_Dir.mVersionToExtract,
                                   entry.Central_Dir.mGPBitFlag,
                                   entry.Central_Dir.mCompressionMethod,
                                   entry.Central_Dir.mLastModFileTime,
                                   entry.Central_Dir.mLastModFileDate,
                                   entry.Central_Dir.mCRC32,
                                   entry.Central_Dir.mCompressedSize,
                                   entry.Central_Dir.mUncompressedSize,
                                   entry.Central_Dir.mFileNameLength,
                                   entry.Central_Dir.mExtraFieldLength,
                                   entry.Central_Dir.mFileCommentLength,
                                   entry.Central_Dir.mDiskNumberStart,
                                   entry.Central_Dir.mInternalAttrs,
                                   entry.Central_Dir.mExternalAttrs,
                                   entry.Central_Dir.mLocalHeaderRelOffset)
                                 
                                   


        
       
       

       
        # logger.info("写入中心目录数据: %s" % central_data)
        # logger.info("中心目录数据 size==>: %s" % len(central_data))


        start = self.fd.tell()
        self.fd.write(central_data)
        if entry.Central_Dir.mFileNameLength != 0 :
            # logger.info("文件名: %s" % entry.Central_Dir.mFileName)
            self.fd.write(entry.Central_Dir.mFileName)
        if entry.Central_Dir.mExtraFieldLength != 0:
            # logger.info("扩展区: %s" % entry.Central_Dir.mExtraField)
            self.fd.write(mExtraField)
        if entry.Central_Dir.mFileCommentLength != 0:
            # logger.info("注释: %s" % entry.Central_Dir.mFileComment)
            self.fd.write(entry.Central_Dir.mFileComment)
        end = self.fd.tell()
        # logger.info("中心总 size==>: %s" % str(end - start))


    def Write_EndCentral_Dir(self):
        # print("写入结束记录:")
        # print(self.ECD.dir_signtrue)
        # print(self.ECD.number_disk)
        # print(self.ECD.number_disk_start)
        # print(self.ECD.total_entry_disk)
        # print(self.ECD.total_entry_central)
        # print(self.ECD.size_central)
        # print(self.ECD.offset_central_disk)
        # print(self.ECD.comment_length)
        # print(self.ECD.comment)
       
        end_data = struct.pack("<IHHHHIIH", self.ECD.dir_signtrue,
                               self.ECD.number_disk,
                               self.ECD.number_disk_start,
                               self.ECD.total_entry_disk,
                               self.ECD.total_entry_central,
                               self.ECD.size_central,
                               self.ECD.offset_central_disk,
                               self.ECD.comment_length)   
        self.fd.write(end_data)
        if self.ECD.comment_length > 0:
            self.fd.write(self.ECD.comment)











    def init_enddir(self,InEcd,eocdPosn):
        if InEcd.zip_record !=None:
            self.zip_record.signature = InEcd.zip_record.signature
            self.zip_record.size_dirrecord = InEcd.zip_record.size_dirrecord
            self.zip_record.version = InEcd.zip_record.version
            self.zip_record.version_extract = InEcd.zip_record.version_extract
            self.zip_record.number_disk = InEcd.zip_record.number_disk
            self.zip_record.start_central = InEcd.zip_record.start_central

            #  已经计算过
            # self.zip_record.central_directory = 0     
            # self.zip_record.totalfiles = 0     
            # self.zip_record.central_offet = 0          # 8 bytes
            # 写入完central 后计算
            # self.zip_record.size_central = eocdPosn - self.zip_record.central_offet          # 8 bytes
        
            self.zip_record.extensible_data = InEcd.zip_record.extensible_data





        # self.ECD.size_central =  eocdPosn - self.ECD.offset_central_disk
        self.ECD.size_central = 0
        self.ECD.dir_signtrue = InEcd.ECD.dir_signtrue  # 中心目录结束标识 (固定值0x06054b50)
        self.ECD.number_disk = InEcd.ECD.number_disk                    #当前磁盘编号
        self.ECD.number_disk_start = InEcd.ECD.number_disk_start        #中心目录开始位置的磁盘编号
        # self.total_entry_disk = 0                             #中心目录开始位置的磁盘编号
        # self.total_entry_central = 0                          #该磁盘上所记录的中心目录数量
        # self.ECD.size_central = InEcd.size_central                  #中心目录大小
        # self.offset_central_disk = 0                          #中心目录开始位置相对于.ZIP archive开始的位移
        self.ECD.comment_length = InEcd.ECD.comment_length              #ZIP文件注释内容长度（n）
        self.ECD.comment = InEcd.ECD.comment                            #ZIP文件注释内容

    def addpartentry(self, zipin, temp_entry, padding):

        entry = copy.deepcopy(temp_entry)
        #获取 local_file   偏移量
        lfhPosn = self.fd.tell()
        # logger.info("写入文件头部信息:")
        # 写入localheadfile 头部信息
        self.write_localheadfile(entry,padding)
       

        zipin.fd.seek(temp_entry.getFileOffset(),0)
        
        copyLen = entry.getCompressedLen()
        if (entry.LocalFileHeader.general_purpose_bit_flag & kUsesDataDescr) != 0:
            copyLen += kDataDescriptorLen
        # logger.info("写入文件数据: size ==>  %s" % copyLen)
        #写入 localheadfile 的 data数据 包括 数字签名区域(16个字节)
        self.copyPartialFpToFp(zipin, copyLen)
        
        # 主要是计算中心目录的偏移量
        endPosn = self.fd.tell()
        entry.setLFHOffset(lfhPosn)
        if zipin.zip_record:
            self.ECD.total_entry_disk = 65535
            self.ECD.total_entry_central = 65535
            self.zip_record.central_directory +=1
            self.zip_record.totalfiles +=1
            self.zip_record.central_offet = endPosn
        else:
            self.ECD.total_entry_disk +=1
            self.ECD.total_entry_central +=1
        self.ECD.size_central = 0      # mark invalid; set by flush()
        self.ECD.offset_central_disk = endPosn
        

        self.Entry_List.append(entry)

    def copyPartialFpToFp(self,zipin,copyLen):
        readSize = 32768
        while copyLen:
            if readSize > copyLen:
                readSize = copyLen
            data = zipin.fd.read(readSize)
            self.fd.write(data)
            copyLen -= readSize


        
        
    def write_localheadfile(self, entry, padding):
        # logger.info("扩展去长度: %d    pading : %d "% (entry.LocalFileHeader.extra_field_length,padding))
        # logger.info(entry.LocalFileHeader.extra_field)
        # logger.info(len(entry.LocalFileHeader.extra_field))
       
        if padding > 0:
            if entry.LocalFileHeader.extra_field_length > 0:
                entry.LocalFileHeader.extra_field_length += padding
                entry.LocalFileHeader.extra_field += (b'0' * padding)
            else:
                entry.LocalFileHeader.extra_field_length = padding
                entry.LocalFileHeader.extra_field = (b'0' * padding)
        localhead = struct.pack("<IHHHHHIIIHH", entry.LocalFileHeader.local_file_header_signature,
                                    entry.LocalFileHeader.version_needed_to_extract,
                                    entry.LocalFileHeader.general_purpose_bit_flag,
                                    entry.LocalFileHeader.compression_method,
                                    entry.LocalFileHeader.last_mod_file_time,
                                    entry.LocalFileHeader.last_mod_file_date,
                                    entry.LocalFileHeader.crc_32,
                                    entry.LocalFileHeader.compressed_size,
                                    entry.LocalFileHeader.uncompressed_size,
                                    entry.LocalFileHeader.file_name_length,
                                    entry.LocalFileHeader.extra_field_length)


        self.fd.write(localhead)
        # logger.info("写入local_filet")
        # logger.info("写入文件名: %s " % entry.LocalFileHeader.file_name)
        # logger.info("扩展去长度: %d    pading : %d "% (entry.LocalFileHeader.extra_field_length,padding))
        self.fd.write(entry.LocalFileHeader.file_name)
        if entry.LocalFileHeader.extra_field_length != 0:
             self.fd.write(entry.LocalFileHeader.extra_field)
            #  logger.info("写入扩展区: size==> %d " % len(entry.LocalFileHeader.extra_field))


def verify(outfile, alignment):

    foundBad = False
    filefd = M_Zipfile(outfile,'rb',False)
    logger.info("开始校验请稍等")
    for index ,entry in  enumerate(filefd.Entry_List):
        if entry.isCompressed():
            pass
            # logger.info("%s %s OK - compressed" % (entry.getFileOffset(), entry.getfilename()))
        else:
            offset = entry.getFileOffset()
            if (offset % alignment) != 0:
                foundBad = True
                #logger.info(" %s %s  BAD - %s" % (index ,offset,  offset % alignment))
                # logger.info("%s %s BAD - %s" % (offset, entry.getfilename(), offset % alignment))

            else:
                pass
                # logger.info("%s %s (OK)" % ( offset, entry.getfilename()))
    if foundBad:
        logger.info("Verification  FAILED")
        return 
    logger.info("Verification  Succesful...")


  





def align_sdk(inputapk,outputapk, alignment):
    try:
        zipin = M_Zipfile(inputapk)
        zipout = M_Zipfile(outputapk,'wb')
        copyAndAlign(zipin, zipout, alignment)
        verify(outputapk, alignment)
    except:
        track_error()
        if os.path.exists(outputapk):
            os.remove(outputapk)


def verify_sdk(inputapk, alignment):
    try:
        verify(inputapk, alignment)
    except:
        track_error()
        
    
if __name__ == "__main__":
    

    try:
        fileout = r"G:\github\book\5e742811747a55a3c01c97e52df84303.apk"
        #filein = r"G:\github\zipalign\test.zip"
        #zipin = M_Zipfile(filein)
        #zipout = M_Zipfile(fileout,'wb')

        #copyAndAlign(zipin,zipout,4)

        verify(fileout,4)
       
    except:
        track_error()
        if os.path.exists(fileout):
            os.remove(fileout)
    
    
