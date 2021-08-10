#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author : MuLuguang

# 参考文档
# http://docs.ceph.org.cn/radosgw/s3/python/
# https://blog.csdn.net/nslogheyang/article/details/100115336
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-examples.html


import logging
import os
import configparser
import time
import botocore
import click
import uuid
import urllib
import boto3


def _show_version():
    click.echo('NKO Object Downloader, Version 1.0.0')


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    _show_version()
    ctx.exit()


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

str_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
log_file = "NKO" + str_time + ".log"
error_file = "NKO" + str_time + ".err"

fh = logging.FileHandler(log_file, encoding="utf-8", mode="a")  # fh : file handler
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

fh2 = logging.FileHandler(error_file, encoding="utf-8", mode="a")  # fh : file handler
fh2.setLevel(logging.ERROR)  # 只记录ERROR等级及以上的日志
fh2.setFormatter(formatter)

ch = logging.StreamHandler()   # ch : console handler
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(fh2)
logger.addHandler(ch)


class CephS3BOTO3:

    def __init__(self, access_key, secret_key, host):
        logger.info("初始化S3连接。")
        self.session = boto3.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        self.url = host
        try:
            self.s3_client = self.session.client('s3', endpoint_url=self.url)
        except Exception as e:
            logger.error(e)

    # 获得所有存储桶的信息，并打印桶的名字
    def get_bucket(self):
        logger.info("获取所有桶的名称。")
        buckets = [bucket['Name'] for bucket in self.s3_client.list_buckets()['Buckets']]
        print(buckets)
        return buckets

    # 创建一个存储桶
    def create_bucket(self, bucket_name, region=None):
        try:
            if region is None:
                self.s3_client.create_bucket(Bucker=bucket_name)
            else:
                location = {'LocationConstraint': region}
                self.s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
        except Exception as e:
            logger.error(e)
            return False
        return True

    # 上传一个文件
    #
    def upload_file(self, file_name, bucket, object_name=None):
        """Upload a file to an S3 bucket
        :param file_name: File to upload  like E:\\数据库\\backup_aoss.sql
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified ,use file_name instead
        :return: True if file was uploaded, else False
        """
        # 生成一个UUID
        object_id = str(uuid.uuid3(uuid.NAMESPACE_OID, file_name))
        # If S3 object_name was not specified, use file_name
        base_name = os.path.basename(file_name)
        if object_name is None:
            object_name = base_name

        # Upload the file
        try:
            self.s3_client.upload_file(file_name, bucket, object_id,
                                       ExtraArgs={"Metadata": {"x-ycore-filename": object_name}})
        except Exception as e:
            logger.error(e)
            return False
        return True

    def download_file(self, d_dir, bucket, object_id):
        # param d_dir: directory to download files
        # param bucket: Bucket to download to
        # param object_name: S3 object name.must have
        if d_dir == '':
            d_dir = r'D:\s3_downloads'
        if not os.path.exists(d_dir):
            os.mkdir(d_dir)
        try:
            metadata = self.s3_client.head_object(Bucket=bucket, Key=object_id)
        except botocore.exceptions.ClientError as e:
            logger.error(f'获取 {object_id} 的Metadata时出错！')
            logger.error(e)
            return False

        try:
            meta = metadata['Metadata']['x-ycore-filename']
            meta = urllib.parse.unquote(meta, encoding='utf-8', errors='replace')  # 中文格式乱码转为utf-8
            file_name = meta.replace(r'/', '_')  # 如果Metadata中有'x-ycore-filename'，使用它的值作为文件名
            file_name = file_name.replace('\\', '_')
            file_full_name = os.path.join(d_dir, file_name)
            logger.info(f'开始下载对象 {object_id},使用文件名：{file_name}。')
        except KeyError:
            file_name = object_id.replace(r'/', '_')
            file_name = file_name.replace('\\', '_')
            file_full_name = os.path.join(d_dir, file_name)
            logger.info(f'开始下载对象 {object_id}。')
        try:
            self.s3_client.download_file(bucket, object_id, file_full_name)
            logger.info("下载对象 %s 成功。" % object_id)
        except Exception as e:
            logger.error("下载对象 %s 失败！" % object_id)
            logger.error(e)
            return False
        return True

    def delete(self, bucket, object_name):
        # import boto3
        # s3 = boto3.resource('s3')
        # s3.Object('your-bucket', 'your-key').delete()
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=object_name)
        except Exception as e:
            logger.error(e)
            return False
        return True


# 读取配置文件
class ReadConfig:
    def __init__(self, file_path=None):
        if file_path:
            config_path = file_path
        else:
            root_dir = os.path.dirname(os.path.abspath('.'))
            config_path = os.path.join(root_dir, 'nkoconfig.ini')  # 使用当前目录下的nkoconfig.ini文件
        self.cf = configparser.ConfigParser()
        try:
            self.cf.read(config_path, encoding="utf-8")
        except Exception as e:
            logger.error(e)

    def get_config(self, param):
        try:
            value = self.cf.get('config', param)
            return value
        except Exception as e:
            logger.error(e)
            logger.error("请检查配置文件config区域中的配置！")
            return False

    def get_download_list(self):
        try:
            value = self.cf.get('downloads', 'download_list')
            return value
        except Exception as e:
            logger.error(e)
            logger.error('请检查配置文件中downloads区域download_list项！')
            return False


