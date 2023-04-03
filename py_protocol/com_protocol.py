import threading

from py_taskcenter import public
from py_tools import tools_common

error_msg_prefix = "error: com_protocol: "


class UdpProtocol:

    def __init__(self, gui_id=''):
        """初始化"""
        # 路由表，格式：{gui_id: class.start_one_task, gui_id2: task_center_pipe}
        self.buffer_route = {}
        # 线程锁
        self.buffer_route_lock = None
        # 本进程的IP
        self.gui_id = gui_id
        # 附加显示信息
        self.additional_info = ''

    def initial(self):
        """初始化"""
        # 线程锁
        self.buffer_route_lock = threading.Lock()

    def add_route(self, gui_id='', route=None):
        """添加一条路由"""
        try:
            if self.buffer_route_lock:
                self.buffer_route_lock.acquire()
            # 当前不存在该路由时，才会添加
            if gui_id not in self.buffer_route.keys():
                self.buffer_route[gui_id] = route
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "add_route")
            print(error_msg)
        finally:
            if self.buffer_route_lock:
                self.buffer_route_lock.release()

    def update_route(self, gui_id='', route=None):
        """更新一条路由"""
        try:
            if self.buffer_route_lock:
                self.buffer_route_lock.acquire()
            # 无论此前是否存在该路由，均会被写入
            self.buffer_route[gui_id] = route
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "update_route")
            print(error_msg)
        finally:
            if self.buffer_route_lock:
                self.buffer_route_lock.release()

    def delete_route(self, gui_id=''):
        """删除一条路由"""
        try:
            if self.buffer_route_lock:
                self.buffer_route_lock.acquire()
            if gui_id in self.buffer_route.keys():
                self.buffer_route.pop(gui_id)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "delete_route")
            print(error_msg)
        finally:
            if self.buffer_route_lock:
                self.buffer_route_lock.release()

    def transfer_msg(self, msg=None, print_on=False):
        """转发数据"""
        transfer_msg_protocol(self.buffer_route, self.buffer_route_lock,
                              msg, self.gui_id,
                              self.additional_info, print_on)


def transfer_msg_protocol(buffer_route=None, buffer_route_lock=None,
                          msg=None, gui_id='',
                          append_error_msg='', print_on=False):
    """后台任务的接口，首先由此进行分发"""
    # buffer_route：路由表，buffer_local：当前进程的Queue，buffer_route_lock：线程锁，读写路由表时使用
    # msg：报文数据，gui_id：当前进程的地址，append_error_msg：打印时的附加信息，print_on：是否打印过程信息
    # 这里处理的数据来源有两类，一类是本进程的内部类写入buffer的数据，一类是其他进程写入pipe的数据
    # 这里相当于之前的转发线程，分析数据之后转发至其他类中执行，所以又有执行的功能
    try:
        if print_on:
            print(append_error_msg + ": transfer_msg_protocol: received msg: ")
            print(msg)
            print()
        # 如果source_id或者destination_id为空，则丢弃
        # 所有的数据都需要符合相同的格式
        if isinstance(msg, dict) and \
                'source_id' in msg.keys() and \
                'destination_id' in msg.keys() and \
                msg['source_id'] and \
                msg['destination_id']:

            # 说明数据是发往外部进程
            # 首先对source_id加上转发进程的前缀gui_id
            if len(msg['source_id']) < len(gui_id) or msg['source_id'][0:len(gui_id)] != gui_id:
                msg['source_id'] = gui_id + '_' + msg['source_id']

            # 增加支持多目的地址转发，
            # 存储的格式是{'destination_id'： ['dst0', 'dst1', ...]}
            if isinstance(msg['destination_id'], list):
                for dst_id_temp in msg['destination_id']:
                    transfer_one_msg(gui_id, dst_id_temp, msg,
                                     buffer_route, buffer_route_lock,
                                     append_error_msg, print_on)
            else:
                # 然后是对于destination_id，要去掉gui_id前缀
                transfer_one_msg(gui_id, msg['destination_id'], msg,
                                 buffer_route, buffer_route_lock,
                                 append_error_msg, print_on)
    except Exception as e:
        if print_on:
            print(tools_common.get_error_msg(e.args, error_msg_prefix + append_error_msg + ": transfer_msg_protocol2"))


def transfer_one_msg(gui_id='', dst_id='', msg=None,
                     buffer_route=None, buffer_route_lock=None,
                     append_error_msg='', print_on=False):
    """转发一个地址"""
    # 如果是发给转发线程的信息，不需要去掉gui_id
    # 转发线程存储的是{gui_id: class.start_one_task, gui_id2: task_center_pipe}
    # 为了区分数据是发送给本地的还是发送给其他进程，需要在dst_id中进行标记
    # 如，假设task_center的gui_id是9_0，那么9_0_3_1是发送给task_center的数据，而3_1是发送给本地的数据
    # 所以需要先分解下一跳的dst_id
    # 对于src_id，需要加上转发线程的gui_id
    # 对于dst_id，需要减去转发线程的gui_id
    try:
        if buffer_route_lock:
            buffer_route_lock.acquire()
        # 如果数据是发送给主界面，也就是下一跳就是主界面，就不要减
        # 先减去转发线程的gui_id之后再看下一跳
        if dst_id == gui_id:
            # 如果目的地址是转发类所在的线程，根据task_id确定下一跳地址
            fun_id = str(msg['task_id']).split('_')[0]
            dst_id_next = fun_id + '_0'
        else:
            # dst，需要减去本转发线程的gui_id，比如转发线程的gui_id是6_0，6_0_3_2减去之后就是3_2，2_1减去之后还是2_1
            # 去掉转发线程的dui_id，也就是主线程（主界面）的gui_id
            dst_id = tools_common.string_lstrip(dst_id, gui_id)
            dst_id = tools_common.string_lstrip(dst_id, '_')
            # 首先提取下一跳的地址，比如：8_0_2_1，则下一跳是8_0，3_1的下一跳是3_1
            dst_id_next = public.get_actual_destination_id(dst_id)
        msg['destination_id'] = dst_id
        if print_on:
            print(append_error_msg + ": transfer_msg_protocol: send out msg: ")
            print(msg)
            print()
        if dst_id_next in buffer_route.keys():
            # 如果能够找到地址，就转发
            buffer_route[dst_id_next].write(msg)
        else:
            pass
    except Exception as e:
        if print_on:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "transfer_msg_one2")
            print("transfer center: 转发: " + error_msg + append_error_msg)
            print(msg)
            print()
    finally:
        if buffer_route_lock:
            buffer_route_lock.release()
