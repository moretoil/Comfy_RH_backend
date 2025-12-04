from fastapi import FastAPI, BackgroundTasks, Query, Body, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import json
import http.client
import time
import os
from dotenv import load_dotenv
from .models import SessionLocal, Task
from typing import Dict
import threading
import time
from datetime import datetime, timedelta
import copy
import pandas as pd

load_dotenv()

app = FastAPI()

# 全局缓存字典，线程安全
task_cache: Dict[str, dict] = {}
cache_lock = threading.Lock()

# 缓存清理函数
def cleanup_cache():
    while True:
        time.sleep(3600)  # 每小时清理一次
        with cache_lock:
            now = datetime.now()
            expired_keys = []
            for task_id, data in task_cache.items():
                if 'created_at' in data and isinstance(data['created_at'], str):
                    try:
                        created_time = datetime.fromisoformat(data['created_at'])
                        if (now - created_time).total_seconds() > 86400:  # 24小时过期
                            expired_keys.append(task_id)
                    except:
                        pass
            for key in expired_keys:
                del task_cache[key]


class NodeInfo(BaseModel):
    nodeId: str
    fieldName: str
    fieldValue: str
    description: Optional[str] = None

class SubmitTaskRequest(BaseModel):
    webappId: str
    nodeInfoList: List[NodeInfo]

class QueryTaskStatusRequest(BaseModel):
    taskId: str

class ModifyWorkflowRequest(BaseModel):
    image_list: List[str]  # 图像文件列表，控制添加的套数
    prompt: str = ""  # 节点2的prompt参数


class BatchT2IRequest(BaseModel):
    unet_name: str = ""  # 节点1的unet_name参数
    seed: int = 9  # 节点4的seed参数
    steps: int = 8  # 节点4的steps参数
    cfg: float = 1.0  # 节点4的cfg参数
    sampler_name: str = "dpmpp_2m"  # 节点4的sampler_name参数
    scheduler: str = "sgm_uniform"  # 节点4的scheduler参数
    denoise: float = 1.0  # 节点4的denoise参数
    prompt: str = ""  # 节点65的prompt参数
    width: int = 1024  # 节点55的width参数
    height: int = 1024  # 节点55的height参数

class SubmitWorkflowRequest(BaseModel):
    workflowId: str
    workflowType: str = "aichat"  # 默认为 aichat，可选值：aichat, custom

@app.get("/get_node_info")
async def get_node_info(webappId: str = Query(...)):
    api_key = os.getenv('RUNNINGHUB_API_KEY')
    conn = http.client.HTTPSConnection("www.runninghub.cn")
    headers = {'Host': 'www.runninghub.cn'}
    conn.request("GET", f"/api/webapp/apiCallDemo?apiKey={api_key}&webappId={webappId}", headers=headers)
    res = conn.getresponse()
    data = res.read()
    response = json.loads(data.decode("utf-8"))
    if response.get("code") == 0:
        filtered_node_info_list = []
        for node in response["data"]["nodeInfoList"]:
            filtered_node = {
                "nodeId": node.get("nodeId", ""),
                "fieldName": node.get("fieldName", ""),
                "fieldValue": node.get("fieldValue", ""),
                "description": node.get("description", "")
            }
            filtered_node_info_list.append(filtered_node)
        return filtered_node_info_list
    else:
        return []

