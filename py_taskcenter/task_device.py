import copy
import threading
import time

from py_taskcenter import public
from py_tools import tools_common

error_msg_prefix = 'error: task_device: '


class TaskDevice:

    def __init__(self):
        self.fun_name = ''
        self.fun_property = None
        self.gui_id = ''
        self.task_center_gui_id = ''

        # 所有的请求都写在这个buffer，由统一的主线程读取并响应
        self.buffer_write = None

        # 所有的设备，{ip: one_device}
        # 一个ip就是一台设备，一台设备只属于一个类别，一个ip只能创建一次一个设备，跟登陆的用户密码都无关
        self.device_dict = {}

        # 存储设备信息的数据库
        self.result_path = ''

        # 界面的地址
        self.gui_dst = None

        # 后台检查设备是否在线线程
        self.check_thread = None

        self.exited = False

    def start(self):
        """需要一个start函数，做初始化"""
        self.result_path = self.fun_property['path'][public.fun_result_path]
        # 后台检查设备是否在线线程
        self.check_thread = threading.Thread(target=self.check_online, args=())
        self.check_thread.setDaemon(True)
        self.check_thread.start()

    def check_online(self):
        """检查设备是否在线"""
        try:
            count = 0
            while True:
                # 定期检查ip是否可以ping通
                count += 1
                if count >= 1000:
                    count = 0
                    state_changed_host = dict()
                    for host, device_temp in self.device_dict.items():
                        state_changed, cur_state = device_temp.check_online_state_change()
                        if state_changed:
                            state_changed_host[host] = cur_state
                    if state_changed_host:
                        self.send_check_result_to_gui(state_changed_host)
                time.sleep(0.0005)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'ping_task')
            print(error_msg)

    def write(self, rev_data=None):
        """响应任务"""
        print('Task Device: 接收数据:')
        print(rev_data)
        print()
        if isinstance(rev_data, dict):
            if 'data' in rev_data.keys() and 'task_type' in rev_data['data'].keys():
                if str(rev_data['data']['task_type']) == \
                        str(public.task_identify[self.fun_name]["task_type"]['add_device']):
                    self.add_device(rev_data)
                elif str(rev_data['data']['task_type']) == \
                        str(public.task_identify[self.fun_name]['task_type']['delete_device']):
                    self.delete_device(rev_data)
                elif str(rev_data['data']['task_type']) == \
                        str(public.task_identify[self.fun_name]['task_type']['query_device_info']):
                    self.query_device_info(rev_data)
                else:
                    self.undefined_task_type(rev_data)

    def add_device(self, rev_data=None):
        """添加一个设备"""
        try:
            host_info_list = rev_data['data']['append_data']
            host_info_success = []
            host_info_msg = []
            for i in range(len(host_info_list)):
                host_info = host_info_list[i]
                success, error_msg = self._connect_host_local(host_info)
                host_info_success.append(success)
                host_info_msg.append(error_msg)

            rev_data['data']['task_success'] = True
            rev_data['data'][rev_data['data']['task_type']] = host_info_success
            rev_data['data'][public.error_msg_name] = host_info_msg

        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'add_device')
            rev_data['data']['task_success'] = False
            rev_data['data'][public.error_msg_name] = error_msg

        public.send_response(self.send_msg,
                             rev_data,
                             rev_data['data'])

        if not self.gui_dst:
            rev_data_temp = rev_data.copy()
            rev_data_temp.pop('data')
            self.gui_dst = rev_data_temp
            self.gui_dst['data'] = {}

    def delete_device(self, rev_data=None):
        """删除设备"""
        try:
            error_msg = ''
            ip_list = rev_data['data']['append_data']
            for ip in ip_list:
                if ip in self.device_dict.keys():
                    self.device_dict.pop(ip)

            rev_data['data']['task_success'] = True
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'delete_device')
            rev_data['data']['task_success'] = False
        rev_data['data'][public.error_msg_name] = error_msg
        public.send_response(self.send_msg,
                             rev_data,
                             rev_data['data'])

    def query_device_info(self, rev_data=None):
        """查询设备信息"""
        try:
            error_msg = ''
            info = {}
            for host, device_temp in self.device_dict.items():
                info[host] = device_temp.host_info
                info[host].update({'online': device_temp.online_state})
            rev_data['data'][rev_data['data']['task_type']] = info
            rev_data['data']['task_success'] = True
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'query_device_info')
            rev_data['data']['task_success'] = False
        rev_data['data'][public.error_msg_name] = error_msg
        public.send_response(self.send_msg,
                             rev_data,
                             rev_data['data'])

    def undefined_task_type(self, rev_data=None):
        """未定义的任务"""
        rev_data['data']['task_success'] = False
        rev_data['data'][public.error_msg_name] = '请求的任务未定义！'
        public.send_response(self.send_msg,
                             rev_data,
                             rev_data['data'])

    def send_msg(self, content=None):
        """发送数据"""
        try:
            print('Task Device: 发送数据:')
            print(content)
            print()
            if self.buffer_write:
                self.buffer_write.put(content)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'send_msg')
            print(error_msg)

    def _connect_host_local(self, host_info=None):
        """登陆设备"""
        error_msg = ''
        success = False
        try:
            # 检查ip是否已经存在
            host = host_info['host']
            if host in self.device_dict.keys():
                # 如果ip已经存在，不再新建设备，返回错误
                # 20221010，重新登陆设备
                device_temp = self.device_dict[host]
                if not device_temp.online:
                    # 根据host_info的信息登陆设备
                    device_temp.login()
                    # 登陆成功
                    success = True
            else:
                # 如果ip不存在
                # 创建设备
                device_temp = OneDevice(host_info)
                device_temp.login()
                self.device_dict[host] = device_temp
                # 登陆成功
                success = True
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + '_connect_host_local')
        return success, error_msg

    def send_check_result_to_gui(self, state_changed_host=None):
        """将ping的结果发送回界面"""
        try:
            data = {'task_type': public.task_identify[self.fun_name]['task_type']['online_state_changed'],
                    'append_data': state_changed_host}
            public.send_response(self.send_msg,
                                 self.gui_dst,
                                 data)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'send_ping_result_to_gui')
            print(error_msg)

    def exit_program(self):
        """退出程序"""
        try:
            pass
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'exit_program')
            print(error_msg)
        finally:
            self.exited = True


class OneDevice:

    def __init__(self, host_info=None):
        """初始化"""
        self.host_info = host_info
        self.online_state = False
        self.last_online_state = False
        self.lock = threading.Lock()

    def login(self):
        """登陆设备"""
        self.online_state = True
        th = threading.Thread(target=self.set_online_state, args=())
        th.setDaemon(True)
        th.start()

    def set_online_state(self):
        """模拟设置设备在线状态"""
        try:
            while True:
                self.lock.acquire()
                self.online_state = not self.online_state
                self.lock.release()
                time.sleep(5)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'set_online_state')
            print(error_msg)

    def check_online_state_change(self):
        """检查状态变化"""
        changed = False
        cur_state = None
        try:
            self.lock.acquire()
            cur_state = copy.deepcopy(self.online_state)
            if self.online_state != self.last_online_state:
                changed = True
                self.last_online_state = self.online_state
            self.lock.release()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'check_online_state_change')
            print(error_msg)
        return changed, cur_state
