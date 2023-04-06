
# 用于创建功能按键，名称，及对应的函数
# 各种路径的名称，作为key
import random

from py_tools import tools_common

fun_lib_path = 'lib_path'
fun_result_path = 'result_path'

# 定义各个功能的名称，方便后续读写
fun_name_device = 'device_management'
fun_name_device_info = 'device_info'
fun_name_show_text = 'show_text'
fun_name_show_text_direct = 'show_text_direct'
fun_name_task_center = 'task_center'
fun_name_main_gui = 'main_gui'

fun_path = {
    'lib': '\\Resource\\Lib',
    'result': '\\Result'
}

error_msg_name = 'error_msg'
error_msg_prefix = "error: public: "

# path是指包含的相关路径
fun_property = {
    fun_name_device: {
        'fun_name': fun_name_device,
        'path': {fun_lib_path: '\\Device_LIB\\',
                 fun_result_path: '\\Device_Result\\'}
    },
    fun_name_show_text: {
        'fun_name': fun_name_show_text,
        'path': {fun_result_path: '\\Show_Result\\'}
    },
    fun_name_show_text_direct: {
        'fun_name': fun_name_show_text_direct,
        'path': {fun_result_path: '\\Show_Result\\'}
    }
}


# 定义各个功能类支持的任务类型
task_identify = {
    fun_name_task_center: {
        "fun_id": 6,
        "task_type": {}
    },
    fun_name_main_gui: {
        "fun_id": 8,
        "task_type": {
            'open_gui': 'm0',
            'set_title': 'm1'
        }
    },
    fun_name_device: {
        "fun_id": 13,
        "task_type": {
            'add_device': 'd1',
            'delete_device': 'd7',
            'online_state_changed': 'd8',
            'query_device_info': 'd9'
        }
    },
    fun_name_device_info: {
        "fun_id": 14,
        "task_type": {
            'show_info': 'di1'
        }
    },
    fun_name_show_text: {
        "fun_id": 15,
        "task_type": {
        }
    },
    fun_name_show_text_direct:{
        "fun_id": 16,
        "task_type": {
        }
    },
}


common_task_type = {
    'program_exit': 'c3',  # 通知各进程退出程序
    'initial': 'c4',  # 报告初始化是否完成
    'watch_dog': 'c11',  # 子进程定期发送看门狗
    'main_gui_no_response': 'c12',  # 主进程没有响应
}


def generate_task_id(fun_name=''):
    """生成任务id"""
    # 0_20211018，0表示snmp，20211018表示时间
    task_id = None
    if fun_name in task_identify.keys():
        task_id = str(task_identify[fun_name]['fun_id']) + '_' + tools_common.get_timestamp() + \
                  str(random.randint(100, 999))
    return task_id


def generate_msg_id():
    return tools_common.get_timestamp() + str(random.randint(100, 999))


def encode_transfer_msg(source_id='', destination_id=None, task_id='', msg_id='', data=None):
    """发送数据的格式"""
    # data的格式是字典
    msg = None
    if isinstance(data, dict):
        msg = {
            'source_id': source_id,  # gui_id
            'destination_id': destination_id,  # gui_id
            'task_id': task_id,
            'msg_id': msg_id,
            'data': data
        }
    return msg


def get_gui_id(fun_name='', fun_instance=None):
    """给每个界面编号"""
    # 编号：1_2,1表示界面类型，2表示界面数量的增量
    # 查表public
    if fun_instance is None:
        fun_instance = list()
    gui_id = None
    if fun_name in task_identify.keys():
        fun_id = str(task_identify[fun_name]["fun_id"])
        gui_num = list()
        for instance_temp in fun_instance:
            gui_num.append(instance_temp.fun_property['gui_id'].split('_')[1])
        ava_num = "-1"
        if len(gui_num) <= 0:
            ava_num = "0"
        else:
            for i in range(1000):
                if str(i) not in gui_num:
                    ava_num = str(i)
                    break
        if ava_num != '-1':
            gui_id = fun_id + '_' + ava_num
    return gui_id


def generate_task_id_by_fun_id(fun_id=''):
    """生成任务id"""
    # 0_20211018，0表示snmp，20211018表示时间
    return str(fun_id + '_' + tools_common.get_timestamp() + str(random.randint(100, 999)))


def get_actual_destination_id(dst_id=""):
    """第一位IP"""
    dst_id_actual = dst_id
    try:
        dst_pos = tools_common.find_all_positions_in_src(dst_id, '_')
        if len(dst_pos) > 1:
            dst_id_actual = dst_id[0:dst_pos[1]]
    except Exception as e:
        print(tools_common.get_error_msg(e.args, error_msg_prefix + 'get_actual_destination_id'))
    return dst_id_actual


def get_actual_source_id(src_id=""):
    """最后一位IP"""
    src_pos = tools_common.find_all_positions_in_src(src_id, '_')
    if len(src_pos) > 1:
        src_id = src_id[src_pos[-2] + 1:]
    return src_id


def check_transfer_msg_format(msg=None):
    """检查数据的格式"""
    if isinstance(msg, dict) and \
            'source_id' in msg.keys() and \
            'destination_id' in msg.keys() and \
            'task_id' in msg.keys() and \
            'msg_id' in msg.keys() and \
            'data' in msg.keys() and \
            msg['data'] is not None:
        return True
    else:
        return False


def send_response(fun=None, rev_data=None, data=None):
    """返回信息"""
    if rev_data is None or not check_transfer_msg_format(rev_data):
        return False
    if data is None:
        data = {'error_msg': 'Unexpected Error!'}
    msg = encode_transfer_msg(rev_data['destination_id'],
                              rev_data['source_id'],
                              rev_data['task_id'],
                              rev_data['msg_id'],
                              data)
    if msg is not None:
        fun(msg)
        return True
    return False
