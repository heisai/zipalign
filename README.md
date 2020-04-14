# zipalign 兼容2G 以上 以及zip_64 的apk
zip 通用格式

    [local file header 1]
    [file data 1]
    [data descriptor 1]
    . 
    .
    .
    [local file header n]
    [file data n]
    [data descriptor n]
    [archive decryption header] (EFS)
    [archive extra data record] (EFS)
    [central directory]
    [zip64 end of central directory record]
    [zip64 end of central directory locator] 
    [end of central directory record]
    
 ==## Local file header 文件头==
 Offset	Bytes	Description	描述
 
| Offset | Bytes | Description | 翻译|
|--------|-------|-------------|-----|
|0	     |   4	 |local file header signature	  | 文件头标识 (固定值0x04034b50)|
|4	     |   2	 |version needed to extract	    |解压时遵循ZIP规范的最低版本|
|6	     |2	     |general purpose bit flag	    |通用标志位
|8	     |2	     |compression method	          |压缩方式
|10	     |2	     |last mod file time            |	最后修改时间（MS-DOS格式）
|12      |2	     |last mod file date            |	最后修改日期（MS-DOS格式）
|14	     |4	     |crc-32                        |	冗余校验码
|18	     |4	     |compressed size               |	压缩后的大小
|22	     |4	     |uncompressed size	            |未压缩之前的大小
|26	     |2	     |file name length	            |文件名长度（n）
|28	     |2	     |extra field length	          |扩展区长度（m）
|30	     |n	     |file name	                    |文件名
|30+n	   |m	     |extra field	                  |扩展区


##File data 文件数据
储存在[Local file header] 数据段后，用来记录文件本身的数据。

Data descriptor 数据描述
Offset	Bytes	Description	译
0	4		数据描述符标识（固定值0x08074b50，ZIP标准里面没有这个字段）
4	4	crc-32	冗余校验码
8	4	compressed size	压缩后的大小
12	4	uncompressed size	未压缩之前的大小
只有当 [local file header] 的 general purpose bit flag 字段第3位Bit置1时，[data descriptor] 才会存在，此时[local file header] 的 crc-32 、compressed size 、uncompressed size 这三个字段都会被储存为0，其正确的值会记录在 [data descriptor] 数据段里面。

Central directory
根据上面的分析可知，ZIP中的每一个文件，都对应着 [local file header] + [file data] + [data descriptor]，而 [central directory] 就是ZIP中所有文件的目录，其储存格式展开如下：

[file header 1]
      .
      .
      . 
[file header n]
[digital signature] 
File header
Offset	Bytes	Description	描述
0	4	central file header signature	文件头标识 (固定值0x02014b50)
4	2	version made by	高位字节表示文件属性信息的兼容性，
低位字节表示压缩软件支持的ZIP规范版本
6	2	version needed to extract	解压时遵循ZIP规范的最低版本
8	2	general purpose bit flag	通用标志位
10	2	compression method	压缩方式
12	2	last mod file time	最后修改时间（MS-DOS格式）
14	2	last mod file date	最后修改日期（MS-DOS格式）
16	4	crc-32	冗余校验码
20	4	compressed size	压缩后的大小
24	4	uncompressed size	未压缩之前的大小
28	2	file name length	文件名长度（n）
30	2	extra field length	扩展区长度（m）
32	2	file comment length	文件注释长度（k）
34	2	disk number start	文件开始位置的磁盘编号
36	2	internal file attributes	内部文件属性
38	4	external file attributes	外部文件属性
42	4	relative offset of local header	对应 [local file header] 的偏移位置
46	n	file name	目录文件名
46+n	m	extra field	扩展域
46+n+m	k	file comment	文件注释内容


digital signature
Offset	Bytes	Description	描述
0	4	header signature	数字签名头标识 (固定值0x05054b50)
4	2	size of data	数字签名数据大小（n）
6	n	signature data	数字签名数据


end of central directory record 中心目录结束记录
Offset	Bytes	Description	描述
0	4	end of central dir signature	中心目录结束标识 (固定值0x06054b50)
4	2	number of this disk	当前磁盘编号
6	2	number of the disk with the
start of the central directory	中心目录开始位置的磁盘编号
8	2	total number of entries in the
central directory on this disk	中心目录开始位置的磁盘编号
10	2	total number of entries in
the central directory	该磁盘上所记录的中心目录数量
12	4	size of the central directory	中心目录大小
16	4	offset of start of central
directory with respect to
the starting disk number	中心目录开始位置相对于.ZIP archive开始的位移
20	2	.ZIP file comment length	ZIP文件注释内容长度（n）
22	n	.ZIP file comment	ZIP文件注释内容

来源: ThisMJ
作者: ThisMJ
链接: https://thismj.cn/2019/02/14/qian-xi-zip-ge-shi/
本文章著作权归作者所有，任何形式的转载都请注明出处。
