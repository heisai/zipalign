'''
@Author: heisai
@Date: 2020-04-03 11:50:29
@LastEditTime: 2020-04-10 18:13:51
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: \zipalign\zipalign.py
'''
import os
import sys
import argparse
import time
from M_Zipfile import align_sdk, verify_sdk
if __name__ == "__main__":
    try:
        if len(sys.argv[1:]) == 5:
            (inputapk, outputapk,alignment) = (sys.argv[4], sys.argv[5], sys.argv[3])
            align_sdk(inputapk, outputapk, int(alignment))
        elif len(sys.argv[1:]) ==4:
            (inputapk, alignment) = (sys.argv[4], sys.argv[3])
            verify_sdk(inputapk, int(alignment))
        else:
            print("""Usage:
                zipalign.exe  -f -v 4  inputapk  outputapk  or 
                zipalign.exe  -c -v 4  inputapk
                """)
            time.sleep(10)
    except :
        pass
        
        
