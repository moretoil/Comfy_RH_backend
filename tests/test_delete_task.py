from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_delete_task():
    """测试删除任务功能"""

    # 首先提交一个任务
    submit_response = client.post("/submit_task", json={
        "webappId": "1992884626727260162",
        "nodeInfoList": [
            {
                "nodeId": "4",
                "fieldName": "ckpt_name",
                "fieldValue": "sdxl-动漫_1.0.safetensors",
                "description": "ckpt_name"
            },
            {
                "nodeId": "5",
                "fieldName": "height",
                "fieldValue": "720",
                "description": "height"
            },
            {
                "nodeId": "5",
                "fieldName": "width",
                "fieldValue": "1288",
                "description": "width"
            },
            {
                "nodeId": "3",
                "fieldName": "seed",
                "fieldValue": "12345",
                "description": "seed"
            },
            {
                "nodeId": "3",
                "fieldName": "cfg",
                "fieldValue": "1.5",
                "description": "cfg"
            },
            {
                "nodeId": "3",
                "fieldName": "steps",
                "fieldValue": "15",
                "description": "steps"
            },
            {
                "nodeId": "38",
                "fieldName": "prompt",
                "fieldValue": "a beautiful landscape",
                "description": "正向提示词"
            },
            {
                "nodeId": "39",
                "fieldName": "prompt",
                "fieldValue": "blurry, low quality",
                "description": "负向提示词"
            }
        ]
    })

    print("提交任务响应:", submit_response.status_code, submit_response.json())

    if submit_response.status_code == 200:
        submit_data = submit_response.json()
        if submit_data.get("code") == 0:
            task_id = submit_data["data"]["taskId"]
            print(f"提交任务成功，任务ID: {task_id}")

            # 获取任务列表，确认任务存在
            get_response = client.get("/get_task")
            print("获取任务列表响应:", get_response.status_code, get_response.json())

            # 删除任务
            delete_response = client.post("/delete_task", json={
                "taskId": task_id
            })
            print("删除任务响应:", delete_response.status_code, delete_response.json())

            # 验证任务已被删除
            get_after_delete_response = client.get("/get_task")
            print("删除后获取任务列表响应:", get_after_delete_response.status_code, get_after_delete_response.json())

        else:
            print("提交任务失败:", submit_data)
    else:
        print("提交任务请求失败:", submit_response.status_code)

if __name__ == "__main__":
    test_delete_task()