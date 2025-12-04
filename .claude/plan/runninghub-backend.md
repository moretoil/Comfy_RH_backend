# FastAPI后端开发计划

## 1. 项目结构
- main.py - 主应用入口和路由
- task_service.py - 任务相关功能
- webapp_service.py - RunningHub代理相关功能
- database.py - 数据库操作
- 使用FastAPI框架
- 异步SQLite数据库

## 2. API接口
- POST /get_node_info - 获取节点信息nodeInfoList(webapp_service)
  此功能目的是获取节点信息，并返回给前端
  要在功能内部进行如下工作
  #获取 nodeInfoList
  curl -X GET "https://www.runninghub.cn/api/webapp/apiCallDemo?apiKey=YOUR_API_KEY&webappId=YOUR_WEBAPP_ID" \
     -H "Host: www.runninghub.cn"
  然后将二次加工的信息进行二次加工
  这是runninghub的原生返回信息，也是要加工的原始信息字段
  
#获取 nodeInfoList 返回示例
{
    "code": 0,
    "msg": "success",
    "errorMessages": null,
    "data": {
        "descriptionEn": "<p>Based on the ComfyUI workflow of LoRA applications, by loading the pre-trained base model and overlaying multiple LoRA models, specific styles and themes of image generation are achieved.</p>",
        "curl": "curl --location --request POST 'https://www.runninghub.cn/task/openapi/ai-app/run' \\\n--header 'Host: www.runninghub.cn' \\\n--header 'Content-Type: application/json' \\\n--data-raw '{\n    \"webappId\": \"null\",\n    \"apiKey\": \"ef974dd428bb4a11876a37f44a546a72\",\n    \"nodeInfoList\": [\n        {\n            \"nodeId\": \"4\",\n            \"fieldName\": \"ckpt_name\",\n            \"fieldValue\": \"dreamshaper_8.safetensors\",\n            \"description\": \"选择模型\"\n        },\n        {\n            \"nodeId\": \"11\",\n            \"fieldName\": \"lora_name\",\n            \"fieldValue\": \"风格化三维-3D-迪士尼皮克斯_v1.0.safetensors\",\n            \"description\": \"选择微调LoRA\"\n        },\n        {\n            \"nodeId\": \"15\",\n            \"fieldName\": \"text\",\n            \"fieldValue\": \"upperbody shot, 1girl,solo,chibi,long hairs, happy, laugh, hugging a teddy bear, looking at viewers, dancing stand, cute, soft color, flowers in background, many flowers, among flowers, best quality, highres, delicate details,\",\n            \"description\": \"正面prompt（英文）\"\n        },\n        {\n            \"nodeId\": \"16\",\n            \"fieldName\": \"text\",\n            \"fieldValue\": \"(worst quality, low quality:1.4), (bad anatomy), text, error, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, signature, watermark, username, blurry, deformed face\",\n            \"description\": \"负面prompt（英文）\"\n        }\n    ]\n}'",
        "webappName": "【c0029】基础LoRA配合提示词文生图",
        "description": "<p>基于 LoRA 应用 的 ComfyUI 工作流，通过加载预训练基础模型并叠加多个 LoRA 模型，实现了特定风格和主题的图像生成。</p>",
        "statisticsInfo": {
            "likeCount": "0",
            "downloadCount": "0",
            "useCount": "0",
            "pv": "0",
            "collectCount": "0"
        },
        "nodeInfoList": [
            {
                "nodeId": "4",
                "nodeName": "CheckpointLoaderSimple",
                "fieldName": "ckpt_name",
                "fieldValue": "dreamshaper_8.safetensors",
                "fieldData": "[{},{\"tooltip\":\"The name of the checkpoint (model) to load.\"}]",
                "fieldType": "CKPT",
                "description": "选择模型",
                "descriptionCn": null,
                "descriptionEn": "Select model"
            },
            {
                "nodeId": "11",
                "nodeName": "LoraLoader",
                "fieldName": "lora_name",
                "fieldValue": "风格化三维-3D-迪士尼皮克斯_v1.0.safetensors",
                "fieldData": "[{},{\"tooltip\":\"The name of the LoRA.\"}]",
                "fieldType": "LORA",
                "description": "选择微调LoRA",
                "descriptionCn": null,
                "descriptionEn": "Select fine-tune LoRA"
            },
            {
                "nodeId": "15",
                "nodeName": "Text",
                "fieldName": "text",
                "fieldValue": "upperbody shot, 1girl,solo,chibi,long hairs, happy, laugh, hugging a teddy bear, looking at viewers, dancing stand, cute, soft color, flowers in background, many flowers, among flowers, best quality, highres, delicate details,",
                "fieldData": "[\"STRING\", {\"multiline\": true}]",
                "fieldType": "STRING",
                "description": "正面prompt（英文）",
                "descriptionCn": null,
                "descriptionEn": "Positive prompt (English)"
            },
            {
                "nodeId": "16",
                "nodeName": "Text",
                "fieldName": "text",
                "fieldValue": "(worst quality, low quality:1.4), (bad anatomy), text, error, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, signature, watermark, username, blurry, deformed face",
                "fieldData": "[\"STRING\", {\"multiline\": true}]",
                "fieldType": "STRING",
                "description": "负面prompt（英文）",
                "descriptionCn": null,
                "descriptionEn": "negative prompt (English)"
            }
        ],
        "covers": [
            {
                "id": "1992766471596208129",
                "objName": "3216356b8d387b5dcee6767bc968cdf6/2025-11-24/0e00688aa051d7480da940a3e29cf66e.png",
                "url": "https://rh-images.xiaoyaoyou.com/3216356b8d387b5dcee6767bc968cdf6/2025-11-24/0e00688aa051d7480da940a3e29cf66e.png",
                "thumbnailUri": "https://rh-images.xiaoyaoyou.com/3216356b8d387b5dcee6767bc968cdf6/2025-11-24/0e00688aa051d7480da940a3e29cf66e.png?imageMogr2/format/jpg/ignore-error/1",
                "imageWidth": "1280",
                "imageHeight": "720"
            }
        ],
        "tags": [
            {
                "id": "1871151815242543197",
                "name": "文生图",
                "nameEn": "Text-to-Image",
                "labels": null
            }
        ]
    }
}




