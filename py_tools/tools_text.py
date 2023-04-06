import os

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor

from py_tools import tools_common, tools_file

# 显示前：超过这个长度的数据会被截断
# 这是全局超限长度，oversize_length是局部的超限长度
from py_tools.tools_common import BufferQueue

show_text_length = 10000
oversize_length_min = 1000
oversize_length_max = 1280000

# 显示后：text中的数据长度超过此值会被删除
show_text_delete_length = 4096000
# 截断或删除操作后实际显示的数据长度
show_text_remain_length = 2000
error_msg_prefix = 'error: tools_text: '


def show_msg_to_text_dict(msg_queue=None, tk_text_dict=None):
    """显示msg到text"""
    # str_convert为True表示读时转换
    # display_way为True表示一次性显示
    try:
        msg_showed = False
        all_msg_dict = {}
        while not msg_queue.empty():
            msg_get_list = msg_queue.get()
            gui_id = msg_get_list[0]
            msg_get = msg_get_list[1]

            if gui_id in tk_text_dict.keys():
                tk_text = tk_text_dict[gui_id].show_text
                path = tk_text_dict[gui_id].txt_path
                show_time = tk_text_dict[gui_id].show_time
                str_convert = tk_text_dict[gui_id].str_convert
                display_way = tk_text_dict[gui_id].display_way
                display_on = tk_text_dict[gui_id].display_on
                oversize_save_txt = tk_text_dict[gui_id].oversize_save
                oversize_length = tk_text_dict[gui_id].oversize_length

                if gui_id not in all_msg_dict.keys():
                    all_msg_dict[gui_id] = ""

                if display_on:
                    if str_convert:
                        # 需要先转换，再显示
                        if isinstance(msg_get, list) and len(msg_get) == 2:
                            # 转换数据部分挪到了这里
                            msg_to_text = convert_to_str(msg_get[0], msg_get[1]) + '\n'
                            if show_time:
                                msg_to_text = tools_common.get_date_time_ms() + '\n' + msg_to_text
                            if display_way:
                                # 先累加，最后一次性显示
                                all_msg_dict[gui_id] += msg_to_text
                            else:
                                # get一次显示一次
                                show_text_action(tk_text, msg_to_text, path,
                                                 oversize_save_txt, oversize_length)
                    else:
                        # 在写的时候转换，这里直接显示
                        if show_time:
                            msg_get[0] = tools_common.get_date_time_ms() + '\n' + msg_get[0] + msg_get[1]
                        if display_way:
                            # 先累加，最后一次性显示
                            all_msg_dict[gui_id] += msg_get[0] + '\n'
                        else:
                            # get一次显示一次
                            show_text_action(tk_text, msg_get[0] + '\n', path,
                                             oversize_save_txt, oversize_length)
                    msg_showed = True
        if all_msg_dict:
            for gui_id_temp, all_msg in all_msg_dict.items():
                if all_msg:
                    path = tk_text_dict[gui_id_temp].txt_path
                    oversize_save_txt = tk_text_dict[gui_id_temp].oversize_save
                    oversize_length = tk_text_dict[gui_id_temp].oversize_length
                    show_text_action(tk_text_dict[gui_id_temp].show_text, all_msg, path,
                                     oversize_save_txt, oversize_length)
        if msg_showed:
            for gui_id_temp in all_msg_dict.keys():
                tk_text = tk_text_dict[gui_id_temp].show_text
                tk_text.moveCursor(QTextCursor.End)
                # delete_text_in_tk_text(tk_text, is_tk)
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_msg_to_text_dict')
        print(error_msg)


def show_text_action(tk_text=None, msg_to_text='', path="",
                     oversize_save_txt=True, oversize_length=show_text_length):
    # is_tk为True表示tk，False表示为pyqt
    try:
        length = len(msg_to_text)
        actual_show_text_length = int(oversize_length) + 2 * int(show_text_remain_length)
        if 0 < length <= actual_show_text_length:
            insert_to_tk_text(tk_text, msg_to_text)
        elif length > actual_show_text_length:
            now_time = tools_common.get_date_time_ms()
            if oversize_save_txt:
                txt_name = os.path.join(path, now_time + '.txt')
                tools_file.save_to_txt(txt_name, msg_to_text)
                msg = msg_to_text[0: show_text_remain_length] + '...\n......\n...' + \
                    msg_to_text[length - show_text_remain_length:] + \
                    '数据过大（' + str(length) + '），只显示部分数据，全部数据已存储在：\n' + \
                    txt_name + '\n请查看！\n\n'
            else:
                msg = msg_to_text[0: show_text_remain_length] + \
                      '...\n......\n...' + \
                      msg_to_text[length - show_text_remain_length:] + \
                      '数据过大（' + str(length) + '），只显示部分数据。\n\n'
            insert_to_tk_text(tk_text, msg)
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_text_action')
        print(error_msg)


