"""
承接所有任务，只有此一个进程
"""
import time
from multiprocessing import Process

from py_protocol import com_protocol
from py_taskcenter import task_device, public
from py_tools import tools_common
from py_watchdog.watchdog import WatchDog

error_msg_prefix = "error: task_center: "


class TaskCenter(Process):

    def __init__(self, input_property=None):
        """初始化"""
        Process.__init__(self)
        try:
            # 主进程提供的一些信息
            self.input_property = input_property

            # 和main_gui通信的pipe
            self.task_gui_buffer = self.input_property['gui_pipe']
            # 看门狗之间的通信
            self.watch_dog_gui_task_pipe_child = self.input_property['watch_dog_pipe']

            # task center的gui_id
            self.gui_id = self.input_property['gui_id']
            self.main_gui_id = self.input_property['main_gui_gui_id']
            self.main_gui_fun_name = self.input_property['main_gui_fun_name']
            # 主界面的名称
            self.fun_name = self.input_property['fun_name']

            self.root_path = self.input_property['root_path']

            # 所有的任务
            self.task_device_instance = None

            # path是指包含的相关路径
            self.fun_property = None

            # 标记是否完成初始化
            self.initial_finished = False

            # 程序退出
            self.to_exit = False

            # 看门狗
            self.watch_dog_client = None

            # 监听数据的线程的buffer
            # 本进程只有两个线程，一个界面线程，一个后台任务线程，所有类的请求，都写到这个队列里，由它进行实际的执行
            # 所以这个线程有两个功能，一个是转发数据，一个是执行任务
            self.buffer_read = None

            # 数据转发协议
            self.data_transfer = com_protocol.UdpProtocol()
            self.data_transfer.additional_info = "Task Center: "
            self.data_transfer.gui_id = self.gui_id

            # 所有的buffer都要放在这，主线程循环检查buffer是否有数据，如有数据则处理
            self.buffer_list = []
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + '_init_')
            print(error_msg)

    def run(self):
        """实际的进程，具体的操作要放在这，参数可以放在外面，但是跟线程相关的操作要放在这"""
        # 定义任务处理的类
        self.task_device_instance = task_device.TaskDevice()

        # path是指包含的相关路径
        self.fun_property = {
            public.fun_name_device: {
                'fun_name': public.fun_name_device,
                'path': self.input_property['fun_path'][public.fun_name_device]['path'],
                'task_host': self.task_device_instance,
                'private_key': ['task_host', 'private_key']
            }
        }

        self.data_transfer.initial()

        self._initial()

        # 开启看门狗，作为客户端
        self.watch_dog_client = WatchDog(1, self.watch_dog_gui_task_pipe_child,
                                         self.gui_id, self.main_gui_id, self.send_request_to_self)
        self.watch_dog_client.setDaemon(True)
        self.watch_dog_client.start()

        # 给主界面发送信息，进程已经启动
        self.send_initial_info()

        while True:
            try:
                for buffer in self.buffer_list:
                    if self.to_exit:
                        break
                    self.check_buffer(buffer)
                if self.to_exit:
                    break
                time.sleep(0.0005)
            except Exception as e:
                print(tools_common.get_error_msg(e.args, error_msg_prefix + "BackgroundThread: run"))
        try:
            self.close()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'run: close')
            print(error_msg)
        print('task center进程已退出！\n')

    def check_buffer(self, buffer=None):
        try:
            if buffer:
                while not buffer.empty():
                    if self.to_exit:
                        break
                    rev_data = buffer.get()
                    # 接收到数据之后，解析数据，响应任务
                    self.distribute_task(rev_data)
        except Exception as e:
            print(tools_common.get_error_msg(e.args, error_msg_prefix + "BackgroundThread: check_buffer"))

    def distribute_task(self, rev_data=None):
        """后台任务的接口，首先由此进行分发"""
        # 这里处理的数据来源有两类，一类是本进程的内部类写入buffer的数据，一类是其他进程写入pipe的数据
        # 这里相当于之前的转发线程，分析数据之后转发至其他类中执行，所以又有执行的功能
        try:
            # print('Task Center: 原始接收数据:')
            # print(rev_data)
            # print()
            self.data_transfer.transfer_msg(rev_data, True)
        except Exception as e:
            error_msg = (e.args, error_msg_prefix + "distribute_task")
            print(error_msg)

    def write(self, rev_data=None):
        self.start_one_task(rev_data)

    def start_one_task(self, rev_data=None):
        """响应任务"""
        if isinstance(rev_data, dict):
            if 'data' in rev_data.keys() and 'task_type' in rev_data['data'].keys():
                if str(rev_data['data']['task_type']) == \
                        str(public.common_task_type['program_exit']):
                    self.exit_program(rev_data)
                elif str(rev_data['data']['task_type']) == \
                        str(public.common_task_type['initial']):
                    self.check_initial(rev_data)
                elif str(rev_data['data']['task_type']) == \
                        str(public.common_task_type['main_gui_no_response']):
                    self.exit_program()
                else:
                    self.undefined_task_type(rev_data)

    def exit_program(self, rev_data=None):
        """退出程序"""
        # 关闭所有任务
        self.close_all_task()
        self.watch_dog_client.to_exit = True
        # 返回信息
        if rev_data:
            self.send_program_exited(rev_data)

        self.to_exit = True

    def close_all_task(self):
        """关闭所有任务"""
        try:
            self.task_device_instance.exit_program()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'close_all_task')
            print(error_msg)

    def send_program_exited(self, rev_data=None):
        """返回程序退出信号"""
        rev_data['data']['task_success'] = True

        public.send_response(self.send_msg_to_main_gui,
                             rev_data,
                             rev_data['data'])

    def check_initial(self, rev_data=None):
        """检查是否完成初始化"""
        rev_data['data']['task_success'] = True
        rev_data['data'][rev_data['data']['task_type']] = self.initial_finished
        rev_data['data'][public.error_msg_name] = ''
        public.send_response(self.send_msg_to_main_gui,
                             rev_data,
                             rev_data['data'])

    def undefined_task_type(self, rev_data=None):
        """未定义的任务"""
        rev_data['data']['task_success'] = False
        rev_data['data'][public.error_msg_name] = '请求的任务未定义！'
        public.send_response(self.send_msg_to_main_gui,
                             rev_data,
                             rev_data['data'])

    def send_response(self, rev_data=None, data=None):
        """返回信息"""
        if rev_data is None or not public.check_transfer_msg_format(rev_data):
            return False
        if data is None:
            data = {'error_msg': 'Unexpected Error!'}
        msg = public.encode_transfer_msg(rev_data['destination_id'],
                                         rev_data['source_id'],
                                         rev_data['task_id'],
                                         rev_data['msg_id'],
                                         data)
        if msg is not None:
            self.send_msg_to_main_gui(msg)
            return True
        return False

    def send_msg_to_main_gui(self, content=None):
        print('task center: send_msg_to_main_gui: ')
        print(content)
        print()
        if self.task_gui_buffer:
            self.task_gui_buffer.write(content)

    def send_msg_to_local(self, content=None):
        """在当前进程内发送数据"""
        print('task center: send_msg_to_local: ')
        print(content)
        print()
        self.buffer_read.write(content)

    def send_request_to_main_gui(self, data=None):
        """发送数据到主界面"""
        task_id = public.generate_task_id(public.fun_name_main_gui)
        msg_id = public.generate_msg_id()

        msg = public.encode_transfer_msg(self.gui_id,
                                         self.main_gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.send_msg_to_main_gui(msg)

    def send_request_to_self(self, data=None):
        """发送数据给自己"""
        task_id = public.generate_task_id(self.fun_name)
        msg_id = public.generate_msg_id()

        msg = public.encode_transfer_msg(self.gui_id,
                                         self.gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.send_msg_to_local(msg)

    def send_request_out(self, dst_gui_id=None, data=None, task_fun_name=''):
        """给task center发送服务请求"""
        if not task_fun_name:
            task_fun_name = self.fun_name
        task_id = public.generate_task_id(task_fun_name)
        msg_id = public.generate_msg_id()

        msg = public.encode_transfer_msg(self.gui_id,
                                         dst_gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.send_msg_to_main_gui(msg)

    def send_initial_info(self):
        """发送初始化成功的信息"""
        data = {
            "task_type": public.common_task_type['initial'],
            'task_success': True
        }
        self.send_request_out(self.main_gui_id, data, self.main_gui_fun_name)

    def _initial(self):
        """初始化"""
        # 监听数据的线程的buffer
        # 本进程只有两个线程，一个界面线程，一个后台任务线程，所有类的请求，都写到这个队列里，由它进行实际的执行
        # 所以这个线程有两个功能，一个是转发数据，一个是执行任务
        self.buffer_read = tools_common.BufferQueue()

        # 添加到数据监听列表
        self.buffer_list.append(self.task_gui_buffer)
        self.buffer_list.append(self.buffer_read)

        # 主界面跟其他界面是一样的，也需要注册，如果属于主界面的任务，也能够响应执行
        self.data_transfer.add_route(self.gui_id, self)
        self.data_transfer.add_route(self.main_gui_id, self.task_gui_buffer)

        self.start_all_task_host()

    def start_all_task_host(self):
        """启动管理任务的线程"""
        for fun_name, fun_value in self.fun_property.items():
            if 'task_host' in fun_value.keys() and fun_value['task_host'] is not None:
                try:
                    gui_id = public.get_gui_id(fun_name)
                    self.data_transfer.add_route(gui_id, fun_value['task_host'])

                    fun_value['task_host'].gui_id = gui_id
                    fun_value['task_host'].task_center_gui_id = self.gui_id
                    fun_property_temp = tools_common.copy_dict_except(self.fun_property[fun_name],
                                                                      self.fun_property[fun_name]['private_key'])
                    fun_value['task_host'].fun_property = fun_property_temp
                    fun_value['task_host'].fun_name = fun_name
                    fun_value['task_host'].buffer_write = self.buffer_read
                    fun_value['task_host'].start()
                except Exception as e:
                    error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "tart_all_task_host")
                    print(error_msg)