@app.post("/change_aichat")
async def change_aichat(request: ModifyWorkflowRequest):
    """
    根据提供的图像列表和prompt动态修改AI Chat工作流
    """
    try:
        # 读取基础工作流文件
        import os.path
        base_workflow_path = os.path.join(os.path.dirname(__file__), "..", "config", "nano_api.json")

        with open(base_workflow_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 根据图像列表确定要添加的套数
        image_list = request.image_list
        num_sets = len(image_list)

        # 更新节点2的prompt参数
        if '2' in data and 'inputs' in data['2']:
            data['2']['inputs']['prompt'] = request.prompt

        # 获取当前最大的节点ID
        max_node_id = max(int(key) for key in data.keys())

        # 统计当前存在的图像缩放节点数量（通过查找class_type为"ImageResize+"的节点）
        resize_nodes = [key for key, value in data.items() if value.get("class_type") == "ImageResize+"]
        current_resize_count = len(resize_nodes)

        # 添加指定数量的节点对
        for i in range(num_sets):
            # 计算新节点编号
            load_image_num = max_node_id + 1 + (i * 2)  # LoadImage节点
            resize_num = max_node_id + 2 + (i * 2)      # ImageResize+节点

            # 从图像列表获取当前节点的图像文件
            image_file = image_list[i]

            # 添加LoadImage节点
            data[str(load_image_num)] = {
                "inputs": {
                    "image": image_file
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            }

            # 添加ImageResize+节点，连接到LoadImage节点
            data[str(resize_num)] = {
                "inputs": {
                    "width": 1280,
                    "height": 1280,
                    "interpolation": "nearest",
                    "method": "keep proportion",
                    "condition": "always",
                    "multiple_of": 0,
                    "image": [
                        str(load_image_num),
                        0
                    ]
                },
                "class_type": "ImageResize+",
                "_meta": {
                    "title": "图像缩放"
                }
            }

            # 计算当前要连接的目标参数名
            total_resize_count = current_resize_count + i  # 当前已有的+新增的（不包括当前这个）
            if total_resize_count == 0:
                input_name = 'images'  # 如果没有其他图像缩放节点，连接到'images'
            elif total_resize_count == 1:
                input_name = 'image1'  # 如果有1个，连接到'image1'
            else:
                # 如果有更多，使用'image2', 'image3'等格式
                input_name = f'image{total_resize_count}'

            # 更新节点1，添加对应参数，连接到新图像缩放节点
            data['1']['inputs'][input_name] = [str(resize_num), 0]

        # 保存修改后的工作流到本地文件
        output_path = os.path.join(os.path.dirname(__file__), "..", "config", "modified_workflow.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "code": 0,
            "message": "工作流修改成功",
            "data": {
                "modified_workflow": data,
                "added_sets_count": num_sets,
                "saved_path": output_path
            }
        }

    except FileNotFoundError:
        return {
            "code": 404,
            "message": f"基础工作流文件不存在: {base_workflow_path}"
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"修改工作流时发生错误: {str(e)}"
        }

from fastapi import UploadFile
@app.post("/upload")
async def upload_file(file: UploadFile):
    api_key = os.getenv('RUNNINGHUB_API_KEY')
    conn = http.client.HTTPSConnection("www.runninghub.cn")
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }

    body = []
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="apiKey"'.encode())
    body.append(b'')
    body.append(api_key.encode())

    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="fileType"'.encode())
    body.append(b'')
    body.append(b'input')

    filename = file.filename
    content_type = file.content_type

    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
    body.append(f'Content-Type: {content_type}'.encode())
    body.append(b'')
    file_content = await file.read()
    body.append(file_content)

    body.append(f'--{boundary}--'.encode())

    conn.request("POST", "/task/openapi/upload", b'\r\n'.join(body), headers)
    res = conn.getresponse()
    data = res.read()
    response = json.loads(data.decode("utf-8"))
    if response.get("code") == 0:
        return {
            "fileName": response["data"]["fileName"],
            "msg": "success"
        }
    else:
        return response

@app.post("/submit_task")
async def submit_task(request: SubmitTaskRequest, background_tasks: BackgroundTasks = BackgroundTasks()):
    webappId = request.webappId
    nodeInfoList = request.nodeInfoList
    print("✅ 提取的 nodeInfoList:", nodeInfoList)
    api_key = os.getenv('RUNNINGHUB_API_KEY')
    conn = http.client.HTTPSConnection("www.runninghub.cn")
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json'
    }
    node_info_dicts = []
    for node in nodeInfoList:
        node_dict = {
            "nodeId": node.nodeId,
            "fieldName": node.fieldName,
            "fieldValue": node.fieldValue,
            "description": node.description
        }
        node_info_dicts.append(node_dict)

    payload = {
        "webappId": webappId,
        "apiKey": api_key,
        "nodeInfoList": node_info_dicts
    }
    conn.request("POST", "/task/openapi/ai-app/run", json.dumps(payload), headers)
    res = conn.getresponse()
    data = res.read()
    response = json.loads(data.decode("utf-8"))

    if response.get("code") == 0:
        task_id = response["data"]["taskId"]
        print(f"提交任务成功，任务ID为：{task_id}")

        # 保存到数据库和缓存
        db = SessionLocal()
        try:
            # 将nodeInfoList转换为JSON字符串存储
            node_info_json = json.dumps([node.dict() for node in nodeInfoList])

            # 从响应中获取status，如果不存在则默认为PENDING
            initial_status = response["data"].get("taskStatus", "PENDING") if "data" in response and isinstance(response["data"], dict) else "PENDING"

            new_task = Task(
                task_id=task_id,
                webapp_id=webappId,
                node_info_list=node_info_json,
                status=initial_status
            )
            db.add(new_task)
            db.commit()

            # 添加到缓存
            with cache_lock:
                task_cache[task_id] = {
                    "id": new_task.id,
                    "task_id": task_id,
                    "webapp_id": webappId,
                    "node_info_list": node_info_json,
                    "status": "PENDING",
                    "created_at": datetime.now().isoformat()
                }
        except Exception as e:
            db.rollback()
            print(f"保存任务数据失败: {e}")
        finally:
            db.close()

        # 确保数据库提交完成后再启动后台任务
        background_tasks.add_task(update_task_status, api_key, task_id)

        return response
    else:
        return response

