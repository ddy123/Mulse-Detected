import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
from bleak import BleakScanner, BleakClient
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class BluetoothController:
    def __init__(self):
        self.client = None
        self.connected = False
        self.device_address = None
        self.device_name = None
        
    async def discover_devices(self):
        """发现附近的蓝牙设备，只返回名称以olfaction开头的设备"""
        devices = await BleakScanner.discover()
        
        # 过滤名称以olfaction开头的设备
        filtered_devices = []
        for device in devices:
            if device.name and device.name.lower().startswith('olfaction'):
                filtered_devices.append((device.name, device.address))
        
        return filtered_devices
    
    async def connect(self, address, name):
        """连接到指定蓝牙设备"""
        self.client = BleakClient(address)
        await self.client.connect()
        self.connected = True
        self.device_address = address
        self.device_name = name
        return True
    
    async def disconnect(self):
        """断开蓝牙连接"""
        if self.client:
            await self.client.disconnect()
        self.connected = False
        self.device_address = None
        self.device_name = None
        return True
    
    async def send_command(self, command):
        print(command)
        """通过蓝牙发送命令"""
        if not self.connected or not self.client:
            return False
        
        try:
            # 获取服务
            services = await self.client.get_services()
            
            # 查找第一个可写的特征
            for service in services:
                for char in service.characteristics:
                    if 'write' in char.properties:
                        # 将命令转换为字节并发送
                        command_bytes = command.encode('utf-8')
                        await self.client.write_gatt_char(char.uuid, command_bytes)
                        return True
            
            return False
        except Exception:
            return False

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, bluetooth_controller, *args, **kwargs):
        self.bluetooth_controller = bluetooth_controller
        super().__init__(*args, **kwargs)
    
    def _set_cors_headers(self):
        """设置 CORS 头部"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """处理预检请求 (CORS)"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求 - 返回服务状态"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        
        status = {
            "status": "running",
            "bluetooth_connected": self.bluetooth_controller.connected,
            "bluetooth_device": self.bluetooth_controller.device_name
        }
        
        response = json.dumps(status).encode('utf-8')
        self.wfile.write(response)
    
    def do_POST(self):
        """处理 POST 请求"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            command = data.get('command', '')
            
            if command:
                # 在新线程中发送蓝牙命令
                def send_ble_command():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(
                            self.bluetooth_controller.send_command(command)
                        )
                        
                    finally:
                        loop.close()
                
                threading.Thread(target=send_ble_command, daemon=True).start()
                
                response = {"status": "success", "message": f"命令 '{command}' 已发送"}
            else:
                response = {"status": "error", "message": "未提供命令"}
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            error_response = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

# GUI 部分保持不变...
class BluetoothGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("蓝牙控制服务")
        self.root.geometry("400x300")
        
        # 蓝牙控制器
        self.bluetooth_controller = BluetoothController()
        
        # HTTP 服务器
        self.http_server = None
        self.http_thread = None
        self.http_running = False
        self.http_port = 8080
        
        self.create_widgets()
        self.refresh_devices()
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 蓝牙设备部分
        device_frame = ttk.LabelFrame(main_frame, text="蓝牙设备", padding="5")
        device_frame.pack(fill=tk.X, pady=5)
        
        self.device_combo = ttk.Combobox(device_frame, state="readonly")
        self.device_combo.pack(fill=tk.X, padx=5, pady=5)
        
        btn_frame = ttk.Frame(device_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.refresh_btn = ttk.Button(btn_frame, text="刷新设备", command=self.refresh_devices)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = ttk.Button(btn_frame, text="连接", command=self.connect_device)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(btn_frame, text="断开", command=self.disconnect_device, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(device_frame, text="状态: 未连接")
        self.status_label.pack(pady=5)
        
        # HTTP 服务部分
        http_frame = ttk.LabelFrame(main_frame, text="HTTP 服务", padding="5")
        http_frame.pack(fill=tk.X, pady=5)
        
        port_frame = ttk.Frame(http_frame)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="端口:").pack(side=tk.LEFT, padx=5)
        self.port_entry = ttk.Entry(port_frame, width=10)
        self.port_entry.insert(0, str(self.http_port))
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        http_btn_frame = ttk.Frame(http_frame)
        http_btn_frame.pack(fill=tk.X, pady=5)
        
        self.start_http_btn = ttk.Button(http_btn_frame, text="启动 HTTP 服务", command=self.start_http_server)
        self.start_http_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_http_btn = ttk.Button(http_btn_frame, text="停止 HTTP 服务", command=self.stop_http_server, state=tk.DISABLED)
        self.stop_http_btn.pack(side=tk.LEFT, padx=5)
        
        self.http_status_label = ttk.Label(http_frame, text="HTTP 服务: 未启动")
        self.http_status_label.pack(pady=5)
        
        # 测试命令部分
        test_frame = ttk.LabelFrame(main_frame, text="测试命令", padding="5")
        test_frame.pack(fill=tk.X, pady=5)
        
        self.command_entry = ttk.Entry(test_frame)
        self.command_entry.pack(fill=tk.X, padx=5, pady=5)
        self.command_entry.bind('<Return>', self.send_test_command)
        
        self.send_btn = ttk.Button(test_frame, text="发送测试命令", command=self.send_test_command)
        self.send_btn.pack(pady=5)
    
    def refresh_devices(self):
        """刷新蓝牙设备列表"""
        threading.Thread(target=self._discover_devices_thread, daemon=True).start()
    
    def _discover_devices_thread(self):
        """在新线程中搜索蓝牙设备"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(self.bluetooth_controller.discover_devices())
            self.root.after(0, self._update_device_list, devices)
        finally:
            loop.close()
    
    def _update_device_list(self, devices):
        """更新设备列表"""
        device_list = []
        for name, addr in devices:
            display_name = f"{name or '未知设备'} ({addr})"
            device_list.append(display_name)
        
        self.device_combo['values'] = device_list
        if device_list:
            self.device_combo.current(0)
    
    def connect_device(self):
        """连接选中的蓝牙设备"""
        selected = self.device_combo.get()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个蓝牙设备")
            return
        
        try:
            addr = selected.split('(')[-1].rstrip(')')
        except:
            messagebox.showerror("错误", "设备格式错误")
            return
        
        threading.Thread(target=self._connect_device_thread, args=(addr, selected), daemon=True).start()
    
    def _connect_device_thread(self, addr, name):
        """在新线程中连接蓝牙设备"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(self.bluetooth_controller.connect(addr, name))
            self.root.after(0, self._update_connection_status, success, name)
        except Exception as e:
            self.root.after(0, self._update_connection_status, False, name)
        finally:
            loop.close()
    
    def _update_connection_status(self, success, name):
        """更新连接状态"""
        if success:
            self.status_label.config(text=f"状态: 已连接到 {name}")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="状态: 连接失败")
            messagebox.showerror("错误", f"连接设备失败: {name}")
    
    def disconnect_device(self):
        """断开蓝牙连接"""
        threading.Thread(target=self._disconnect_device_thread, daemon=True).start()
    
    def _disconnect_device_thread(self):
        """在新线程中断开蓝牙连接"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.bluetooth_controller.disconnect())
            self.root.after(0, self._update_disconnection_status)
        finally:
            loop.close()
    
    def _update_disconnection_status(self):
        """更新断开连接状态"""
        self.status_label.config(text="状态: 未连接")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
    
    def start_http_server(self):
        """启动 HTTP 服务"""
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字")
            return
        
        self.http_port = port
        self.http_thread = threading.Thread(target=self._run_http_server, daemon=True)
        self.http_thread.start()
        
        self.http_running = True
        self.start_http_btn.config(state=tk.DISABLED)
        self.stop_http_btn.config(state=tk.NORMAL)
        self.http_status_label.config(text=f"HTTP 服务: 运行在端口 {port}")
    
    def stop_http_server(self):
        """停止 HTTP 服务"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server = None
        
        self.http_running = False
        self.start_http_btn.config(state=tk.NORMAL)
        self.stop_http_btn.config(state=tk.DISABLED)
        self.http_status_label.config(text="HTTP 服务: 未启动")
    
    def _run_http_server(self):
        """运行 HTTP 服务器"""
        handler = lambda *args: HTTPRequestHandler(self.bluetooth_controller, *args)
        
        try:
            self.http_server = HTTPServer(('0.0.0.0', self.http_port), handler)
            self.http_server.serve_forever()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"HTTP 服务器错误: {e}"))
            self.root.after(0, self.stop_http_server)
    
    def send_test_command(self, event=None):
        """发送测试命令"""
        command = self.command_entry.get().strip()
        if not command:
            messagebox.showwarning("警告", "请输入命令")
            return
        
        if not self.bluetooth_controller.connected:
            messagebox.showwarning("警告", "未连接到蓝牙设备")
            return
        
        def send_command():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.bluetooth_controller.send_command(command))
            finally:
                loop.close()
        
        threading.Thread(target=send_command, daemon=True).start()
        self.command_entry.delete(0, tk.END)

def main():
    root = tk.Tk()
    app = BluetoothGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()