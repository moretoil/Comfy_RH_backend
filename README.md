# Comfy_RH_backend

FastAPI后端服务，集成RunningHub API的AI图像生成工作流。

## 功能特性

- 任务提交和状态查询
- 工作流动态修改
- 批量文本到图像生成
- 文件上传处理
- Excel数据处理

## API接口

### 任务管理
- `POST /submit_task` - 提交AI任务
- `POST /task/query_task_status` - 查询任务状态
- `GET /get_task` - 获取所有任务
- `POST /delete_task` - 删除任务

### 工作流管理
- `POST /submit_workflow` - 提交工作流
- `POST /change_aichat` - 修改AI Chat工作流
- `POST /batch_T2I` - 批量文生图参数修改

### 文件处理
- `POST /upload` - 文件上传
- `POST /excel_division` - Excel文件处理

### 其他
- `GET /get_node_info` - 获取节点信息

## 安装运行

```bash
pip install -r requirements.txt
python scripts/run_server.py
```

## 环境配置

在`.env`文件中配置：
```
RUNNINGHUB_API_KEY=your_api_key_here
```

## 技术栈

- FastAPI
- SQLAlchemy
- SQLite
- Pandas
- RunningHub API