@app.post("/task/query_task_status")
async def query_task_status(request: QueryTaskStatusRequest):
    api_key = os.getenv('RUNNINGHUB_API_KEY')
    conn = http.client.HTTPSConnection("www.runninghub.cn")
    headers = {
        'Host': 'www.runninghub.cn',
        'Content-Type': 'application/json'
    }

    payload = {
        "apiKey": api_key,
        "taskId": request.taskId
    }
    conn.request("POST", "/task/openapi/outputs", json.dumps(payload), headers)
    res = conn.getresponse()
    data = res.read()
    response = json.loads(data.decode("utf-8"))


    return response

@app.get("/get_task")
async def get_task():
    """
    获取所有任务信息，合并缓存和数据库的数据
    """
    all_tasks = []

    with cache_lock:
        # 先从缓存获取数据
        all_tasks.extend(list(task_cache.values()))

    # 从数据库获取所有任务
    db = SessionLocal()
    try:
        tasks = db.query(Task).all()
        db_task_ids = {task.task_id for task in tasks}  # 数据库中的任务ID集合
        cached_task_ids = {task['task_id'] for task in all_tasks}  # 缓存中的任务ID集合

        # 获取只在数据库中但不在缓存中的任务
        missing_in_cache = [task for task in tasks if task.task_id not in cached_task_ids]

        # 添加只在数据库中的任务到结果
        for task in missing_in_cache:
            task_data = {
                "id": task.id,
                "task_id": task.task_id,
                "webapp_id": task.webapp_id,
                "node_info_list": task.node_info_list,
                "file_url": task.file_url,
                "file_type": task.file_type,
                "task_cost_time": task.task_cost_time,
                "status": task.status,
                "created_at": task.created_at.isoformat() if task.created_at else None
            }
            all_tasks.append(task_data)

        # 更新缓存，包含所有数据库中的任务
        with cache_lock:
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "task_id": task.task_id,
                    "webapp_id": task.webapp_id,
                    "node_info_list": task.node_info_list,
                    "file_url": task.file_url,
                    "file_type": task.file_type,
                    "task_cost_time": task.task_cost_time,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
                task_cache[task.task_id] = task_data

        return all_tasks
    except Exception as e:
        return {"error": f"Database error: {e}"}
    finally:
        db.close()



@app.post("/delete_task")
async def delete_task(request: QueryTaskStatusRequest):
    """
    删除指定任务，同时从数据库和缓存中移除
    """
    task_id = request.taskId
    
    # 从数据库删除
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return {"code": 404, "message": "任务不存在"}
        
        # 从数据库删除任务
        db.delete(task)
        db.commit()
        
        # 从缓存中删除
        with cache_lock:
            if task_id in task_cache:
                del task_cache[task_id]
        
        return {"code": 0, "message": "任务删除成功", "data": {"taskId": task_id}}
    
    except Exception as e:
        db.rollback()
        return {"code": 500, "message": f"删除任务失败: {e}"}
    
    finally:
        db.close()

