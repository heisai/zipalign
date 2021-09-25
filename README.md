# zipalign 兼容2G 以上 以及zip_64 的apk
### 该版本使用python 语言开发. 后期会采用c++ 开发出c++ 的版本.
  __该工具用python 实现 zipalign  兼容2G以上的apk 包括(64位)__
  

  **本篇博客 只讲解 zip 32, 64的结构.也就是 zipalign 的实现原理:**
### 首先看下zip 的结构吧:

	 4.3.6 Overall .ZIP file format:
	
      [local file header 1]
      [encryption header 1]
      [file data 1]
      [data descriptor 1]
      . 
      .
      .
      [local file header n]
      [encryption header n]
      [file data n]
      [data descriptor n]
      [archive decryption header] 
      [archive extra data record] 
      [central directory header 1]
      .
      .
      .
      [central directory header n]
      [zip64 end of central directory record]
      [zip64 end of central directory locator] 
      [end of central directory record]


### Local file header 文件头
|Offset |Bytes|Description|描述|
|--|--|--|--|
|0|	4|	local file header signature	|文件头标识 (固定值0x04034b50)
|4	|2|	version needed to extract|	解压时遵循ZIP规范的最低版本
|6	|2	|general purpose bit flag|	通用标志位
|8	|2	|compression method	|压缩方式
|10|	2	|last mod file time	|最后修改时间（MS-DOS格式）
|12	|2	|last mod file date	|最后修改日期（MS-DOS格式）
|14|	4	|crc-32	|冗余校验码
|18|	4	|compressed size	|压缩后的大小
|22	|4	|uncompressed size|	未压缩之前的大小
|26|	2	|file name length|	文件名长度（n）
|28	|2	|extra field length	|扩展区长度（m）
|30	|n	|file name	|文件名
|30+n	|m	|extra field	|扩展区
__用 010  工具 可以查看 具体字段的 数据, 如下是 Local file header的结构__ 
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200523164244517.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3NpbmF0XzE0ODU0NzIx,size_16,color_FFFFFF,t_70#pic_center)
### File data 文件数据
里面存储文件的数据,在Local file header 数据段中,filename 之后
![在这里插入图片描述](https://img-blog.csdnimg.cn/20200523174716769.png?x-oss-process=image/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3NpbmF0XzE0ODU0NzIx,size_16,color_FFFFFF,t_70)

### Data descriptor 数据描述
|Offset|Bytes|Description|描述
|--|--|--|--|
|0	|4		|数据描述符标识|（固定值0x08074b50，ZIP标准里面没有这个字段）
|4	|4	|crc-32	|冗余校验码
|8	|4	|compressed size	|压缩后的大小
|12	|4	|uncompressed size	|未压缩之前的大小

__只有当 [local file header] 的 general purpose bit flag 字段第3位Bit置1时 也是8 ，[data descriptor] 才会存在，此时[local file header] 的 crc-32 、compressed size 、uncompressed size 这三个字段都会被储存为0，其正确的值会记录在 [data descriptor] 数据段里面__


### Central directory  中心目录区


|Offset|Bytes|Description|描述
|--|--|--|--|
|0|	4	|central file header signature	|文件头标识 |(固定值0x02014b50)|
|4	|2	|version made by	|高位字节表示文件属性信息的兼容性，低位字节表示压缩软件支持的ZIP规范版本
|6	|2	|version needed to extract	|解压时遵循ZIP规范的最低版本
|8	|2	|general purpose bit flag	|通用标志位
|10	|2	|compression method	|压缩方式
|12	|2	|last mod file time	|最后修改时间（MS-DOS格式）
|14	|2	|last mod file date	|最后修改日期（MS-DOS格式）
|16	|4	|crc-32	|冗余校验码
|20	|4	|compressed size	|压缩后的大小
|24	|4	|uncompressed size	|未压缩之前的大小
|28	|2	|file name length	|文件名长度（n）
|30	|2	|extra field length	|扩展区长度（m）
|32	|2	|file comment length	|文件注释长度（k）
|34	|2	|disk number start	|文件开始位置的磁盘编号
|36	|2	|internal file attributes	|内部文件属性
|38	|4	|external file attributes	|外部文件属性
|42	|4	|relative offset of local header	|对应 [local file header] 的偏移位置
|46	|n	|file name	|目录文件名
|46+n|	m	|extra field|	扩展域
|46+n+m	|k|	file comment|	文件注释内容

__这里需要注意的是64 位的格式:__

1:  compressed size 大小大于4个字节  默认写0xffffffff. 因为最多只能存储四个字节大小.
2:  uncompressed size 大小大于4个字节  默认写0xffffffff.  同上
3: 当文件偏移量 (relative offset of local header) 大于4个字节的时候. 默认写0xffffffff. 同上

那么这三个字段的数据真正 存储在哪呢? 
这个三个存储在 extra field 里面;
	 结构如下:
	 
   

|序号|Value| Size|Description
|--|--|--|--|
1|(ZIP64) 0x0001|        2 bytes        |     Tag for this "extra" block type(zip 64 默认)
2|Size              |    2 bytes    |         Size of this "extra" block  Original (扩展区的大小,是以上三项数据的大下)
3|Size     |             8 bytes        |     Original uncompressed file size   Compressed (文件压缩前的大小)     
4|Size      |            8 bytes      |       Size of compressed data   Relative Header   (文件压缩前的大小)   
5|Offset        |        8 bytes       |      Offset of local header record Disk Start    (文件的偏移量)
6|Number      |          4 bytes      |       Number of the disk on which this file starts 

序号1: 固定格式 0x0001 前提是 当 compressed size ,uncompressed size, relative offset of local header 大于四个字节的时候, 这块数据才有效.
序号2: 表示扩展区的大小 基本上是8, 16, 24 最后一个四个字节可不写入

### Zip64 end of central directory record 结构

|序号|Description|size
|--|--|--|
1|zip64 end of central dir  signature            |           4 bytes  (0x06064b50)
2|size of zip64 end of central directory record     |           8 bytes
3| version made by          |       2 bytes
4|version needed to extract     |  2 bytes
5|number of this disk        |     4 bytes
6|number of the disk with the start of the central directory | 4 bytes
7|total number of entries in the central directory on this disk  |8 bytes
8| total number of entries in the central directory         |      8 bytes
 9|size of the central directory |  8 bytes
10|offset of start of central directory with respect to  the starting disk number     |   8 bytes
11| zip64 extensible data sector |   (variable size)

当文件数目 大于65535 的时候.  end of central directory record 中心目录结束记录 是存放不下的. 所以这个数, 以及中心目录区的偏移量 都存储在这里. 
### Zip64 end of central directory locator 结构
|Description|size
|--|--|
zip64 end of central dir locator  signature |4 bytes  (0x07064b50)
number of the disk with the start of the zip64 end of central directory | 4 bytes
relative offset of the zip64 end of central directory record| 8 bytes
total number of disks| 4 bytes







### end of central directory record 中心目录结束记录
|Offset|Bytes|Description|描述
|--|--|--|--|
|0	|4	|end of central dir signature	|中心目录结束标识 (固定值0x06054b50)
|4	|2	|number of this disk	|当前磁盘编号
|6	|2	|number of the disk with the start of the central directory	|中心目录开始位置的磁盘编号
|8	|2	|total number of entries in the central directory on this disk	|中心目录开始位置的磁盘编号
|10	|2|	total number of entries in the central directory	|该磁盘上所记录的中心目录数量
|12	|4	|size of the central directory	|中心目录大小
|16	|4	|offset of start of central directory with respect to the starting disk number	|中心目录开始位置相对于.ZIParchive开始的位移
|20	|2|	.ZIP file comment length	|ZIP文件注释内容长度（n）
|22	|n	|.ZIP file comment	|ZIP文件注释内容

主要说下 该磁盘上所记录的中心目录数量,  中心目录开始位置相对于.ZIParchive开始的位移. .
当文件数目小于2个字节 65535 的时候. 那么获取文件数就从这里获取, 当大于的时候真正获取文件数目那就的从 Zip64 end of central directory record 结构 中获取. 
中心目录开始位置相对于.ZIParchive开始的位移 也是.同样的方式



### 参考文档:
[https://thismj.cn/2019/02/14/qian-xi-zip-ge-shi/]
[https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT]


### 详细讲解以及zip 结构在我的博客中: 本仓库只提供开源代码
https://blog.csdn.net/sinat_14854721/article/details/106301673

#### 参考链接:
https://thismj.cn/2019/02/14/qian-xi-zip-ge-shi/

https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT

