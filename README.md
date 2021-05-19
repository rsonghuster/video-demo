## 部署

首先修改 template.yml, 修改成您自己的 bucket

`BucketName: pumpkin-video # change to your bucket`

然后:

```bash
make deploy
```

会自动生成 vpc、 nas 和 log， 并且配置到 service 上

## 测试

直接上传视频到对应 bucket 的 /inputs 目录中

或者直接在工作流控制台， 发起一个执行， 输入的参数是如下格式

```
{
    "oss_bucket_name":"pumpkin-video",
    "video_key":"inputs/480P.mov",
    "output_prefix":"outputs/",
    "segment_time_seconds":40,
    "dst_format":".mp4",
    "execution_name":"test"
}
```
