import threading
import time

from py_taskcenter import public
from py_tools import tools_common

error_msg_prefix = "error: watchdog: "


class WatchDog(threading.Thread):
    """定期发送命令给主界面，如果主界面没有回复，就退出进程"""
    Roles = {0: 'server', 1: 'client'}

    def __init__(self, role=0, client_buffer=None, gui_id=None, main_gui_id=None, send_request_to_self=None):
        threading.Thread.__init__(self)
        self.role = role
        self.child_process_pipe = list()
        self.client_buffer = client_buffer
        # 标记子进程
        self.gui_id = gui_id
        self.main_gui_id = main_gui_id
        # 是否退出线程
        self.to_exit = False
        # 间隔一段时间发送命令
        self.interval_s = 5
        # 等待主界面返回数据的时间，即如果5s内没有返回数据，则退出进程
        self.wait_s = 10
        # 如果超过该次数，再退出
        self.max_count = 5
        # 累计的次数，
        self.no_response_count = 0
        # 主界面返回了信息
        self.response = True
        # 线程锁
        self.lock = threading.Lock()
        # 发送数据到子进程
        self.send_request_to_self = send_request_to_self
        # 客户端发送请求时用到的变量
        self.task_id = public.generate_task_id(public.fun_name_main_gui)

    def set_response(self, response=False):
        """投喂"""
        try:
            self.lock.acquire()
            self.response = response
        except Exception as e:
            error_msg = (e.args, error_msg_prefix + "set_response")
            print(error_msg)
        finally:
            self.lock.release()

    def get_response(self):
        """判断返回的数据"""
        try:
            self.lock.acquire()
            if not self.response:
                self.no_response_count += 1
                if self.no_response_count >= self.max_count:
                    data = {
                        'task_type': public.common_task_type["main_gui_no_response"]
                    }
                    self.send_request_to_self(data)
                    self.to_exit = True
            # print('self.response') print(self.response) print() print('*************\nget_response:\n' + str(
            # self.gui_id) + ': ' + str(self.response) + '\n*************\n')
        except Exception as e:
            error_msg = (e.args, error_msg_prefix + "run")
            print(error_msg)
        finally:
            self.lock.release()

    def run(self):
        """执行看门狗的任务"""
        while True:
            try:
                if self.Roles[self.role] == 'server':
                    # 作为服务器，持续监听pipe的数据
                    # 如果接收到请求，就返回响应
                    for buffer in self.child_process_pipe:
                        while not buffer.empty():
                            if self.to_exit:
                                break
                            rev_data = buffer.get()
                            response_of_watch_dog(rev_data, buffer)
                            # print('-----------\nresponse_of_watch_dog:\n' + str(rev_data) + '\n----------\n')
                elif self.Roles[self.role] == 'client':
                    # 作为客户端，定期发送请求
                    # 发送请求后等待服务器的响应
                    # 如果没有接收到响应，就通知进程退出
                    tools_common.time_sleep(self.interval_s, self.to_exit)
                    if self.to_exit:
                        break
                    self.set_response(False)
                    if self.to_exit:
                        break
                    data = {
                        'task_type': public.common_task_type["watch_dog"]
                    }
                    self.send_request_to_main_gui(data)
                    if self.to_exit:
                        break
                    # time.sleep(self.wait_s)
                    tools_common.time_sleep(self.wait_s, self.to_exit)
                    if self.to_exit:
                        break
                    while not self.client_buffer.empty():
                        rev_data = self.client_buffer.get()
                        if str(rev_data['data']['task_type']) == str(public.common_task_type['watch_dog']):
                            self.set_response(rev_data['data']['task_success'])
                    self.get_response()
                    if self.to_exit:
                        break
                else:
                    print(error_msg_prefix + '看门狗角色定义错误！\n')
                    break
                time.sleep(0.001)
            except Exception as e:
                error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'WatchDog2: run')
                print(error_msg)

    def send_request_to_main_gui(self, data=None):
        """发送数据到主界面"""
        msg_id = public.generate_msg_id()
        msg = public.encode_transfer_msg(self.gui_id,
                                         self.main_gui_id,
                                         self.task_id,
                                         msg_id,
                                         data)
        self.client_buffer.write(msg)


def response_of_watch_dog(rev_data=None, buffer=None):
    """看门狗"""
    try:
        if str(rev_data['data']['task_type']) == str(public.common_task_type['watch_dog']) and \
                public.check_transfer_msg_format(rev_data):
            rev_data['data']['task_success'] = True
            rev_data['task_id'] = \
                public.generate_task_id_by_fun_id(
                    public.get_actual_source_id(rev_data['source_id']).split('_')[0])
            msg = public.encode_transfer_msg(rev_data['destination_id'],
                                             rev_data['source_id'],
                                             rev_data['task_id'],
                                             rev_data['msg_id'],
                                             rev_data['data'])
            buffer.write(msg)
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "response_of_watch_dog")
        print(error_msg)
