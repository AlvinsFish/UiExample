from PyQt5.QtCore import QThread, pyqtSignal

from py_tools import tools_common

error_msg_prefix = "error: background_task: "


class BackgroundTask:
    """
    循环查询数据，后台任务
    """

    def __init__(self):
        """初始化"""
        # 循环查询此list中的buffer
        self.buffer_list = list()

        # 通知线程退出
        self.to_exit = False

    def work(self):
        """循环查询"""
        while True:
            if self.to_exit:
                break
            try:
                # 循环查询是否有数据
                for buffer in self.buffer_list:
                    self.check_buffer(buffer)
                if self.to_exit:
                    break
                self.time_sleep_us(500)
            except Exception as e:
                error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "BackgroundTask: work")
                print(error_msg)

    def check_buffer(self, buffer=None):
        try:
            if buffer:
                while not buffer.empty():
                    if self.to_exit:
                        break
                    rev_data = buffer.get()
                    # print('check_buffer')
                    # print(rev_data)
                    # print()
                    # 接收到数据之后，解析数据，响应任务
                    self.process_received_data(rev_data)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "BackgroundQThread: check_buffer")
            print(error_msg)

    def process_received_data(self, rev_data=None):
        """处理接收到的数据"""
        pass

    def time_sleep_us(self, sleep_time=0):
        """等待时间"""
        pass


class BackgroundQThread(QThread, BackgroundTask):
    task_signal = pyqtSignal(dict)

    def __init__(self):
        """初始化"""
        super().__init__()
        BackgroundTask.__init__(self)

    def run(self):
        self.work()

    def process_received_data(self, rev_data=None):
        """处理接收到的数据"""
        try:
            # print('process_received_data 0')
            # print(rev_data)
            # print()
            self.task_signal.emit(rev_data)
            # print('process_received_data 1')
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "BackgroundQThread: check_buffer")
            print(error_msg)

    def time_sleep_us(self, sleep_time=0):
        """等待时间"""
        self.usleep(sleep_time)
