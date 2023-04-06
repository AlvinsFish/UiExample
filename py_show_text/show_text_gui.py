import os
import random

from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor

from py_show_text import text_ui, text_direct_ui
from py_taskcenter import public
from py_tools import tools_text, tools_common, tools_file
from py_tools.tools_text import LocalShowTextDirect

error_msg_prefix = 'error: show_text_gui: '


class ShowTextGui:

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
        self.win_main = text_ui.Ui_Form()

        # 界面相关的路径
        self.path = self.fun_property['path']
        self.result_path = self.path[public.fun_result_path]

        # 界面是否退出
        self.exited = False

    def create_main_gui(self):
        """界面初始化"""
        self.win_main.setupUi(self.parent)

        self.local_show_text.add_show_text(self.gui_id, self.win_main.show_text, txt_path=self.result_path)

        self.win_main.send_btn.clicked.connect(self.send_info)
        self.win_main.confirm_btn.clicked.connect(self.confirm_setting)
        self.win_main.clear_btn.clicked.connect(self.win_main.show_text.clear)

        self.set_setting_state()

        self.show_data_to_text(self.gui_id)

    def write(self, rev_data=None):
        """接收到的数据"""
        pass

    def set_setting_state(self):
        """设置控件的状态"""
        self.win_main.display_enable_checkbox.setChecked(self.local_show_text.get_display_on(self.gui_id))
        self.win_main.display_time_checkbox.setChecked(self.local_show_text.get_show_time(self.gui_id))
        self.win_main.display_convert_checkbox.setChecked(self.local_show_text.get_str_convert(self.gui_id))
        self.win_main.display_multi_checkbox.setChecked(self.local_show_text.get_display_way(self.gui_id))
        self.win_main.display_oversize_save_checkbox.setChecked(self.local_show_text.get_oversize_save(self.gui_id))
        self.win_main.display_oversize_edit.setText(str(self.local_show_text.get_oversize_length(self.gui_id)))

    def send_info(self):
        """显示数据"""
        text = self.win_main.text_edit.toPlainText()
        if text:
            self.show_data_to_text(text)
            self.win_main.text_edit.clear()

    def confirm_setting(self):
        """显示设置"""
        display_on = self.win_main.display_enable_checkbox.isChecked()
        show_time = self.win_main.display_time_checkbox.isChecked()
        str_convert = self.win_main.display_convert_checkbox.isChecked()
        display_way = self.win_main.display_multi_checkbox.isChecked()
        oversize_save = self.win_main.display_oversize_save_checkbox.isChecked()
        show_text_length = self.win_main.display_oversize_edit.text().strip()

        if show_text_length.isdigit() and \
                tools_text.oversize_length_min <= int(show_text_length) <= tools_text.oversize_length_max:
            self.local_show_text.set_save_display_display_on(self.gui_id, display_on)
            self.local_show_text.set_save_display_show_time(self.gui_id, show_time)
            self.local_show_text.set_save_display_str_convert(self.gui_id, str_convert)
            self.local_show_text.set_save_display_display_way(self.gui_id, display_way)
            self.local_show_text.set_save_display_oversize_save(self.gui_id, oversize_save)
            self.local_show_text.set_save_display_oversize_length(self.gui_id, show_text_length)
            self.show_data_to_text('修改成功！')
        else:
            self.show_data_to_text('超限长度错误（' + str(tools_text.oversize_length_min) + ', ' +
                                   str(tools_text.oversize_length_max) + '）！')

    def show_data_to_text(self, content=None, additional_msg=''):
        """显示数据"""
        self.local_show_text.local_show_everything_to_text(content, additional_msg, self.gui_id)


class ShowTextDirectGui:

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
        # 直显
        self.show_text_direct = LocalShowTextDirect()

        # 主界面
        self.main_window = self.fun_property['main_window']
        self.win_main = text_direct_ui.Ui_Form()

        # 界面相关的路径
        self.path = self.fun_property['path']
        self.result_path = self.path[public.fun_result_path]

        # 界面是否退出
        self.exited = False

        # 涉及频繁显示的任务
        self.hard_work = None

    def create_main_gui(self):
        """界面初始化"""
        self.win_main.setupUi(self.parent)

        self.local_show_text.add_show_text(self.gui_id, self.win_main.show_text, txt_path=self.result_path)
        self.show_text_direct.show_text = self.win_main.show_text
        self.show_text_direct.result_path = self.result_path

        self.win_main.clear_btn.clicked.connect(self.win_main.show_text.clear)
        self.win_main.start_btn.clicked.connect(self.start_work)

        self.show_data_to_text(self.gui_id)

    def start_work(self):
        """启动任务"""
        if not self.hard_work or not self.hard_work.isRunning():
            self.hard_work = SomeWork()
            self.hard_work.signal.connect(self.work_action)
            self.hard_work.start()
        elif self.hard_work.isRunning():
            self.hard_work.to_exit = True

    def write(self, rev_data=None):
        """接收到的数据"""
        pass

    def work_action(self, data=None):
        """任务的响应函数"""
        if data is None:
            data = {}
        for key, value in data.items():
            if key == LocalShowTextDirect.show_info:
                self.show_text_direct.show_text_action(key, value)

    def show_data_to_text(self, content=None, additional_msg=''):
        """显示数据"""
        self.local_show_text.local_show_everything_to_text(content, additional_msg, self.gui_id)


class SomeWork(QThread):
    signal = pyqtSignal(dict)

    """后台一些需要频繁显示内容的任务"""

    def __init__(self):
        """初始化"""
        super().__init__()
        # 退出线程
        self.to_exit = False

    def run(self):
        """执行任务"""
        while True:
            if self.to_exit:
                break
            length = random.randint(500, 1200)
            msg = ''
            for i in range(int(length/4)):
                msg += 'Test'
            self.show_data_to_text(msg)
            if self.to_exit:
                break
            self.msleep(300)

    def show_data_to_text(self, show_msg=''):
        """显示数据"""
        try:
            self.signal.emit({LocalShowTextDirect.show_info: show_msg})
            # length = len(show_msg)
            # txt_name = ''
            # if length > self.oversize_length:
            #     if self.oversize_save:
            #         now_time = tools_common.get_date_time_ms()
            #         txt_name = os.path.join(self.result_path, now_time + '.txt')
            #         msg = show_msg[0:self.oversize_length] + '...\n......\n数据过大，只显示部分数据，全部数据已存储在：\n' + txt_name + '\n请查看！\n'
            #     else:
            #         msg = show_msg[0:self.oversize_length] + '...\n......\n数据过大，只显示部分数据\n'
            # else:
            #     msg = show_msg + '\n'
            # self.signal.emit({'show_info': msg})
            #
            # if txt_name:
            #     tools_file.save_to_txt(txt_name, show_msg)
            #
            # self.show_count += 1
            # if self.show_count >= self.clear_count:
            #     self.show_count = 0
            #     self.signal.emit({'clear_show_text': ''})
            #     self.msleep(1)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_data_to_text')
            print(error_msg)
