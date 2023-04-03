import os
import time
from multiprocessing import Pipe
from queue import Queue

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

error_msg_prefix = "error: tools_common: "


class BufferPipe:

    def __init__(self, pipe=None, role='', duplex=True):
        self.pipe = pipe
        self.role = role
        self.duplex = duplex

    def write(self, content=None):
        error_msg = ''
        try:
            self.pipe.send(content)
        except Exception as e:
            error_msg = get_error_msg(e.args, error_msg_prefix + "BufferPipe: write")
        return error_msg

    def get(self):
        return self.pipe.recv()

    def put(self, content=None):
        pass

    def get_all(self):
        pass

    def close(self):
        self.pipe.close()

    def readable(self):
        return self.pipe.readable

    def writable(self):
        return self.pipe.writable

    def closed(self):
        return self.pipe.closed

    def empty(self):
        return not self.pipe.poll()


def new_pipe_buffer(duplex=True):
    """创建新的pipe，返回的是两个类"""
    parent, child = Pipe(duplex)
    return BufferPipe(parent, 'parent', duplex), BufferPipe(child, 'child', duplex)


class BufferQueue(Queue):

    def __init__(self):
        Queue.__init__(self)

    def write(self, content):
        try:
            self.put(content)
        except Exception as e:
            error_msg = get_error_msg(e.args, error_msg_prefix + 'BufferQueue: write')
            print(error_msg)


def get_error_msg(e_args=None, msg=''):
    """将错误信息组合"""
    error_msg = msg + '\n'
    if isinstance(e_args, tuple):
        for arg in e_args:
            error_msg += str(arg) + '\n'
    return error_msg


def check_file_exist(path, file_name):
    """检查path是否存在file_name"""
    try:
        if not os.path.exists(os.path.join(path, file_name)):
            return False
        else:
            return True
    except Exception as e:
        print(get_error_msg(e.args, error_msg_prefix + "check_file_exist"))
    return False


def find_all_positions_in_src(str_src='', str_dst=''):
    """找到dst在src的所有位置，按从小到大排列"""
    positions = list()
    if len(str_src) <= 0 or len(str_dst) <= 0 or len(str_dst) > len(str_src):
        return positions
    for i in range(len(str_src) - len(str_dst) + 1):
        src_temp = str_src[i:(i + len(str_dst))]
        if src_temp == str_dst:
            positions.append(i)
    return positions


def load_icon(file=''):
    """加载图标"""
    icon = None
    error_msg = ''
    try:
        if os.path.exists(file):
            pos = find_all_positions_in_src(file, '.')
            if pos:
                file_type = file[pos[len(pos) - 1] + 1:]
                if file_type == 'ico':
                    icon = QIcon(file)
                elif file_type == 'svg':
                    icon = QIcon()
                    icon.addFile(file)
    except Exception as e:
        error_msg = get_error_msg(e.args, error_msg_prefix + 'load_icon')
    return icon, error_msg


def action_objectname(name='', tree_widget=None, objectname=''):
    """返回一个带有ObjectName的QAction"""
    action = QAction(name, tree_widget)
    action.setObjectName(objectname)
    return action


def get_all_tree_child(item):
    """获取所有的子类"""
    children = list()
    count = item.childCount()
    if not count:
        children.append(item.text(0))
    else:
        for i in range(count):
            child_item = item.child(i)
            children += get_all_tree_child(child_item)
    return children


def get_text_x(text=''):
    """文本的起始点"""
    midpoint = 50
    x = int(midpoint - midpoint * len(text) / 14)
    if x < 0:
        x = 1
    return x + 5


def get_device_no(last_no=''):
    """计算设备编号"""
    next_no = ''
    if last_no:
        if '-' in last_no:
            nos = last_no.split('-')
            if len(nos) == 2:
                if nos[0].isdigit() and nos[1].isdigit():
                    b = int(nos[1]) + 1
                    a = int(nos[0])
                    if b >= 100:
                        b = 0
                        a += 1
                    next_no = str(a) + '-' + str(b)
    else:
        next_no = '0-0'
    return next_no


def get_timestamp():
    """生成时间戳"""
    rec_time_now = time.strftime("%Y%m%d%H%M%S", time.localtime()) + get_ms()
    return str(rec_time_now)


def get_ms():
    """get millisecond of now in string of length 3"""
    ms = str(int(time.time() * 1000) % 1000)
    if len(ms) == 1:
        return '00' + ms
    if len(ms) == 2:
        return '0' + ms
    return ms


def time_sleep(time_interval=0, to_stop=False):
    """等待时间"""
    if time_interval > 0:
        time_interval_ms = time_interval * 10
        for i in range(time_interval_ms):
            time.sleep(0.1)
            # self.msleep(100)
            if to_stop:
                break


def str_find_pos(str_src=''):
    """返回str_dst在str_src的所有位置"""
    pos = list()
    str_dst = '\\'
    # 如果str_src，或者str_dst为空，返回
    # str_dst比str_src长也返回
    if len(str_src) <= 0 or len(str_dst) <= 0 or len(str_dst) > len(str_src):
        return pos
    for i in range(len(str_src)):
        src_temp = str_src[i:(i + 1)]
        if src_temp == str_dst:
            pos.append(i)
    return pos


def check_dir(path=''):
    """检查path是否存在，如果不存在就新建"""
    # 'C:\\Users\\PycharmProjects\\'
    pos = str_find_pos(path)
    pos += [len(path)]
    for i in range(len(pos)):
        temp_path = path[0:pos[i]]
        if not os.path.exists(temp_path):
            try:
                os.mkdir(temp_path)
            except Exception as e:
                print('创建目录失败！')
                print(e.args)
                return False
    return True


def string_lstrip(src='', dst='', once=True):
    # s.lstrip(rm)       删除s字符串中开头处，位于 rm删除序列的字符
    # once：True表示只删除第一个，False表示删除所有
    if src == dst:
        return ''
    elif len(dst) > len(src):
        return src
    if once:
        if src[0: len(dst)] == dst:
            return src[len(dst):]
        else:
            return src
    else:
        pos = 0
        for i in range(int(len(src) / len(dst))):
            if src[i * len(dst): i * len(dst) + len(dst)] == dst:
                pos = i * len(dst) + len(dst)
            else:
                break
        return src[pos:]


def copy_dict_except(src_dict=None, except_keys=None):
    """copy a dict"""
    if except_keys is None:
        except_keys = list()
    dst_dict = {}
    if isinstance(src_dict, dict) and isinstance(except_keys, list):
        for key, value in src_dict.items():
            if key not in except_keys:
                key_temp = key
                value_temp = value
                dst_dict[key_temp] = value_temp
    return dst_dict