@click.command()
@click.option('--config_file', '-c', type=click.Path(exists=True), default='nkoconfig.ini',
              help='程序的配置文件，默认为当前目录下的nkoconfig.ini文件')
@click.option('--log_level', '-l', type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']),
              default='error', help='控制台的日志等级，默认为error。注：critical > error > warning > info > debug')
@click.option('--version', '-v', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True, help='显示本软件的版本信息。')
def main(config_file, log_level):
    """根据配置文件批量下载S3对象的简单小程序."""
    if log_level.upper() == 'WARNING' or log_level.upper() == 'ERROR':
        ch.setLevel(logging.ERROR)  # 根据参数确定控制台的日志等级。
    elif log_level.upper() == 'CRITICAL':
        ch.setLevel(logging.CRITICAL)  # 根据参数确定控制台的日志等级。
    else:
        ch.setLevel(logging.INFO)  # 根据参数确定控制台的日志等级。

    # 从配置文件中获取配置
    config = ReadConfig(config_file)
    host = config.get_config('host')
    access_key = config.get_config('access_key')
    secret_key = config.get_config('secret_key')
    download_dir = config.get_config('download_dir')
    sub_dir = config.get_config('sub_dir')
    download_list = config.get_download_list()
    download_list = download_list.replace('\n', '').replace('\r', '')  # 去除换行,回车
    # \r 代表回车，也就是打印头归位，回到某一行的开头。 \n代表换行，就是走纸，下一行。

    # cephs3_boto3 = CephS3BOTO3(access_key=access_key, secret_key=secret_key, host=host)
    # cephs3_boto3.upload_file(r'E:\Python\dstat-master.zip', 'bkt999')
    # cephs3_boto3.download_file(d_dir='', bucket='bkt999', object_id='373f99a6-6e8a-3b2b-9a49-04051b071743')
    # cephs3_boto3.download_file(d_dir='', bucket='bkt999', object_id='s3_downloads3/bkt01/0000dstat-master.zip')
    # cephs3_boto3.download_file(d_dir='', bucket='bkt999', object_id='5576840f-4a95-4735-a8e6-29d6fa989ef5')

    try:
        download_list = eval(download_list)  # 转换为字典
    except Exception as e:
        logger.critical(e)
        logger.critical('请检查配置文件中download_list项')
        logger.critical('程序已退出。')
        exit(-1)

    log_str = 'host=' + host + ', download_dir=' + download_dir + ', sub_dir=' + sub_dir
    logger.info(log_str)
    logger.info('download_list=%s' % str(download_list))
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            logger.info('创建目录 %s 成功' % download_dir)
        except Exception as e:
            logger.critical(e)
            logger.critical("无法创建目录，请检查配置文件中的下载目录。")
            logger.critical("程序已退出。")
            exit(-1)
    else:
        logger.info("%s 目录已经存在，无需创建。" % download_dir)

    # 统计信息 {'all':[0,0,0],'bucket01':[0,0,0],...}    [0,0,0]=[all, successed, failed]
    statistics = {'_All': [0, 0, 0]}
    cephs3_boto3 = CephS3BOTO3(access_key=access_key, secret_key=secret_key, host=host)
    for bucket_name in download_list.keys():
        statistics[bucket_name] = [0, 0, 0]
        if sub_dir.lower() == 'true':
            download_dir_full = os.path.join(download_dir, bucket_name)
            logger.info("使用 %s 作为子目录，桶 %s 中的对象将下载到 %s 目录。" % (bucket_name, bucket_name, download_dir_full))
        else:
            download_dir_full = os.path.abspath(download_dir)
            logger.info("未启用子目录，桶 %s 中所有对象都将下载到 %s 目录。" % (bucket_name, download_dir_full))

        for object_id in download_list[bucket_name].split(','):   # 以，分割称为列表
            if cephs3_boto3.download_file(download_dir_full, bucket_name, object_id):
                statistics[bucket_name][0] += 1  # bucket_all + 1
                statistics[bucket_name][1] += 1  # bucket_successed + 1
                statistics['_All'][0] += 1  # all + 1
                statistics['_All'][1] += 1  # all_successed + 1
            else:
                statistics[bucket_name][0] += 1  # bucket_all + 1
                statistics[bucket_name][2] += 1  # bucket_failed + 1
                statistics['_All'][0] += 1  # all + 1
                statistics['_All'][2] += 1  # all_failed + 1
    logger.info(f'统计信息：{statistics}')
    print('-'*76)
    print('下载统计：')
    print('{:<24}{:<18}{:<18}{:<18}'.format('BucketName', 'TotalDownloaded', 'Successed', 'Failed'))
    for k, v in statistics.items():
        if k != '_All':
            print('{:<24}{:<18}{:<18}{:<18}'.format(k, v[0], v[1], v[2]))
    print('{:<24}{:<18}{:<18}{:<18}'.format('Total', statistics['_All'][0],
                                            statistics['_All'][1], statistics['_All'][2]))
    print('-'*76)
    logger.info("程序已结束，日志请查看 log.txt 文件和 error.txt 文件。")
    logger.removeHandler(fh)
    logger.removeHandler(fh2)
    logger.removeHandler(ch)


if __name__ == "__main__":
    main()