@app.post("/submit_workflow")
async def submit_workflow(request: SubmitWorkflowRequest, background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    提交工作流到 RunningHub API
    """
    try:
        # 根据 workflowType 选择工作流文件
        if request.workflowType == "custom":
            workflow_path = os.path.join(os.path.dirname(__file__), "..", "config", "custom_workflow.json")
        else:
            workflow_path = os.path.join(os.path.dirname(__file__), "..", "config", "modified_workflow.json")

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_json = f.read()

        api_key = os.getenv('RUNNINGHUB_API_KEY')
        conn = http.client.HTTPSConnection("www.runninghub.cn")

        payload = json.dumps({
            "apiKey": api_key,
            "workflowId": request.workflowId,
            "workflow": workflow_json,
        })

        headers = {
            'Host': 'www.runninghub.cn',
            'Content-Type': 'application/json'
        }

        conn.request("POST", "/task/openapi/create", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_data = data.decode("utf-8")

        try:
            response_json = json.loads(response_data)

            if response_json.get("code") == 0:
                task_id = response_json["data"]["taskId"]
                print(f"提交工作流任务成功，任务ID为：{task_id}")

                # 保存到数据库和缓存
                db = SessionLocal()
                try:
                    # 从响应中获取status，如果不存在则默认为PENDING
                    initial_status = response_json["data"].get("taskStatus", "PENDING") if "data" in response_json and isinstance(response_json["data"], dict) else "PENDING"

                    new_task = Task(
                        task_id=task_id,
                        webapp_id=f"workflow_{request.workflowId}",  # 使用workflow作为webapp_id标识
                        node_info_list=workflow_json,  # 存储完整的 workflow JSON
                        status=initial_status
                    )
                    db.add(new_task)
                    db.commit()

                    # 添加到缓存
                    with cache_lock:
                        task_cache[task_id] = {
                            "id": new_task.id,
                            "task_id": task_id,
                            "webapp_id": new_task.webapp_id,
                            "node_info_list": new_task.node_info_list,
                            "status": "PENDING",
                            "created_at": datetime.now().isoformat()
                        }

                    # 确保数据库提交完成后再启动后台任务
                    background_tasks.add_task(update_task_status, api_key, task_id)

                except Exception as e:
                    db.rollback()
                    print(f"保存工作流任务数据失败: {e}")
                finally:
                    db.close()

                return response_json
            else:
                return response_json

        except json.JSONDecodeError:
            return {
                "code": 500,
                "message": "API响应解析失败",
                "data": response_data
            }

    except FileNotFoundError:
        return {
            "code": 404,
            "message": f"工作流文件不存在: {workflow_path}，请确保文件存在"
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"提交工作流失败: {str(e)}"
        }

@app.post("/batch_T2I")
async def batch_t2i(request: BatchT2IRequest):
    """
    批量文本到图像：修改 backend_asyn/config/batch_T2I_api.json 的节点信息
    """
    try:
        # 读取基础工作流文件
        base_workflow_path = os.path.join(os.path.dirname(__file__), "..", "config", "batch_T2I_api.json")

        with open(base_workflow_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 更新节点1的unet_name
        if request.unet_name and '1' in data and 'inputs' in data['1']:
            data['1']['inputs']['unet_name'] = request.unet_name

        # 更新节点4的参数
        if '4' in data and 'inputs' in data['4']:
            if request.seed is not None:
                data['4']['inputs']['seed'] = request.seed
            if request.steps is not None:
                data['4']['inputs']['steps'] = request.steps
            if request.cfg is not None:
                data['4']['inputs']['cfg'] = request.cfg
            if request.sampler_name:
                data['4']['inputs']['sampler_name'] = request.sampler_name
            if request.scheduler:
                data['4']['inputs']['scheduler'] = request.scheduler
            if request.denoise is not None:
                data['4']['inputs']['denoise'] = request.denoise

        # 更新节点65的prompt
        if request.prompt and '65' in data and 'inputs' in data['65']:
            data['65']['inputs']['prompt'] = request.prompt

        # 更新节点55的width和height
        if '55' in data and 'inputs' in data['55']:
            if hasattr(request, 'width') and request.width is not None:
                data['55']['inputs']['width'] = request.width
            if hasattr(request, 'height') and request.height is not None:
                data['55']['inputs']['height'] = request.height

        # 保存修改后的工作流到文件
        output_path = os.path.join(os.path.dirname(__file__), "..", "config", "custom_workflow.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {
            "code": 0,
            "message": "批量文生图参数修改成功",
            "data": {
                "updated_nodes": {
                    "node_1_unet_name": request.unet_name,
                    "node_4_seed": request.seed,
                    "node_4_steps": request.steps,
                    "node_4_cfg": request.cfg,
                    "node_4_sampler_name": request.sampler_name,
                    "node_4_scheduler": request.scheduler,
                    "node_4_denoise": request.denoise,
                    "node_65_prompt": request.prompt,
                    "node_55_width": request.width if hasattr(request, 'width') else None,
                    "node_55_height": request.height if hasattr(request, 'height') else None
                },
                "saved_path": output_path
            }
        }

    except FileNotFoundError:
        return {
            "code": 404,
            "message": f"工作流文件不存在: {base_workflow_path}"
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"修改工作流失败: {str(e)}"
        }


async def update_task_status(apiKey: str, taskId: str):
    while True:
        api_key = os.getenv('RUNNINGHUB_API_KEY')
        conn = http.client.HTTPSConnection("www.runninghub.cn")
        headers = {
            'Host': 'www.runninghub.cn',
            'Content-Type': 'application/json'
        }
        payload = {
            "apiKey": api_key,
            "taskId": taskId
        }
        conn.request("POST", "/task/openapi/outputs", json.dumps(payload), headers)
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))

        if response.get("code") == 0:
            # 更新数据库和缓存
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.task_id == taskId).first()
                if not task:
                    print(f"任务 {taskId} 不存在，可能是提交任务后尚未保存到数据库")
                    break

                if response["data"]:
                    # 获取所有输出结果
                    all_outputs = response["data"] if isinstance(response["data"], list) else []

                    # 提取所有文件 URL
                    all_file_urls = []
                    for output in all_outputs:
                        if isinstance(output, dict) and "fileUrl" in output:
                            all_file_urls.append(output["fileUrl"])

                    # 将所有文件 URL 存储为 JSON 字符串
                    all_file_urls_json = json.dumps(all_file_urls, ensure_ascii=False)

                    # 更新数据库
                    # 取第一个输出的 file_type 和 task_cost_time 作为代表
                    first_output = all_outputs[0] if all_outputs else {}
                    task.file_url = all_file_urls_json  # 存储所有文件 URL
                    task.file_type = first_output.get("fileType", "")
                    task.task_cost_time = first_output.get("taskCostTime", "")
                    task.status = "COMPLETED"
                    db.commit()

                    # 更新缓存
                    with cache_lock:
                        if taskId in task_cache:
                            task_cache[taskId].update({
                                "file_url": all_file_urls_json,  # 存储所有文件 URL
                                "file_type": first_output.get("fileType", ""),
                                "task_cost_time": first_output.get("taskCostTime", ""),
                                "status": "COMPLETED"
                            })

            except Exception as e:
                db.rollback()
                print(f"更新任务数据失败: {e}")
            finally:
                db.close()

            break

        time.sleep(5)


@app.post("/excel_division")
async def excel_division(file: UploadFile = File(...)):
    """
    读取上传的Excel文件，将第一列的内容拼接成字符串，用换行符分隔
    """
    try:
        # 检查文件类型
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            return {
                "code": 400,
                "message": "只支持上传Excel文件(.xlsx, .xls)或CSV文件(.csv)"
            }

        # 创建临时文件来保存上传的文件
        import tempfile
        import os

        # 读取上传文件的内容
        contents = await file.read()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(contents)
            temp_file_path = temp_file.name

        try:
            # 根据文件类型读取Excel或CSV
            if file.filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(temp_file_path)
            else:  # CSV文件
                df = pd.read_csv(temp_file_path)

            # 检查是否有数据
            if df.empty:
                return {
                    "code": 400,
                    "message": "Excel文件为空"
                }

            # 获取第一列数据
            first_column = df.iloc[:, 0]  # 获取第一列的所有行

            # 将第一列的数据转换为字符串列表，并去除空值
            str_list = [str(value) for value in first_column if pd.notna(value)]

            # 用换行符连接所有字符串
            result = "\n".join(str_list)

            return {
                "code": 0,
                "message": "Excel文件处理成功",
                "data": {
                    "result": result,
                    "rows_count": len(str_list)
                }
            }
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)

    except Exception as e:
        return {
            "code": 500,
            "message": f"处理Excel文件失败: {str(e)}"
        }