def insert_to_tk_text(tk_text=None, msg=''):
    """以附加的形式写数据到tk_text"""
    try:
        tk_text.append(msg.strip() + '\n')
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'insert_to_tk_text')
        print(error_msg)


def convert_to_str(content=None, additional_msg=''):
    """将数据转换为str"""
    msg_to_text = ''
    try:
        additional_msg = additional_msg.strip()
        if additional_msg:
            msg_to_text += additional_msg + '\n'
        msg_to_text += convert_type_to_str(content)
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'convert_to_str')
        msg_to_text += error_msg
        print(error_msg)
    return msg_to_text


def convert_type_to_str(content=None):
    """将其他类型的数据转为str类型"""
    msg_to_text = ""
    if isinstance(content, str):
        msg_to_text += content + '\n'
    elif isinstance(content, list):
        msg_to_text += '['
        for data in content:
            msg_to_text += convert_type_to_str(data).strip() + ', '
        msg_to_text = msg_to_text.strip().strip(',')
        msg_to_text += ']\n'
    elif isinstance(content, dict):
        msg_to_text += '{'
        for key, value in content.items():
            msg_to_text += convert_type_to_str(key).strip() + ': '
            msg_to_text += convert_type_to_str(value).strip() + ', '
        msg_to_text = msg_to_text.strip().strip(',')
        msg_to_text += '}\n'
    elif isinstance(content, tuple):
        msg_to_text += '('
        for arg in content:
            msg_to_text += convert_type_to_str(arg).strip() + ', '
        msg_to_text = msg_to_text.strip().strip(',')
        msg_to_text += ')\n'
    else:
        msg_to_text += str(content) + '\n'
    return msg_to_text


def show_everything_to_text(msg_queue=None, content=None, additional_msg='',
                            str_convert=True, gui_id="default"):
    """显示所有类型的信息"""
    # 根据msg的类型判断怎么写入显示，最终要分解为str类型
    # 先完成，str、int、float、error->tuple，类型
    # 这里主要的工作是解析输入的需要显示的变量的类型
    try:
        # 第二种方式，直接str，转换的时候更快，但是在显示的时候这种方式转换出来的显示更慢
        # if len(additional_msg) > 0:
        #     msg_to_text += additional_msg + '\n'
        # msg_to_text += str(content)
        if str_convert:
            if msg_queue:
                # 这里改为，直接写缓存，转换部分留给显示部分
                msg_queue.write([gui_id, [content, additional_msg]])
        else:
            # 第一种方式，转换，在显示的时候这种方式拆出来的显示更快
            msg_to_text = convert_to_str(content, additional_msg)
            if msg_queue:
                msg_queue.write([gui_id, [msg_to_text, '']])
    except Exception as e:
        error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_everything_to_text')
        print(error_msg)


def config_oversize_length(dst_value=None, src_value=None):
    if dst_value and \
            str(dst_value).isdigit() and \
            oversize_length_min <= int(dst_value) <= oversize_length_max and \
            int(dst_value) != int(src_value):
        return True
    return False


