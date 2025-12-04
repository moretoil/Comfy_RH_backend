#!/usr/bin/env python3
import json
import requests
import time

def test_submit_task():
    """
    测试提交任务功能，检查数据库连接是否正常
    """
    # 用户提供的测试数据
    test_data = {
        "webappId": "1992766006175264770",
        "nodeInfoList": [
            {
                "nodeId": "15",
                "fieldName": "text",
                "fieldValue": "upperbody shot, 1girl,solo,chibi,long hairs, happy, laugh, hugging a teddy bear, looking at viewers, dancing stand, cute, soft color, flowers in background, many flowers, among flowers, best quality, highres, delicate details,",
                "description": "正面prompt（英文）"
            }
        ]
    }
    
    try:
        print("开始测试submit_task接口...")
        # 调用submit_task接口
        response = requests.post(
            "http://127.0.0.1:8000/submit_task",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"接口响应状态码: {response.status_code}")
        print(f"接口响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        # 检查响应
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                task_id = data["data"]["taskId"]
                print(f"任务提交成功，task_id: {task_id}")
                
                # 测试获取任务列表
                print("\n测试获取任务列表...")
                get_tasks_response = requests.get("http://127.0.0.1:8000/get_task")
                print(f"获取任务列表响应: {json.dumps(get_tasks_response.json(), ensure_ascii=False, indent=2)}")
                
                return True
            else:
                print(f"接口返回错误: {data.get('msg')}")
                return False
        else:
            print(f"接口调用失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 测试submit_task数据库连接 ===")
    success = test_submit_task()
    if success:
        print("\n✅ 测试通过: submit_task功能正常工作")
    else:
        print("\n❌ 测试失败: submit_task功能存在问题")
