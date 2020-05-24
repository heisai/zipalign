'''
@Author: your name
@Date: 2020-04-03 11:50:29
@LastEditTime: 2020-04-10 18:22:18
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \zipalign\config.py
'''


import os 
import sys

kSignature = 0x06054b50
kEOCDLen = 22     
kMaxCommentLen = 65535 
kMaxEOCDSearch  = kMaxCommentLen +  kEOCDLen

FileheaderLen = 46
kLFHLen      = 30
FileHead = 0x02014b50

#压缩方式, 安卓只有 0,8 
kCompressStored     = 0       # no compression
kCompressDeflated   = 8       #standard deflate

kUsesDataDescr      = 0x0008
kDataDescriptorLen  = 16

Zip64CenSearch = 66535 + 56 + 20 + 66535 + 22


Zip64Record_Signature = 0x06064b50
Zip64Locator_Signature = 0x07064b50



