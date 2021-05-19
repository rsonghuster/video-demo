# -*- coding: utf-8 -*-
import logging
import json

LOGGER = logging.getLogger()


def handler(event, context):
    LOGGER.info(event)
    evt = json.loads(event)
    result = {"videoCensorResult": "succeeded"}
    videoCensorStatus = evt["videoCensorStatus"]
    for st in videoCensorStatus:
        if st != "succeeded":  # 有一个审核没有通过, 返回
            LOGGER.info(videoCensorStatus)
            result = {"videoCensorResult": "failed"}
            return result
    return result
