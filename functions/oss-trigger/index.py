# -*- coding: utf-8 -*-
import os
import json
import re
import logging
import time

from aliyunsdkcore.client import AcsClient
from aliyunsdkfnf.request.v20190315 import StartExecutionRequest
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.auth.credentials import StsTokenCredential


LOGGER = logging.getLogger()

OUTPUT_DST = os.environ["OUTPUT_DST"]
FLOW_NAME = os.environ["FLOW_NAME"]
DST_FORMAT = os.environ["DST_FORMAT"]
DEFAULT_SEG_INTERVAL = os.environ.get("DEFAULT_SEG_INTERVAL", 60)


def get_fileNameExt(filename):
    (fileDir, tempfilename) = os.path.split(filename)
    (shortname, extension) = os.path.splitext(tempfilename)
    return shortname, extension


def handler(event, context):
    evt = json.loads(event)
    evt = evt["events"]
    oss_bucket_name = evt[0]["oss"]["bucket"]["name"]
    object_key = evt[0]["oss"]["object"]["key"]

    object_key = evt[0]["oss"]["object"]["key"]
    size = evt[0]["oss"]["object"]["size"]
    _, extension = get_fileNameExt(object_key)
    M_size = round(size / 1024.0 / 1024.0, 2)

    creds = context.credentials
    sts_token_credential = StsTokenCredential(
        creds.access_key_id, creds.access_key_secret, creds.security_token)
    client = AcsClient(region_id=context.region,
                       credential=sts_token_credential)

    execution_name = re.sub(
        r"[^a-zA-Z0-9-_]", "_", object_key) + "-" + context.request_id

    json_log = {
        "request_id": context.request_id,
        "execution_name": execution_name,
        "video_name": object_key,
        "video_format": extension[1:],
        "size": str(M_size),
        "processed_video_location": OUTPUT_DST,
    }
    print(json.dumps(json_log))

    segment_time_seconds = DEFAULT_SEG_INTERVAL

    input = {
        "oss_bucket_name": oss_bucket_name,
        "video_key": object_key,
        "output_prefix": OUTPUT_DST,
        "segment_time_seconds": int(segment_time_seconds),
        "dst_format": DST_FORMAT,
        "execution_name": execution_name,
    }

    try:
        request = StartExecutionRequest.StartExecutionRequest()
        request.set_endpoint(
            "{}-internal.fnf.aliyuncs.com".format(context.region))
        request.set_FlowName(FLOW_NAME)
        request.set_Input(json.dumps(input))
        request.set_ExecutionName(execution_name)
        return client.do_action_with_exception(request)
    except ServerException as e:
        LOGGER.info(e.get_request_id())

    return "ok"
