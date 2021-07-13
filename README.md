# 赞存S3对象下载工具使用说明
## 一、    功能简介
本工具可以根据配置文件中的配置连接赞存S3对象存储并将需要下载的对象文件批量下载到指定的目录。
## 二、	安装与运行
赞存S3对象下载工具可以在Windows系统和Linux系统下运行，且都无需安装依赖。
Windows下的赞存S3对象下载工具包含一个名为ObjectDownloader.exe的主程序和一个名为nkoconfig.ini的配置文件，请将这两个文件放置于非中文路径下，建议新建一个文件夹专门存放这两个文件以及之后会生成的日志文件。
在nkoconfig.ini文件中做好相应的配置后，即可使用命令行工具（CMD、PowerShell或Windows Terminal）运行该程序了。
将命令行工具切换到ObjectDownloader.exe所在的文件夹，使用命令.\ObjectDownloader.exe –help可以查看赞存S3对象下载工具的帮助信息，如下图：
```
Usage: ObjectDownloader.py [OPTIONS]

  根据配置文件批量下载S3对象的简单小程序.

Options:
  -c, --config_file PATH          程序的配置文件，默认为当前目录下的nkoconfig.ini文件
  -l, --log_level [critical|error|warning|info|debug]
                                  控制台的日志等级，默认为error。注：critical > error >
                                  warning > info > debug
  --help  
```
 
使用 .\ ObjectDownloader.exe --config_file nkoconfig.ini --log_level error来运行程序；或使用简写.\ ObjectDownloader.exe -c nkoconfig.ini -l error，这两个命令是等价的。
--config_file或-c参数后面可以使用不同的配置文件，以实现使用不同S3租户下载对象文件的要求。
--log_level或-l参数后面可以跟随不同的日志等级，以控制命令行中输出的日志数量。若要查看更详细的日志，可以将日志等级调为info。
两个参数都有默认值，若双击ObjectDownloader.exe文件或不带参数运行，将使用默认值运行该程序。
Linux系统下的赞存S3对象下载工具使用方法与Windows下的赞存S3对象下载工具类似，在此不再赘述。
## 三、	配置文件
配置文件nkoconfig.ini的编码格式为utf-8，为避免编码问题导致读取配置文件出错，请尽量使用带编码格式转换功能的编辑器（如notepad++，SublimeText等）打开配置文件，且不要在配置文件中添加中文字符。
配置文件中分两个区域，[config]区域和[downloads]区域。
[config]区域有以下几个选项：
	access_key：配置赞存中租户的AccessKey。
	secret_key：配置赞存中租户的SecretKey。
	Host：用与填写赞存对象存储的统一服务IP及端口，格式为http://服务IP:端口。
	download_dir：配置用户的下载地址，下载文件夹可以不存在但是要确保该下载地址可以被创建成为一个文件夹，不要使用中文地址。
	sub_dir：配置是否使用子文件夹。若为True，将会在下载目录中为要下载的对象文件创建一个以桶名为名字的子文件夹，所有该桶中要下载的对象文件都会被存放于该子文件夹中；若为False，所有桶中要下载的对象文件都会存放于下载文件夹中。
[downloads]区域仅有一个选项：download_list。download_list是python字典类型的，由于该配置是多行的，对于格式有一定要求，除第一行外，其他所有行距离左边界都至少有一个空格的距离。
编辑download_list时，注意逗号的存在与否，不要因为多了或少了逗号而导致格式错误。
对象文件在下载时会将Object ID中的“/”和“\”替换为“_”作为其文件名。

下面是一个配置文件的例子：
```
[config]
 access_key = H2XL9BBABCDD1C55B6GB
 secret_key = KQ2AUj0rEotOrlpCmKUAFPiPqVfjBdD2zhZpjeqJ
 host = http://172.18.0.10:80
 download_dir = D:\s3_downloads
 sub_dir = True
 [downloads]
download_list = {
    "bkt01":
        "
	backup_aoss.sql,
        0000dstat-master.zip,
        46OCXO_06.17.2021_09.05/CV_MAGNETIC/V_302/CHUNKMAP_TRAILER_3329.FOLDER/0
	"
    ,
    "bkt625":
        "
	EGXJ8V_06.25.2021_01.23/CV_MAGNETIC/V_411/asdfHUNKMAP_TRAILER_4636.FOLDER/0,
        EGXJ8V_06.25.2021_01.23/CV_MAGNETIC/V_411/CHUNKMAP_TRAILER_4729.FOLDER/0
	"
    }
```

## 四、	日志记录
赞存S3对象下载工具运行时会在当前工作目录生成NKO[Time].log和NKO[Time].err两个日志文件。Time的格式为年月日时分秒，如2021年7月12日15点37分03秒生成的日志文件就是NKO20210712153703.log和NKO20210712153703.err两个文件。
其中NKO[Time].log中记录的是info及以上等级的日志，NKO[Time].err中记录的是error及以上等级的日志，请根据需求查看。



