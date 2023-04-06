import multiprocessing
import os
import sys
import threading
import time

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow

from py_about import about
from py_protocol import com_protocol
from py_show_text.show_text_gui import ShowTextGui, ShowTextDirectGui
from py_taskcenter import public, task_center
from py_tools import tools_common, background_task
from py_tools.tools_text import LocalShowText
from py_ui import main_gui
from py_ui.device_info import DeviceInfo
from py_ui.device_management import DeviceManage
from py_watchdog.watchdog import WatchDog

error_msg_prefix = "error: UiExample: "


class MainGUI(QMainWindow):

    def __init__(self, screen_size=None, parent=None):
        super(MainGUI, self).__init__(parent)

        # 显示器大小
        self.screen_width = screen_size[0]
        self.screen_height = screen_size[1]

        # 主界面
        self.win_main = main_gui.Ui_MainWindow()
        # 关于界面
        self.win_about = about.AboutGui()

        # 设备管理器
        self.device_manage = DeviceManage(self)

        # 各界面的名称
        self.fun_name = public.fun_name_main_gui
        self.device_manage.fun_name = public.fun_name_device
        self.task_center_fun_name = public.fun_name_task_center

        # 当前界面的地址
        self.gui_id = ''
        # task_center的gui_id
        self.task_center_gui_id = None

        # 根目录
        self.root_path = ""

        # 当前进程内各功能类写入的Queue
        self.buffer_read = tools_common.BufferQueue()

        # 后台线程，持续监听是否接收到新数据
        self.background_task = background_task.BackgroundQThread()

        # 数据转发协议
        self.data_transfer = com_protocol.UdpProtocol()
        self.data_transfer.additional_info = "UiExample: "

        # 任务进程
        self.task_center_process = None
        # 进程是否启动标识
        self.task_center_started = False
        # 进程是否退出标识
        self.task_center_exited = False

        # 显示信息的类
        self.local_show_text = LocalShowText()

        # 工具栏
        self.fun_property = {
            public.fun_name_device_info: {
                'btn': ['设备显示', DeviceInfo, True],
                'instance': [list(), 1],
                'path': None
            },
            public.fun_name_show_text: {
                'btn': ['Text显示', ShowTextGui, True],
                'instance': [list(), 2],
                'path': None
            },
            public.fun_name_show_text_direct: {
                'btn': ['Text显示-直显', ShowTextDirectGui, True],
                'instance': [list(), 2],
                'path': None
            }
        }

    def create_main_gui(self):
        """界面初始化"""
        # 界面控件初始化
        self.win_main.setupUi(self)

        # menu绑定方法
        self.win_main.action_about.triggered.connect(self.win_about.show)

        # 初始化目录
        self.root_path, error_msg_path = fun_path_initial()
        if error_msg_path:
            self.show_data_to_text(error_msg_path)
        self.path_initial()

        # 初始化设备管理界面中的控件
        self.device_manage.create_main_gui()

        # 后台任务的一些初始化和启动
        self.background_task.task_signal.connect(self.distribute_task)
        self.background_task.buffer_list.append(self.buffer_read)
        self.background_task.is_show_text = True
        self.background_task.start()

        # 获取主界面的gui_id
        self.gui_id = public.get_gui_id(self.fun_name)
        self.device_manage.gui_id = public.get_gui_id(self.device_manage.fun_name)
        self.data_transfer.gui_id = self.gui_id

        # 子界面
        self._create_fun_gui(public.fun_name_device_info,
                             self.fun_property[public.fun_name_device_info]['btn'][1])
        self._create_fun_gui(public.fun_name_show_text,
                             self.fun_property[public.fun_name_show_text]['btn'][1])
        self._create_fun_gui(public.fun_name_show_text,
                             self.fun_property[public.fun_name_show_text]['btn'][1])
        self._create_fun_gui(public.fun_name_show_text_direct,
                             self.fun_property[public.fun_name_show_text_direct]['btn'][1])

        # 主界面跟其他界面是一样的，也需要注册，如果属于主界面的任务，也能够响应执行
        self.data_transfer.add_route(self.gui_id, self)
        self.data_transfer.add_route(self.device_manage.gui_id, self.device_manage)

        self.start_sub_process()

        th = threading.Thread(target=self.check_process_started, args=())
        th.setDaemon(True)
        th.start()

        self.win_main.device_tabwidget.setCurrentWidget(self.win_main.main_device_tab)
        # 显示界面
        self.show()

    def _create_fun_gui(self, fun_name='', fun_instance=None):
        """创建界面的公共函数"""
        if not self._gui_management(fun_name):
            return
        if len(self.fun_property[fun_name]['instance'][0]) < \
                int(self.fun_property[fun_name]['instance'][1]):
            gui_id = public.get_gui_id(fun_name, self.fun_property[fun_name]['instance'][0])

            # 显示到tab页上
            new_tab, index = self.add_one_tab(gui_id, self.fun_property[fun_name]['btn'][0])

            instance_test = fun_instance(
                {
                    'fun_name': fun_name,
                    'buffer_write': self.buffer_read,
                    'gui_id': gui_id,
                    'task_center_gui_id': self.task_center_gui_id,
                    'main_gui_id': self.gui_id,
                    'local_show_text': self.local_show_text,
                    'main_window': self,
                    'path': self.fun_property[fun_name]['path'],
                },
                new_tab
            )
            self.fun_property[fun_name]['instance'][0].append(instance_test)
            # 创建界面的时候需要在路由中注册
            self.data_transfer.add_route(gui_id, instance_test)
            instance_test.create_main_gui()
        else:
            # later：这里后续不要警告，而是跳转到最后一个界面
            self.show_last_gui(fun_name)

    def _gui_management(self, fun_name=''):
        """检查界面是否已经退出"""
        instance_temp = self.fun_property[fun_name]['instance'][0].copy()
        for instance_test in instance_temp:
            if instance_test.exited:
                self.fun_property[fun_name]['instance'][0].remove(instance_test)
                self.data_transfer.delete_route(instance_test.gui_id)
        return True

    def add_one_tab(self, obj_name='', tab_name=''):
        """添加一个tab页"""
        new_tab = QtWidgets.QWidget()
        new_tab.setAccessibleName(obj_name)
        self.win_main.device_tabwidget.addTab(new_tab, tab_name)
        self.win_main.device_tabwidget.setCurrentWidget(new_tab)
        index = self.win_main.device_tabwidget.currentIndex()
        return new_tab, index

    def show_last_gui(self, fun_name=""):
        """显示最新的一个界面"""
        try:
            if self.fun_property[fun_name]['instance'][0]:
                self.win_main.device_tabwidget.setCurrentWidget(self.fun_property[fun_name]['instance'][0][
                                                                      len(self.fun_property[fun_name]['instance'][0]) -
                                                                      1].parent)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_last_gui')
            self.show_data_to_text(error_msg)

    def check_process_started(self):
        """检查进程是否启动成功"""
        count = 0
        while not self.task_center_started:
            time.sleep(0.001)
            count += 1
            if count > 30000:
                break
        if self.task_center_started:
            self.show_data_to_text(self.fun_name + ': task center启动成功！')
        else:
            self.show_data_to_text(self.fun_name + ': task center启动失败！')

    def path_initial(self):
        """根据获取的路径初始化本界面的路径"""
        try:
            for path in public.fun_path.values():
                tools_common.check_dir(self.root_path + path)

            for names, properties in self.fun_property.items():
                if names in public.fun_property.keys() and 'path' in public.fun_property[names].keys():
                    properties['path'] = public.fun_property[names]['path']
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "path_initial")
            self.show_data_to_text(error_msg)

    def start_sub_process(self):
        """启动子进程"""
        try:
            # 创建与任务中心进程通信的pipe
            gui_task_center_buffer_parent, gui_task_center_buffer_child = tools_common.new_pipe_buffer()
            # 任务和数据进程的gui_id
            self.task_center_gui_id = public.get_gui_id(self.task_center_fun_name)
            input_property = {
                'gui_id': self.task_center_gui_id,
                'fun_name': self.task_center_fun_name,
                'gui_pipe': gui_task_center_buffer_child,
                'watch_dog_pipe': watch_dog_gui_task_pipe_child,
                'main_gui_gui_id': self.gui_id,
                'main_gui_fun_name': self.fun_name,
                'fun_path': public.fun_property,
                'root_path': self.root_path
            }
            self.task_center_process = task_center.TaskCenter(input_property)
            self.task_center_process.daemon = True

            # 添加路由，用于写数据
            self.data_transfer.add_route(self.task_center_gui_id, gui_task_center_buffer_parent)
            # 加入后台监听，用于读数据
            self.background_task.buffer_list.append(gui_task_center_buffer_parent)

            # 启动进程
            self.task_center_process.start()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "start_sub_process")
            self.show_data_to_text(error_msg)

    def distribute_task(self, msg=None):
        """后台任务的接口，首先由此进行分发"""
        # 这里处理的数据来源有两类，一类是本进程的内部类写入buffer的数据，一类是其他进程写入pipe的数据
        # 这里相当于之前的转发线程，分析数据之后转发至其他类中执行，所以又有执行的功能
        try:
            if 'local_show_text' in msg.keys():
                self.local_show_text.show_msg_outside()
            else:
                self.data_transfer.transfer_msg(msg, True)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "distribute_task")
            self.show_data_to_text(error_msg)

    def write(self, rev_data=None):
        """处理接收到的数据"""
        print('UiExample: write')
        print(rev_data)
        print()
        try:
            if isinstance(rev_data, dict):
                if 'data' in rev_data.keys():
                    if 'task_type' in rev_data['data'].keys():
                        if str(rev_data['data']['task_type']) == \
                                str(public.common_task_type['initial']):
                            self.response_of_initial(rev_data)
                        elif str(rev_data['data']['task_type']) == \
                                str(public.common_task_type['program_exit']):
                            self.response_of_program_exit(rev_data)
                else:
                    print('response_of_undefined_task_type:')
                    print(rev_data)
                    print()
            else:
                print('response_of_undefined_task_type:')
                print(rev_data)
                print()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "write")
            self.show_data_to_text(error_msg)

    def response_of_initial(self, rev_data=None):
        """接收其他进程的初始化信息"""
        src_id = public.get_actual_source_id(rev_data['source_id'])
        if src_id == self.task_center_gui_id:
            self.task_center_started = rev_data['data']['task_success']

    def response_of_program_exit(self, rev_data=None):
        """接收返回的退出信息"""
        src_id = public.get_actual_source_id(rev_data['source_id'])
        if src_id == self.task_center_gui_id:
            self.task_center_exited = True

    def send_exit_signal(self):
        """发送退出信号"""
        # print('\n---------------------------\n发送退出信号\n-------------------')
        data = {
            'task_type': public.common_task_type["program_exit"]
        }
        msg_id = public.generate_msg_id()

        task_id = public.generate_task_id(public.fun_name_task_center)
        msg = public.encode_transfer_msg(self.gui_id,
                                         self.task_center_gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.data_transfer.buffer_route[self.task_center_gui_id].write(msg)

    def closeEvent(self, event):
        """退出程序"""
        try:
            # 各个子界面退出
            self.device_manage.gui_exit()

            # 退出程序，发送信号
            self.background_task.to_exit = True
            self.send_exit_signal()

            self.win_about.close()

            i = 0
            gui_task_center_buffer_parent = self.data_transfer.buffer_route[self.task_center_gui_id]
            while True:
                if not self.task_center_exited:
                    while not gui_task_center_buffer_parent.empty():
                        rev_data = gui_task_center_buffer_parent.get()
                        self.write(rev_data)
                i += 1
                if self.task_center_exited or i > 10000:
                    break
                time.sleep(0.001)

            # print(self.task_center_exited)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "closeEvent")
            self.show_data_to_text(error_msg)

    def show_data_to_text(self, content=None, additional_msg=''):
        """显示数据"""
        if self.fun_property[public.fun_name_device_info]['instance'][0]:
            gui_id = self.fun_property[public.fun_name_device_info]['instance'][0][0].gui_id
            self.local_show_text.local_show_everything_to_text(content, additional_msg, gui_id)


def fun_path_initial():
    """加载文件"""
    # 获取当前路径
    error_msg = ""
    path = os.getcwd()
    try:
        lib_path = path + public.fun_path['lib']
        result_path = path + public.fun_path['result']

        for names, properties in public.fun_property.items():
            if 'path' in properties.keys():
                fun_path = properties['path']
                if public.fun_lib_path in fun_path.keys():
                    if len(fun_path[public.fun_lib_path]) > 0:
                        fun_path[public.fun_lib_path] = lib_path + \
                                                        fun_path[public.fun_lib_path]
                        tools_common.check_dir(fun_path[public.fun_lib_path])

                if public.fun_result_path in fun_path.keys():
                    if len(fun_path[public.fun_result_path]) > 0:
                        fun_path[public.fun_result_path] = result_path + \
                                                           fun_path[public.fun_result_path]
                        tools_common.check_dir(fun_path[public.fun_result_path])
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, "fun_path_initial")
    root_path = path
    return root_path, error_msg


if __name__ == '__main__':
    multiprocessing.freeze_support()

    # 看门狗服务器
    # 创建与任务中心和数据处理进程通信的pipe
    watch_dog_gui_task_pipe_parent, watch_dog_gui_task_pipe_child = tools_common.new_pipe_buffer()
    watch_dog_server = WatchDog(0)
    watch_dog_server.child_process_pipe.append(watch_dog_gui_task_pipe_parent)
    watch_dog_server.setDaemon(True)
    # 启动看门狗
    watch_dog_server.start()

    app = QApplication(sys.argv)
    win = MainGUI([app.desktop().screenGeometry().width(),
                   app.desktop().screenGeometry().height()])

    win.create_main_gui()
    eee = app.exec_()
    sys.exit(eee)