- POST /upload - 文件上传
  此功能目的是上传文件到runninghub，让runninghub能正常处理该文件
  要在功能内部进行如下工作
  #上传文件
  curl -X POST "https://www.runninghub.cn/task/openapi/upload" \
      -H "Host: www.runninghub.cn" \
      -F "apiKey=YOUR_API_KEY" \
      -F "fileType=input" \
      -F "file=@/path/to/your/file"
  #上传文件 返回示例
  {
      "code": 0,
      "msg": "success",
      "data": {
          "fileName": "api/0be036638e518ad1a02e4da639daac5acc21fba275843c8c911283d7d34f9d97.png",
          "fileType": "input"
      }
  }

- POST /submit_task - 提交并创建任务
  此功能是提交任务，并创建任务，返回任务ID
  要在功能内部进行如下工作
  #提交任务
  curl -X POST "https://www.runninghub.cn/task/openapi/ai-app/run" \
      -H "Host: www.runninghub.cn" \
      -H "Content-Type: application/json" \
      -d '{
            "webappId": "YOUR_WEBAPP_ID",
            "apiKey": "YOUR_API_KEY",
            "nodeInfoList": [
              {
                "nodeId": "NODE_ID_1",
                "fieldName": "FIELD_NAME_1",
                "fieldType": "FIELD_TYPE_1",
                "fieldValue": "FIELD_VALUE_1"
              }
            ]
          }'

  
  #提交任务 响应示例
  {
      "code": 0,
      "msg": "success",
      "errorMessages": null,
      "data": {
          "netWssUrl": "wss://www.runninghub.cn:443/ws/c_instance?c_host=10.2.24.99&c_port=84&clientId=60a4d7d100f8c7ee6df5375b6110dab3&workflowId=1992755951447109633&Rh-Comfy-Auth=eyJ1c2VySWQiOiI4NDkzN2RmNTQ2OGUwYWU5N2U5NzNiMWFjOWVmNTVhYyIsInNpZ25FeHBpcmUiOjE3NjQ4NjMyMTU2NzQsInRzIjoxNzY0MjU4NDE1Njc0LCJzaWduIjoiYTYwMGU4MGE5NzY5YmNhMDllMzM2N2MwZjM4YWY5ZjcifQ%3D%3D&target=http://ln.runninghub.cn:11075",
          "taskId": "1994070439827980290",
          "clientId": "60a4d7d100f8c7ee6df5375b6110dab3",
          "taskStatus": "RUNNING",
          "promptTips": "{\"result\": true, \"error\": null, \"outputs_to_execute\": [\"9\"], \"node_errors\": {}}"
      }
  }

  此处就要把返回的信息加工存储到数据库中

- POST /task/query_task_status- 查询任务状态并更新进入数据库
  此功能是查询任务状态并更新进入数据库
  
#查询任务状态
curl -X POST "https://www.runninghub.cn/task/openapi/outputs" \
     -H "Host: www.runninghub.cn" \
     -H "Content-Type: application/json" \
     -d '{
           "apiKey": "YOUR_API_KEY",
           "taskId": "YOUR_TASK_ID"
         }'

  #查询任务状态 响应示例
  {
      "code": 0,
      "msg": "success",
      "errorMessages": null,
      "data": [
          {
              "fileUrl": "https://rh-images.xiaoyaoyou.com/84937df5468e0ae97e973b1ac9ef55ac/output/2loras_test__00001_ztgik_1764258439.png",
              "fileType": "png",
              "taskCostTime": "27",
              "nodeId": "9",
              "thirdPartyConsumeMoney": null,
              "consumeMoney": null,
              "consumeCoins": "6"
          }
      ]
  }

  - GET /tasks/{task_id} - 获取任务状态和结果(task_service)
    此功能是获取自己数据库内的任务状态和结果


## 3. 异步处理
- 使用BackgroundTasks处理耗时操作
- async/await避免阻塞
- 异步数据库查询

## 4. 数据库设计
- SQLite本地存储
- tasks表：id, status, created_at, updated_at, result_data, node_info

## 5. 部署
- uvicorn main:app --reload
- 无需复杂配置