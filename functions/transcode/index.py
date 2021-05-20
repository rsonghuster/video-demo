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
    evt = json.loads(event)
    oss_bucket_name = evt["oss_bucket_name"]
    object_key = evt["video_key"]
    shortname, extension = get_fileNameExt(object_key)
    OUTPUT_DST = evt["output_prefix"]
    DST_TARGET = evt["dst_format"]

    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId,
                        creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(
        auth, 'oss-%s-internal.aliyuncs.com' % context.region, oss_bucket_name)

    input_path = oss_client.sign_url('GET', object_key, 6 * 3600)
    transcoded_filepath = '/mnt/auto/' + shortname + DST_TARGET
    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)

    # 转码  ffmpeg 命令
    cmd = ["/code/ffmpeg", "-y", "-threads", "4", "-i", input_path,
           "-s", "480x360", transcoded_filepath]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as exc:
        print(str(exc))
        # if transcode fail， send event to mns queue or insert in do db
        # ...
        raise Exception(context.request_id + " transcode failure")

    oss_client.put_object_from_file(
        os.path.join(OUTPUT_DST, shortname + DST_TARGET), transcoded_filepath)

    # if transcode succ， send event to mns queue or insert in do db
    # ...

    if os.path.exists(transcoded_filepath):
        os.remove(transcoded_filepath)

    return {}
