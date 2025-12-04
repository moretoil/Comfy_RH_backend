import uvicorn
import socket
import subprocess
import sys
import time
import os
from multiprocessing import freeze_support

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    try:
        if sys.platform == "win32":
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid])
                    print(f"已终止占用端口 {port} 的进程 (PID: {pid})")
                    return True
        else:
            result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
            for line in result.stdout.split('\n')[1:]:
                if line:
                    pid = line.split()[1]
                    subprocess.run(['kill', '-9', pid])
                    print(f"已终止占用端口 {port} 的进程 (PID: {pid})")
                    return True
        return False
    except Exception as e:
        print(f"释放端口时出错: {e}")
        return False

if __name__ == "__main__":
    freeze_support()

    # 添加项目路径到sys.path
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_dir)

    port = 8000
    if is_port_in_use(port):
        print(f"端口 {port} 已被占用，正在尝试释放...")
        if kill_process_on_port(port):
            time.sleep(1)  # 等待端口释放
            print("端口已释放")
        else:
            print("无法释放端口，程序将退出")
            sys.exit(1)

    print("服务器将在 http://127.0.0.1:8000 启动")
    print("访问 http://127.0.0.1:8000/docs 查看API文档")

    # 不使用reload模式，避免多进程问题
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)