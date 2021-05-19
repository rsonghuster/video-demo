# -*- coding: utf-8 -*-
import logging

from aliyunsdkcore.client import AcsClient
from aliyunsdkgreen.request.v20180509 import VideoAsyncScanRequest
from aliyunsdkgreen.request.v20180509 import VideoAsyncScanResultsRequest
from aliyunsdkcore.auth.credentials import StsTokenCredential
import json
import uuid
import oss2

LOGGER = logging.getLogger()


class ExceptionNeedsRetry(Exception):
    pass


def handler(event, context):
    LOGGER.info(event)
    evt = json.loads(event)
    video_key = evt['split_video_key']
    oss_bucket_name = evt['oss_bucket_name']
    creds = context.credentials
    sts_token_credential = StsTokenCredential(
        creds.access_key_id, creds.access_key_secret, creds.security_token)
    clt = AcsClient(region_id=context.region, credential=sts_token_credential)

    request = VideoAsyncScanRequest.VideoAsyncScanRequest()
    request.set_accept_format('JSON')
    request.set_endpoint("green.{}.aliyuncs.com".format(context.region))

    creds = context.credentials
    auth = oss2.StsAuth(creds.accessKeyId,
                        creds.accessKeySecret, creds.securityToken)
    oss_client = oss2.Bucket(
        auth, 'oss-%s.aliyuncs.com' % context.region, oss_bucket_name)
    object_url = oss_client.sign_url('GET', video_key, 6 * 3600)

    task = {
        "dataId": str(uuid.uuid1()),
        "url": object_url
    }

    # 鉴黄
    request.set_content(json.dumps({"tasks": [task], "scenes": ["porn"]}))
    response = clt.do_action_with_exception(request)

    LOGGER.info(str(response, encoding='utf-8'))
    result = json.loads(response)
    ret = {"censorTaskIds": []}
    if 200 == result["code"]:
        taskResults = result["data"]
        for taskResult in taskResults:
            ret["censorTaskIds"].append(taskResult["taskId"])
    else:
        # 出现 errcode， 可能是内容审核那边返回限流等错误
        # https://help.aliyun.com/document_detail/53414.html?spm=a2c4g.11186623.6.623.57f5c4379FDVBW
        # 可以做更加详细的错误分析，抛出错误， 让 fnf 会自动重试
        raise ExceptionNeedsRetry("fail to VideoAsyncScan")
    LOGGER.info(ret)
    return ret
