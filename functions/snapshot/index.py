# -*- coding: utf-8 -*-
import logging
import oss2
import os
import time
import json
import subprocess

logging.getLogger("oss2.api").setLevel(logging.ERROR)
logging.getLogger("oss2.auth").setLevel(logging.ERROR)

LOGGER = logging.getLogger()


def get_fileNameExt(filename):
    (fileDir, tempfilename) = os.path.split(filename)
    (shortname, extension) = os.path.splitext(tempfilename)
    return shortname, extension


def handler(event, context):
    # 清空 /tmp 文件夹
    try:
        os.system("rm -rf /tmp")
    except:
        pass
    evt = json.loads(event)
    oss_bucket_name = evt["oss_bucket_name"]
    object_key = evt["video_key"]
    shortname, extension = get_fileNameExt(object_key)
    output_prefix = evt["output_prefix"]
    execution_name = evt['execution_name']

    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId,
                        creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(
        auth, 'oss-%s-internal.aliyuncs.com' % context.region, oss_bucket_name)

    # delete all split video in oss
    split_keys = evt["split_keys"]
    for obj in split_keys:
        oss_client.delete_object(obj)

    input_path = oss_client.sign_url('GET', object_key, 6 * 3600)
    # 获取 meta 信息
    raw_result = subprocess.check_output(["/code/ffprobe", "-v", "quiet", "-show_format", "-show_streams",
                                          "-print_format", "json",  "-i",  input_path])
    meta_result = json.loads(raw_result)
    LOGGER.info(meta_result)
    # TODO: 插入数据库

    # 每一秒截图一张
    video_proc_dir = "/tmp/"
    subprocess.check_call(
        ["/code/ffmpeg", "-i", input_path, "-vf", "fps=1", video_proc_dir + shortname + "_%d.jpg"])

    pic_prefix = os.path.join(output_prefix, execution_name)
    for filename in os.listdir(video_proc_dir):
        filepath = os.path.join(video_proc_dir, filename)
        filekey = os.path.join(pic_prefix, filename)
        oss_client.put_object_from_file(filekey, filepath)
        os.remove(filepath)
        LOGGER.info("Uploaded {} to {}".format(filepath, filekey))

    return {}