class LocalShowText(QThread):
    """负责所有显示和txt生成"""
    signal = pyqtSignal(dict)

    def __init__(self):
        """初始化"""
        super().__init__()
        # 以下两个队列是全局唯一的，作用于各个线程，各个线程写入数据
        # 主线程读取数据，进行显示和保存数据
        # msg_queue是显示和txt的缓存，因为显示的都写入txt，保存的就是str
        self.global_msg_queue = BufferQueue()
        # 主界面
        self.sub_top = None
        # 显示窗口
        # {'gui_id': {'show_text': show_text, 'result_txt': None}}
        self.show_text_dict = {}

        # 如果显示的内容大于1000行，就清理到只剩下100
        self.max_show_count = [0, 1000, 500]

        # 超限的长度
        self.oversize_length = show_text_length

        # 显示次数
        self.show_count = 0

    def add_show_text(self, gui_id='', tk_text=None, show_time=True, txt_path="", oversize_save=True):
        """增加一个show_text"""
        try:
            if gui_id in self.show_text_dict.keys():
                self.show_text_dict[gui_id].show_text = tk_text
                self.show_text_dict[gui_id].show_time = show_time
            else:
                self.show_text_dict[gui_id] = \
                    DisplaySetting(tk_text, show_time, txt_path, True, True, True, oversize_save)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "add_show_text")
            self.local_show_everything_to_text(error_msg)

    def delete_show_text(self, gui_id=None):
        """删除一个show_text"""
        try:
            if gui_id in self.show_text_dict.keys():
                self.show_text_dict.pop(gui_id)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "delete_show_text")
            self.local_show_everything_to_text(error_msg)

    def run(self):
        """持续监听，如有内容则显示"""
        count = 0
        while True:
            show_msg_to_text_dict(self.global_msg_queue,
                                  self.show_text_dict)
            QThread.usleep(500)

            count += 1
            if count >= 5000:
                self.response_of_check_show_text()
                count = 0

    def show_msg_outside(self):
        """在外部显示内容"""
        try:
            show_msg_to_text_dict(self.global_msg_queue, self.show_text_dict)
            self.show_count += 1
            if self.show_count >= 5000:
                self.response_of_check_show_text()
                self.show_count = 0
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "show_msg_outside")
            self.local_show_everything_to_text(error_msg)

    def response_of_check_show_text(self):
        """检查show text的内容是否超过限制"""
        # 能否这么使用还需要验证
        try:
            # {'gui_id': {'show_text': show_text, 'result_txt': None}}
            for value in self.show_text_dict.values():
                show_text = value.show_text
                if show_text:
                    text = show_text.toPlainText()
                    length = len(text)
                    if length >= int(show_text_delete_length + show_text_remain_length):
                        show_text.clear()
                        show_text.document().clear()
                        show_text.append(text[length - show_text_remain_length:])
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'response_of_check_show_text')
            self.local_show_everything_to_text(error_msg)

    def local_show_everything_to_text(self, content=None, additional_msg='', gui_id="default"):
        """本地对接显示函数"""
        # 显示数据和存储数据是分开的
        # 写数据
        try:
            if gui_id in self.show_text_dict.keys():
                show_everything_to_text(self.global_msg_queue, content, additional_msg,
                                        self.show_text_dict[gui_id].str_convert, gui_id)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: show_everything_to_text')
            print(error_msg)

    def set_save_display_show_time(self, gui_id='', value=None):
        error_msg = ''
        try:
            if gui_id in self.show_text_dict.keys():
                error_msg = self.show_text_dict[gui_id].set_save_display_show_time(value)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: set_save_display_show_time')
        if error_msg:
            self.local_show_everything_to_text(error_msg)

    def set_save_display_oversize_length(self, gui_id='', value=None):
        try:
            error_msg = ''
            if value:
                if gui_id in self.show_text_dict.keys():
                    error_msg = self.show_text_dict[gui_id].set_save_display_display_way(int(value))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: set_save_display_oversize_length')
        if error_msg:
            self.local_show_everything_to_text(error_msg)

    def set_save_display_str_convert(self, gui_id='', value=None):
        try:
            # if value:
            error_msg = ''
            if gui_id in self.show_text_dict.keys():
                error_msg = self.show_text_dict[gui_id].set_save_display_display_way(value)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: set_save_display_str_convert')
        if error_msg:
            self.local_show_everything_to_text(error_msg)

    def set_save_display_display_way(self, gui_id='', value=None):
        try:
            # if value:
            error_msg = ''
            if gui_id in self.show_text_dict.keys():
                error_msg = self.show_text_dict[gui_id].set_save_display_display_way(value)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: set_save_display_display_way')
        if error_msg:
            self.local_show_everything_to_text(error_msg)

    def set_save_display_display_on(self, gui_id='', value=None):
        try:
            # if value:
            error_msg = ''
            if gui_id in self.show_text_dict.keys():
                error_msg = self.show_text_dict[gui_id].set_save_display_display_on(value)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: set_save_display_display_on')
        if error_msg:
            self.local_show_everything_to_text(error_msg)

    def set_save_display_oversize_save(self, gui_id='', value=None):
        try:
            # if value:
            error_msg = ''
            if gui_id in self.show_text_dict.keys():
                error_msg = self.show_text_dict[gui_id].set_save_display_oversize_save(value)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'local_show_everything_to_text: set_save_display_oversize_save')
        if error_msg:
            self.local_show_everything_to_text(error_msg)

    def get_show_time(self, gui_id=''):
        """"""
        result = None
        if gui_id in self.show_text_dict.keys():
            result = self.show_text_dict[gui_id].show_time
        return result

    def get_str_convert(self, gui_id=''):
        """"""
        result = None
        if gui_id in self.show_text_dict.keys():
            result = self.show_text_dict[gui_id].str_convert
        return result

    def get_display_on(self, gui_id=''):
        """"""
        result = None
        if gui_id in self.show_text_dict.keys():
            result = self.show_text_dict[gui_id].display_on
        return result

    def get_display_way(self, gui_id=''):
        """"""
        result = None
        if gui_id in self.show_text_dict.keys():
            result = self.show_text_dict[gui_id].display_way
        return result

    def get_oversize_save(self, gui_id=''):
        """"""
        result = None
        if gui_id in self.show_text_dict.keys():
            result = self.show_text_dict[gui_id].oversize_save
        return result

    def get_oversize_length(self, gui_id=''):
        """"""
        result = None
        if gui_id in self.show_text_dict.keys():
            result = self.show_text_dict[gui_id].oversize_length
        return result


