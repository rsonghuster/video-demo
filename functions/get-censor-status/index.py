# -*- coding: utf-8 -*-
import logging
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkgreen.request.v20180509 import VideoAsyncScanRequest
from aliyunsdkgreen.request.v20180509 import VideoAsyncScanResultsRequest
from aliyunsdkcore.auth.credentials import StsTokenCredential

LOGGER = logging.getLogger()


class ExceptionNeedsRetry(Exception):
    pass


def handler(event, context):
    LOGGER.info(event)
    evt = json.loads(event)
    creds = context.credentials
    sts_token_credential = StsTokenCredential(
        creds.access_key_id, creds.access_key_secret, creds.security_token)
    clt = AcsClient(region_id=context.region, credential=sts_token_credential)
    request = VideoAsyncScanResultsRequest.VideoAsyncScanResultsRequest()
    request.set_endpoint("green.{}.aliyuncs.com".format(context.region))
    request.set_accept_format('JSON')
    taskIds = evt['censorTaskIds']
    request.set_content(json.dumps(taskIds))
    response = clt.do_action_with_exception(request)
    LOGGER.info(response)
    result = json.loads(response)
    censorStatus = "running"
    if 200 == result["code"]:
        taskResults = result["data"]
        censorStatus = "succeeded"
        for taskResult in taskResults:
            if 200 == taskResult['code']:
                results = taskResult.get('results')
                if not results:
                    censorStatus = "failed"
                else:
                    for r in results:
                        if r["suggestion"] != "pass":
                            censorStatus = "failed"
                        else:
                            censorStatus = "succeeded"
            elif 280 == taskResult["code"]:
                censorStatus = "running"
            else:  # TODO, 这里可以处理的更加细腻些
                raise ExceptionNeedsRetry("fail to VideoAsyncScanResults")
    else:
        # 出现 errcode， 可能是内容审核那边返回限流等错误
        # https://help.aliyun.com/document_detail/53414.html?spm=a2c4g.11186623.6.623.57f5c4379FDVBW
        # 可以定义自定义错误，让 fnf 自动重试
        raise ExceptionNeedsRetry(
            "fail to get VideoAsyncScanResults")

    return {
        "censorStatus": censorStatus
    }
