from py_taskcenter import public
from py_tools import tools_common
from py_ui import device_info_ui

error_msg_prefix = "error: device_info: "


class DeviceInfo:

    def __init__(self, fun_property=None, parent=None):
        """初始化"""
        self.fun_property = fun_property
        self.parent = parent

        self.gui_id = self.fun_property['gui_id']
        self.fun_name = self.fun_property['fun_name']

        # 跟主进程通信的buffer
        self.buffer_write = self.fun_property['buffer_write']
        # task center的地址
        self.task_center_gui_id = self.fun_property['task_center_gui_id']
        self.main_gui_id = self.fun_property['main_gui_id']

        # 显示信息
        # 用于显示到text，还有就是生成报告相关的配置
        # 创建结果文件
        self.local_show_text = self.fun_property['local_show_text']

        # 主界面
        self.main_window = self.fun_property['main_window']
        self.win_main = device_info_ui.Ui_Form()

        # 界面是否退出
        self.exited = False

    def create_main_gui(self):
        """创建主界面"""
        self.win_main.setupUi(self.parent)
        self.win_main.query_btn.clicked.connect(self.query_device_info)
        self.win_main.clear_btn.clicked.connect(lambda: self.win_main.show_text.clear())

        self.local_show_text.add_show_text(self.gui_id, self.win_main.show_text)

    def write(self, rev_data=None):
        """接收到的数据"""
        try:
            print('device_info: received: ')
            print(rev_data)
            print()
            if isinstance(rev_data, dict):
                if 'data' in rev_data.keys() and 'task_type' in rev_data['data'].keys():
                    if str(rev_data['data']['task_type']) == \
                            str(public.task_identify[public.fun_name_device]["task_type"]["query_device_info"]):
                        self.response_of_query_device_info(rev_data)
                    elif str(rev_data['data']['task_type']) == \
                            str(public.task_identify[self.fun_name]["task_type"]['show_info']):
                        self.task_of_show_info(rev_data)
                    else:
                        self.response_of_undefined_task_type(rev_data)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'write')
            self.show_data_to_text(error_msg)

    def response_of_query_device_info(self, rev_data=None):
        """添加设备"""
        try:
            error_msg = rev_data['data'][public.error_msg_name]
            if rev_data['data']['task_success']:
                info = rev_data['data'][rev_data['data']['task_type']]
                # print(info)
                if not info:
                    self.show_data_to_text("无设备信息！\n")
                else:
                    msg = "设备信息：\n"
                    online = {True: '在线', False: '离线'}
                    for host, host_info in info.items():
                        msg += "Host：" + host + "，名称：" + host_info['name'] + \
                               "，项目：" + host_info['project_name'] + "，类别：" + host_info['net_name'] + \
                               "，当前：" + online[host_info['online']] + "\n"
                    self.show_data_to_text(msg)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "response_of_query_device_info")
        if error_msg:
            self.show_data_to_text(error_msg)

    def task_of_show_info(self, rev_data=None):
        """添加设备"""
        try:
            msg = rev_data['data']['append_data']
            if msg:
                if not isinstance(msg, str):
                    msg = str(msg)
                self.show_data_to_text(msg)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "response_of_show_info")
            self.show_data_to_text(error_msg)

    def response_of_undefined_task_type(self, rev_data=None):
        """未定义的功能"""
        try:
            print(error_msg_prefix + 'response_of_undefined_task_type')
            print(rev_data)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "response_of_undefined_task_type")
            self.show_data_to_text(error_msg)

    def query_device_info(self):
        """查询设备信息"""
        data = {
            'task_type':
                public.task_identify[public.fun_name_device]["task_type"]["query_device_info"]
        }
        self.send_request_to_task_center(data, public.fun_name_device)

    def show_data_to_text(self, content=None, additional_msg=''):
        """显示数据"""
        self.local_show_text.local_show_everything_to_text(content, additional_msg, self.gui_id)

    def send_request_to_task_center(self, data=None, task_fun_name=""):
        """给task center发送服务请求"""
        if not task_fun_name:
            task_fun_name = self.fun_name
        task_id = public.generate_task_id(task_fun_name)
        msg_id = public.generate_msg_id()

        msg = public.encode_transfer_msg(self.gui_id,
                                         self.main_window.task_center_gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.send_msg(msg)

    def send_msg(self, content=None):
        """发送数据"""
        try:
            print('device info ' + self.gui_id + " 发送数据：")
            print(content)
            print()
            if self.main_window.buffer_read:
                self.main_window.buffer_read.write(content)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'send_msg')
            self.show_data_to_text(error_msg)

    def gui_exit(self):
        """退出"""
        """关闭窗口事件"""
        try:
            pass
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "gui_exit")
            print(error_msg)
        self.exited = True