class DisplaySetting:
    """显示设置"""

    def __init__(self, tk_text=None, show_time=True, txt_path="", str_convert=True,
                 display_on=True, display_way=True, oversize_save=True, ):
        """初始化"""
        self.show_text = tk_text
        self.show_time = show_time
        self.txt_path = txt_path
        self.str_convert = str_convert
        self.display_on = display_on
        self.display_way = display_way
        self.oversize_save = oversize_save
        self.oversize_length = show_text_length

    def set_save_display_show_time(self, value=None):
        error_msg = ''
        try:
            self.show_time = value
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'DisplaySetting: set_save_display_show_time')
        return error_msg

    def set_save_display_oversize_length(self, value=None):
        error_msg = ""
        try:
            self.oversize_length = int(value)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'DisplaySetting: set_save_display_oversize_length')
        return error_msg

    def set_save_display_str_convert(self, value=None):
        error_msg = ''
        try:
            self.str_convert = value
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'DisplaySetting: set_save_display_str_convert')
        return error_msg

    def set_save_display_display_way(self, value=None):
        error_msg = ''
        try:
            self.display_way = value
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'DisplaySetting: set_save_display_display_way')
        return error_msg

    def set_save_display_display_on(self, value=None):
        error_msg = ''
        try:
            self.display_on = value
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'DisplaySetting: set_save_display_display_on')
        return error_msg

    def set_save_display_oversize_save(self, value=None):
        error_msg = ''
        try:
            self.oversize_save = value
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix +
                                                   'DisplaySetting: set_save_display_oversize_save')
        return error_msg


class LocalShowTextDirect:
    show_info = 'show_info'

    def __init__(self, show_text=None, result_path=''):
        """初始化"""
        self.show_text = show_text
        self.result_path = result_path
        # 设置超限是否存储到txt
        self.oversize_save = True
        # 超限长度
        self.oversize_length = 1000
        # 调用显示次数
        self.show_count = 0
        # 清理阈值次数
        self.clear_count = 10

    def show_text_action(self, key='', data=None):
        """显示"""
        if key == self.show_info:
            self.show_data_to_text_direct(data)

    def show_data_to_text(self, msg=''):
        """直接显示数据"""
        try:
            self.show_text.append(msg)
            self.show_text.moveCursor(QTextCursor.End)
        except Exception as e:
            print(tools_common.get_error_msg(e.args, error_msg_prefix + 'show_data_to_text_direct'))

    def show_data_to_text_direct(self, show_msg=''):
        """显示数据"""
        try:
            length = len(show_msg)
            txt_name = ''
            if length > self.oversize_length:
                if self.oversize_save:
                    now_time = tools_common.get_date_time_ms()
                    txt_name = os.path.join(self.result_path, now_time + '.txt')
                    msg = show_msg[0:self.oversize_length] + '...\n......\n数据过大，只显示部分数据，全部数据已存储在：\n' + txt_name + '\n请查看！\n'
                else:
                    msg = show_msg[0:self.oversize_length] + '...\n......\n数据过大，只显示部分数据\n'
            else:
                msg = show_msg + '\n'
            self.show_data_to_text(msg)

            if txt_name:
                tools_file.save_to_txt(txt_name, show_msg)

            self.show_count += 1
            if self.show_count >= self.clear_count:
                self.show_count = 0
                self.show_text.clear()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_data_to_text')
            self.show_data_to_text(error_msg)
