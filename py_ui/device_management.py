import os

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QPoint, QFile, QIODevice, Qt
from PyQt5.QtGui import QPainter, QCursor, QPen
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QScrollArea, QMenu, QAction, QTreeWidgetItem, QTreeWidget
from lxml import etree

from py_taskcenter import public
from py_ui import add_device_gui
from py_tools import tools_common
from py_tools.tools_common import action_objectname

error_msg_prefix = "error: device_management: "


class DeviceManage:
    lib_path = ''

    def __init__(self, main_window=None):
        """初始化"""
        self.result_path = ''

        # 此界面的主界面
        self.main_window = main_window
        self.win_main = main_window.win_main
        self.exited = False

        self.fun_name = ''
        self.gui_id = ''

        # # 添加设备界面
        self.win_add = add_device_gui.AddDeviceUi()
        self.win_add.signal.connect(self.start_one_task)

        # 存储所有设备，用ip标识唯一设备, {ip: {'device': SvgDevice}}
        self.all_device = {}
        # 点击设备，被选中的设备，存的是设备的ip
        self.clicked_device = []
        # 设备管理树点击选中的设备，存的也是设备的ip
        self.selected_device = []

        # 管理设备的树，{'项目1': {'item': tree_main, 'children': {'类别1': tree_child}}}
        self.device_tree = dict()
        # device_tree的控件发生变化的标识
        self.device_tree_changed = False

        # 自定义的树
        self.device_tree_widget = None

        # 背景图像相关的变量
        self.background_data = None
        self.background_area = None
        self.background_image = None

        # 设备树中显示在线离线的图标
        self.device_online_icon = None
        self.device_offline_icon = None
        self.net_online_icon = None
        self.net_offline_icon = None
        self.project_online_icon = None
        self.project_offline_icon = None

        # 获取lib_path之后，标记是否需要加载背景图片
        self.should_load_background_image = False

        # 设备设备图像显示的比例
        self.device_ratio = 1.0
        # self.device_height = 100
        # 绘制下一个设备图像的起始点
        self.device_next_x = 0
        self.device_next_y = 0
        # 缩放的比例
        self.zoom_ratio = 1.0
        # 设备绘制抵达边缘的次数，用于计算到达边缘之后下一次设备绘制的起始点
        self.cross_count = 0
        # 当前的设备编号，用于计算下一个可用的设备编号
        self.current_device_no = ''

        self.menu_font = QtGui.QFont()
        self.menu_font.setPointSize(10)  # 括号里的数字可以设置成自己想要的字体大小
        self.menu_font.setFamily("微软雅黑")

        self.initial_finished = False

    def _initial(self):
        """配置初始化"""
        self.result_path = public.fun_property[public.fun_name_device]['path'][public.fun_result_path]
        self.lib_path = public.fun_property[public.fun_name_device]['path'][public.fun_lib_path]

    def create_main_gui(self):
        """创建主界面"""
        self._initial()

        # 功能区各按键的响应函数
        self.win_main.zoom_in_btn.clicked.connect(lambda: self.resize_background_img(1.2))  # 5
        self.win_main.zoom_out_btn.clicked.connect(lambda: self.resize_background_img(0.8))

        # 添加设备
        self.win_main.add_btn.clicked.connect(self.win_add.display)

        self.initial_tree()

        self.load_background_image()
        SvgDevice.lib_path = self.lib_path

        # 加载设备在线图标
        self.load_online_icon()

        self.initial_finished = True

    def initial_tree(self):
        """设备树初始化"""
        self.device_tree_widget = QTreeWidget(self.win_main.main_device_tab)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.device_tree_widget.setFont(font)
        self.device_tree_widget.setObjectName("device_tree")
        self.win_main.device_form_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.device_tree_widget)

        # 设置列数
        self.device_tree_widget.setColumnCount(1)
        # 设置树形控件头部的标题
        self.device_tree_widget.setHeaderLabels(['设备列表'])
        # self.device_tree_widget.setHeaderHidden(True)
        # 打开右键菜单策略
        self.device_tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        # 右键绑定事件
        self.device_tree_widget.customContextMenuRequested.connect(self.device_tree_right_btn)
        # 点击事件
        self.device_tree_widget.clicked.connect(self.device_tree_left_btn)

    def gen_branch(self, node: QTreeWidgetItem, text=''):
        """ 给定某个节点和列表 在该节点生成列表内分支"""
        item = None
        try:
            item = QTreeWidgetItem()
            item.setText(0, text)
            node.addChild(item)

            self.device_tree_widget.expandItem(node)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'gen_branch')
            self.show_data_to_text(error_msg)
        return item

    def device_tree_right_btn(self, pos):
        """设备管理树的右键"""
        try:
            item = self.device_tree_widget.currentItem()
            item1 = self.device_tree_widget.itemAt(pos)

            if item and item1:
                text = item.text(0)
                menu = QMenu()
                menu.setFont(self.menu_font)
                if text in self.device_tree.keys():
                    menu.addAction(action_objectname(u'添加设备', self.device_tree_widget, 'new_device'))
                else:
                    match = False
                    for tree_items in self.device_tree.values():
                        if text in tree_items['children'].keys():
                            menu.addAction(action_objectname(u'添加设备', self.device_tree_widget, 'new_device'))
                            match = True
                            break
                    if not match:
                        menu.addAction(action_objectname(u'添加设备', self.device_tree_widget, 'new_device'))
                menu.triggered[QAction].connect(self.device_tree_btn_process)
                menu.exec_(QCursor.pos())
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'device_tree_right_btn')
            self.show_data_to_text(error_msg)

    def device_tree_btn_process(self, obj):
        """设备列表树的菜单响应函数"""
        try:
            # menu的object名称
            object_name = obj.objectName()
            # 当前的tree控件
            current_item = self.device_tree_widget.currentItem()
            # 父控件
            item_parent = None
            # 父控件的父控件
            item_parent_parent = None
            if current_item.parent():
                item_parent = current_item.parent()
            if item_parent and item_parent.parent():
                item_parent_parent = item_parent.parent()

            if object_name == 'new_device':
                if item_parent and item_parent_parent:
                    # 此时是点击的ip
                    self.win_add.project_name = item_parent_parent.text(0)
                    self.win_add.net_name = item_parent.text(0)
                    self.win_add.display()
                elif item_parent and not item_parent_parent:
                    # 此时点击的是类别
                    self.win_add.project_name = item_parent.text(0)
                    self.win_add.net_name = current_item.text(0)
                    self.win_add.display()
                elif not item_parent and not item_parent_parent:
                    # 此时点击的是项目
                    self.win_add.project_name = current_item.text(0)
                    self.win_add.net_name = ''
                    self.win_add.display()
                else:
                    self.show_data_to_text('添加设备未知异常！\n')
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'device_tree_btn_process')
            self.show_data_to_text(error_msg)

    def new_net(self, project_item=None, net_name=''):
        """创建新的类别"""
        try:
            if not net_name:
                net_name = self.generate_available_net_name()
            if project_item and net_name and net_name not in self.device_tree[project_item.text(0)]['children'].keys():
                project_name = project_item.text(0)
                # 创建类别名，第二级
                net_item = self.gen_branch(self.device_tree[project_name]['item'], net_name)
                if self.net_online_icon:
                    net_item.setIcon(0, self.net_online_icon)
                self.device_tree[project_name]['children'][net_name] = net_item

        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'new_net')
            self.show_data_to_text(error_msg)

    def new_net_by_project_name(self, project_name='', net_name=''):
        """创建新的类别"""
        try:
            project_item = None
            if project_name in self.device_tree.keys():
                project_item = self.device_tree[project_name]['item']
            if not project_item:
                self.new_project(project_name)
            self.new_net(project_item, net_name)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'new_net_by_project_name')
            self.show_data_to_text(error_msg)

    def new_project(self, project_name=''):
        """创建新的项目"""
        try:
            if not project_name:
                project_name = self.generate_available_net_name('新项目', 'project')
            if project_name not in self.device_tree.keys():
                # 创建项目名，第一级
                tree_main = QTreeWidgetItem(self.device_tree_widget)
                tree_main.setText(0, project_name)
                if self.project_online_icon:
                    tree_main.setIcon(0, self.project_online_icon)
                self.device_tree[project_name] = {'item': tree_main, 'children': {}}

        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'new_project')
            self.show_data_to_text(error_msg)

    def generate_available_net_name(self, basic_name='新类别', tree_class='net'):
        """返回一个可用的类别名称"""
        net_name = ''
        try:
            for i in range(5000):
                net_name = basic_name + str(i)
                available = True
                for keys, values in self.device_tree.items():
                    if tree_class == 'net' and net_name in values['children'].keys():
                        available = False
                        break
                    elif tree_class == 'project' and net_name in keys:
                        available = False
                        break
                if available:
                    break
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'net_name')
            self.show_data_to_text(error_msg)
        return net_name

    def device_tree_left_btn(self, index):
        """点击事件"""
        # item = self.device_tree_widget.itemAt(index)
        error_msg = ''
        item = self.device_tree_widget.currentItem()
        children = tools_common.get_all_tree_child(item)
        self.clear_selected_device()
        for child in children:
            try:
                if child in self.all_device.keys():
                    self.all_device[child]['device'].set_selected_state(True)
                    self.selected_device.append(child)
            except Exception as e:
                error_msg += tools_common.get_error_msg(e.args, error_msg_prefix + 'device_tree_left_btn' + child)
        if error_msg:
            self.show_data_to_text(error_msg)

    def clear_selected_device(self):
        """去选中设备"""
        error_msg = ''
        for ip in self.selected_device:
            try:
                self.all_device[ip]['device'].set_selected_state(False)
                self.all_device[ip]['device'].tree_item.setSelected(False)
            except Exception as e:
                error_msg += tools_common.get_error_msg(e.args, error_msg_prefix + 'clear_selected_device' + ip)
        self.selected_device.clear()
        if error_msg:
            self.show_data_to_text(error_msg)

    def load_background_image(self):
        """加载背景图片"""
        # print(self.lib_path)
        if not tools_common.check_file_exist(self.lib_path, 'background.svg'):
            self.show_data_to_text('背景图片文件缺失，软件无法运行，请检查！\n')
            return
        try:
            background_image_file = QFile(os.path.join(self.lib_path, 'background.svg'))
            background_image_file.open(QIODevice.ReadOnly)
            self.background_data = background_image_file.readAll()
            background_image_file.close()

            self.background_area = QScrollArea()
            self.background_image = SvgBackground(self.background_area)
            # self.background_image = SvgBackground(self.background_image)
            self.background_image.renderer().load(self.background_data)
            self.background_area.setWidget(self.background_image)
            self.win_main.svg_layout_2.addWidget(self.background_area)

            # 声明在groupBox创建右键菜单
            self.background_image.setContextMenuPolicy(Qt.CustomContextMenu)
            # 连接到菜单显示函数
            self.background_image.customContextMenuRequested.connect(
                lambda: self.create_right_menu(self.background_image))
            self.background_image.signal.connect(self.device_callback)
            self.background_image.show()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'load_background_image')
            self.show_data_to_text(error_msg)

    def load_online_icon(self):
        """加载设备在线离线图标"""
        device_online_icon = 'device_online.ico'
        device_offline_icon = 'device_offline.ico'
        net_online_icon = 'net_online.ico'
        net_offline_icon = 'net_offline.ico'
        project_online_icon = 'project_online.ico'
        project_offline_icon = 'project_offline.ico'
        self.device_online_icon, error_msg = tools_common.load_icon(os.path.join(self.lib_path, device_online_icon))
        self.device_offline_icon, error_msg = tools_common.load_icon(os.path.join(self.lib_path, device_offline_icon))
        self.net_online_icon, error_msg = tools_common.load_icon(os.path.join(self.lib_path, net_online_icon))
        self.net_offline_icon, error_msg = tools_common.load_icon(os.path.join(self.lib_path, net_offline_icon))
        self.project_online_icon, error_msg = tools_common.load_icon(os.path.join(self.lib_path, project_online_icon))
        self.project_offline_icon, error_msg = tools_common.load_icon(os.path.join(self.lib_path, project_offline_icon))

    def create_device(self, host_info=None, is_connected=False, device_type='unknown'):
        """创建设备图标"""
        # 设备图标是设备的一部分，只是现在暂时不涉及其他逻辑，就先用图标表示设备
        # 两个属性，类别名称和设备编号，类别名称如果没有标识，就默认为网块1
        # 设备编号由系统分配，0-0,
        try:
            net_name = host_info['net_name']
            device_ip = host_info['host']

            if device_ip in self.all_device.keys():
                if is_connected != self.all_device[device_ip]['device'].is_connected:
                    self.all_device[device_ip]['device'].is_connected = is_connected
                    self.all_device[device_ip]['device'].set_connected_state()

                if device_type != self.all_device[device_ip]['device'].device_type:
                    self.all_device[device_ip]['device'].device_type = device_type
                    self.all_device[device_ip]['device'].set_device_type()

            else:
                device_no = tools_common.get_device_no(self.current_device_no)

                # 当前默认都挂在项目1下面
                project_name = '项目1'
                if 'project_name' in host_info.keys() and host_info['project_name']:
                    project_name = host_info['project_name']

                # 在设备管理树上添加设备编号
                if not net_name:
                    net_name = '类别1'

                self.new_project(project_name)

                if net_name not in self.device_tree[project_name]['children'].keys():
                    # 创建类别名，第二级
                    self.new_net(self.device_tree[project_name]['item'], net_name)

                # 创建设备名，第三级
                # child(1) 意思是分支的第1个节点, 序号从0算起
                tree_item = self.gen_branch(self.device_tree[project_name]['children'][net_name], device_ip)

                device = SvgDevice(self.background_image, host_info,
                                   is_connected, device_type, device_no, project_name)
                cs = device.sizeHint()
                start_x = int(self.device_next_x * self.zoom_ratio)
                start_y = int(self.device_next_y * self.zoom_ratio)
                device.setGeometry(start_x,
                                   start_y,
                                   int(cs.width() * self.device_ratio * self.zoom_ratio),
                                   int(cs.height() * self.device_ratio * self.zoom_ratio))
                device.show()

                cs2 = device.size()
                self.device_next_x = int(self.device_next_x + cs2.width() * self.device_ratio / (1.5 * self.zoom_ratio))
                self.device_next_y = int(self.device_next_y + cs2.height() * self.device_ratio / (10 * self.zoom_ratio))
                center_x = start_x + cs2.width() / 2
                center_y = start_y + cs2.height() / 2
                device.center_x = int(center_x)
                device.center_y = int(center_y)

                if self.device_next_x * self.zoom_ratio > (self.background_image.size().width() - cs2.width()) or \
                        self.device_next_y * self.zoom_ratio > (self.background_image.size().height() - cs2.height()):
                    self.cross_count += 1
                    self.device_next_x = 0
                    self.device_next_y = self.cross_count * cs2.height()

                # 声明在groupBox创建右键菜单
                device.setContextMenuPolicy(Qt.CustomContextMenu)
                device.customContextMenuRequested.connect(lambda: self.device_right_btn(device))  # 连接到菜单显示函数

                device.signal.connect(self.device_callback)

                self.current_device_no = device.device_no

                if device_ip not in self.all_device.keys():
                    self.all_device[device_ip] = {}
                    self.all_device[device_ip]['device'] = device
                    device.tree_item = tree_item
                    device.device_online_icon = self.device_online_icon
                    device.device_offline_icon = self.device_offline_icon
                else:
                    if 'device' in self.all_device[device_ip].keys() and \
                            isinstance(self.all_device[device_ip]['device'], SvgDevice):
                        self.all_device[device_ip]['device'].delete()

                    self.all_device[device_ip]['device'] = device
                    device.tree_item = tree_item
                    device.device_online_icon = self.device_online_icon
                    device.device_offline_icon = self.device_offline_icon
                device.set_connected_state()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'create_device')
            self.show_data_to_text(error_msg)

    def show_device(self, device=None):
        """显示设备信息"""
        try:
            online = {True: '在线', False: '离线'}
            msg = "设备信息：\nHost：" + device.device_ip + "，名称：" + device.device_type + \
                  "，项目：" + device.project_name + "，类别：" + device.net_name + \
                  "，当前：" + online[device.is_connected] + "\n"
            data = {
                'task_type':
                    public.task_identify[public.fun_name_device_info]["task_type"]["show_info"],
                'append_data': msg
            }
            self.send_request_to_main_gui(data, public.fun_name_device_info)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'show_device')
            self.show_data_to_text(error_msg)

    def delete_device(self, device=None):
        """删除设备"""
        try:
            ip = device.device_ip
            self.delete_device_net([ip])
            device.delete()
            self.all_device.pop(ip)

            self.show_data_to_text('已删除设备：' + ip + '\n')

        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'delete_device')
            self.show_data_to_text(error_msg)

    def delete_device_net(self, ip_list=None):
        """删除后台的设备信息"""
        try:
            if isinstance(ip_list, list):
                data = {
                    'task_type':
                        public.task_identify[self.fun_name]["task_type"]["delete_device"],
                    'append_data': ip_list
                }
                self.send_request_to_task_center(data)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'delete_device_net')
            self.show_data_to_text(error_msg)

    def device_callback(self, data: dict):
        """设备的处理函数"""
        # {'mousePressEvent': self.device_ip}
        # {'background_mousePressEvent': None}
        if 'mousePressEvent' in data.keys():
            try:
                ip = data['mousePressEvent']
                for ip_temp in self.clicked_device:
                    if ip != ip_temp and ip_temp in self.all_device.keys():
                        device = self.all_device[ip_temp]['device']
                        device.set_clicked_state(False)
                        device.tree_item.setSelected(False)
                self.clicked_device.clear()
                self.clicked_device.append(ip)
                self.all_device[ip]['device'].tree_item.setSelected(True)
            except Exception as e:
                error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'device_callback: mousePressEvent')
                self.show_data_to_text(error_msg)
        elif 'background_mousePressEvent' in data.keys():
            try:
                for ip_temp in self.clicked_device:
                    if ip_temp in self.all_device.keys():
                        device = self.all_device[ip_temp]['device']
                        device.set_clicked_state(False)
                        device.tree_item.setSelected(False)
                self.clicked_device.clear()

                self.clear_selected_device()
            except Exception as e:
                error_msg = tools_common.get_error_msg(e.args,
                                                       error_msg_prefix + 'device_callback: background_mousePressEvent')
                self.show_data_to_text(error_msg)
        elif 'background_select' in data.keys():
            # {'background_select': {'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1}}
            try:
                x0 = data['background_select']['x0']
                x1 = data['background_select']['x1']
                y0 = data['background_select']['y0']
                y1 = data['background_select']['y1']
                for ip, value in self.all_device.items():
                    # device = value['device']
                    center_x = value['device'].center_x
                    center_y = value['device'].center_y
                    if x0 <= center_x <= x1:
                        if y0 <= center_y <= y1:
                            value['device'].set_clicked_state(True)
                            self.clicked_device.append(ip)
                        elif ip in self.clicked_device:
                            value['device'].set_clicked_state(False)
                            self.clicked_device.remove(ip)
                    elif ip in self.clicked_device:
                        value['device'].set_clicked_state(False)
                        self.clicked_device.remove(ip)
            except Exception as e:
                error_msg = tools_common.get_error_msg(e.args,
                                                       error_msg_prefix + 'device_callback: background_select')
                self.show_data_to_text(error_msg)

    def resize_background_img(self, ratio=1.0):
        """改变图片大小"""
        try:
            cs = self.background_image.size()
            re_width = int(cs.width() * ratio)
            re_height = int(cs.height() * ratio)
            if (ratio < 1.0 and re_width > self.background_area.size().width() and
                re_height > self.background_area.size().height()) or \
                    (1.0 < ratio and self.zoom_ratio < 2.0):
                self.background_image.setFixedWidth(re_width)
                self.background_image.setFixedHeight(re_height)
                self.background_image.show()

                self.resize_device_img(ratio)

                self.zoom_ratio = self.zoom_ratio * ratio
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'resize_background_img')
            self.show_data_to_text(error_msg)

    def resize_device_img(self, ratio=1.0):
        """改变所有设备图像的大小"""
        for device_info in self.all_device.values():
            try:
                device = device_info['device']
                cs2 = device.size()
                pos = device.pos()
                start_x = int(pos.x() * ratio)
                start_y = int(pos.y() * ratio)
                device.setGeometry(start_x, start_y,
                                   int(cs2.width() * ratio), int(cs2.height() * ratio))
                device.show()

                center_x = int(start_x + device.size().width() / 2)
                center_y = int(start_y + device.size().height() / 2)
                device.center_x = center_x
                device.center_y = center_y
                # self.all_device[device.device_ip]['position'] = {'x': int(center_x), 'y': int(center_y)}
            except Exception as e:
                error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'resize_device_img')
                self.show_data_to_text(error_msg)

    # 创建右键菜单函数
    def create_right_menu(self, device):
        # 菜单对象
        menu = QMenu(device)
        menu.setFont(self.menu_font)

        action_a = QAction(u'example1', device)  # 创建菜单选项对象
        # action_a.setShortcut('Ctrl+S')  # 设置动作A的快捷键
        menu.addAction(action_a)  # 把动作A选项对象添加到菜单self.groupBox_menu上

        action_b = QAction(u'example2', device)
        menu.addAction(action_b)

        # 声明当鼠标在groupBox控件上右击时，在鼠标位置显示右键菜单   ,exec_,popup两个都可以，
        menu.popup(QCursor.pos())

    def device_right_btn(self, device=None):
        """设备的右键"""
        menu = QMenu(device)
        menu.setFont(self.menu_font)

        action_show = QAction(u'显示设备信息', device)
        action_show.triggered.connect(lambda: self.show_device(device))
        action_delete = QAction(u'删除设备', device)
        action_delete.triggered.connect(lambda: self.delete_device(device))

        menu.addAction(action_show)
        menu.addAction(action_delete)

        # 声明当鼠标在groupBox控件上右击时，在鼠标位置显示右键菜单   ,exec_,popup两个都可以，
        menu.popup(QCursor.pos())

    def write(self, rev_data=None):
        """接收到的任务"""
        print('device_management: received: ')
        print(rev_data)
        print()
        self.start_one_task(rev_data)

    def start_one_task(self, rev_data=None):
        """响应任务"""
        # print(error_msg_prefix + 'start_one_task')
        # print(rev_data)
        # print()
        if isinstance(rev_data, dict):
            if 'data' in rev_data.keys() and 'task_type' in rev_data['data'].keys():
                if str(rev_data['data']['task_type']) == \
                        str(public.task_identify[self.fun_name]["task_type"]['add_device']):
                    self.response_of_add_device(rev_data)
                elif str(rev_data['data']['task_type']) == \
                        str(public.task_identify[self.fun_name]["task_type"]['delete_device']):
                    self.response_of_delete_device(rev_data)
                elif str(rev_data['data']['task_type']) == \
                        str(public.task_identify[self.fun_name]["task_type"]['online_state_changed']):
                    self.event_of_online_state_changed(rev_data)
                else:
                    self.response_of_undefined_task_type(rev_data)
            elif 'add_device' in rev_data.keys():
                self.add_device_service(rev_data, 'add_device')

    def response_of_add_device(self, rev_data=None):
        """添加设备"""
        try:
            error_msg = rev_data['data'][public.error_msg_name]
            if rev_data['data']['task_success']:
                host_info_list = rev_data['data']['append_data']
                host_info_success = rev_data['data'][rev_data['data']['task_type']]
                self._add_device_one_by_one(host_info_list, host_info_success, error_msg)

        except Exception as e:
            self.show_data_to_text(e.args, error_msg_prefix + "response_of_add_device")

    def response_of_delete_device(self, rev_data=None):
        """删除设备的结果"""
        try:
            error_msg = rev_data['data'][public.error_msg_name]
            if error_msg:
                self.show_data_to_text(error_msg)
        except Exception as e:
            self.show_data_to_text(e.args, error_msg_prefix + "response_of_delete_device_net")

    def event_of_online_state_changed(self, rev_data=None):
        """设备状态改变事件"""
        try:
            state_changed_host = rev_data['data']['append_data']
            for ip, state in state_changed_host.items():
                if ip in self.all_device.keys():
                    device = self.all_device[ip]['device']
                    if device.is_connected != state:
                        device.is_connected = state
                        device.set_connected_state()
                        if state:
                            if self.device_online_icon:
                                device.tree_item.setIcon(0, self.device_online_icon)
                            self.show_data_to_text('设备：' + ip + '上线！\n')
                        else:
                            if self.device_offline_icon:
                                device.tree_item.setIcon(0, self.device_offline_icon)
                            self.show_data_to_text('设备：' + ip + '掉线！\n')
                    elif state:
                        self.show_data_to_text('设备：' + ip + '在线！\n')
        except Exception as e:
            self.show_data_to_text(e.args, error_msg_prefix + "response_of_delete_device_net")

    def _add_device_one_by_one(self, host_info_list=None, device_id_list=None, error_msg_list=None,
                               must_login_success=True):
        """添加设备"""
        try:
            if len(host_info_list) == len(device_id_list) == len(error_msg_list):
                for i in range(len(host_info_list)):
                    if not must_login_success or device_id_list[i]:
                        if host_info_list[i]['host']:
                            self.create_device(host_info_list[i], device_id_list[i], host_info_list[i]['name'])
                        else:
                            if host_info_list[i]['project_name']:
                                self.new_project(host_info_list[i]['project_name'])
                            if host_info_list[i]['net_name']:
                                self.new_net_by_project_name(host_info_list[i]['project_name'],
                                                             host_info_list[i]['net_name'])
                    if error_msg_list[i]:
                        self.show_data_to_text(error_msg_list[i])
            else:
                self.show_data_to_text('添加设备失败，后台返回数据错误！\n')
        except Exception as e:
            self.show_data_to_text(e.args, error_msg_prefix + "_add_device_one_by_one")

    def response_of_undefined_task_type(self, rev_data=None):
        """未定义的功能"""
        try:
            print(error_msg_prefix + 'response_of_undefined_task_type')
            print(rev_data)
        except Exception as e:
            self.show_data_to_text(e.args, error_msg_prefix + "response_of_undefined_task_type")

    def add_device_service(self, rev_data=None, task_type=''):
        """添加设备"""
        host_info = rev_data[task_type]
        self.add_device_action(host_info)

    def add_device_action(self, host_info=None):
        """添加一台设备"""
        # host_info，MGMT的信息
        # show_info，是否显示net_name和ip到表格
        # must_connected，是否一定要能够连接上才创建one_device
        # 2 搜索ip是否重复
        result = self.is_in_device_dict(host_info)

        if result:
            # 已有ip，添加失败，对应的错误代码在，add_device_error_code
            self.win_add.win_main.login_host_label.setText('IP已存在')
        else:
            # 服务0
            # 发送保存结果的目录
            data = {
                'task_type': public.task_identify[self.fun_name]["task_type"]["add_device"],
                'append_data': [host_info]
            }
            self.send_request_to_task_center(data)

            self.show_data_to_text('正在添加设备：' + host_info['host'] + '，请稍候\n')
            self.win_add.win_main.login_host_label.setText('')

    def is_in_device_dict(self, host_info=None):
        """判断设备ip是否存在"""
        # 判断是否存在相同的host_info
        # 20220916，ip相同即认为存在相同的设备
        exist = False
        try:
            if host_info['host'] in self.all_device.keys() and \
                    self.all_device[host_info['host']]['device'].is_connected:
                exist = True
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'is_in_device_dict')
            self.show_data_to_text(error_msg)

        return exist

    def send_request_to_task_center(self, data=None):
        """给task center发送服务请求"""
        task_id = public.generate_task_id(self.fun_name)
        msg_id = public.generate_msg_id()

        msg = public.encode_transfer_msg(self.gui_id,
                                         self.main_window.task_center_gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.send_msg(msg)

    def send_request_to_main_gui(self, data=None, task_fun_name=""):
        """给main gui发送服务请求"""
        if not task_fun_name:
            task_fun_name = self.fun_name
        task_id = public.generate_task_id(task_fun_name)
        msg_id = public.generate_msg_id()

        msg = public.encode_transfer_msg(self.gui_id,
                                         self.main_window.gui_id,
                                         task_id,
                                         msg_id,
                                         data)
        self.send_msg(msg)

    def send_msg(self, content=None):
        """发送数据"""
        try:
            print('device management ' + self.gui_id + " 发送数据：")
            print(content)
            print()
            if self.main_window.buffer_read:
                self.main_window.buffer_read.write(content)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + 'send_msg')
            self.show_data_to_text(error_msg)

    def gui_exit(self):
        """退出"""
        """关闭窗口事件"""
        try:
            pass
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, error_msg_prefix + "gui_exit")
            print(error_msg)
        self.exited = True

    def show_data_to_text(self, content=None, additional_msg=''):
        """显示数据"""
        print(content)
        print(additional_msg)


class SvgBackground(QSvgWidget):
    signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.select_rect = None

    def mousePressEvent(self, e):
        self.select_rect = (e.x(), e.y(), 0, 0)
        self.signal.emit({'background_mousePressEvent': None})

        # print('background_mousePressEvent: ' + str(e.x()) + ', ' + str(e.y()) + '\n')

    def mouseMoveEvent(self, e):
        start_x, start_y = self.select_rect[0:2]
        self.select_rect = (start_x, start_y, e.x() - start_x, e.y() - start_y)
        self.update()

    def mouseReleaseEvent(self, event):
        """按钮释放"""
        self.select_rect = (event.x(), event.y(), 0, 0)
        self.update()

    def paintEvent(self, event):
        """重写绘制函数"""
        # 初始化绘图工具
        qp = QPainter()
        # 开始在窗口绘制
        qp.begin(self)
        # 自定义画点方法
        if self.select_rect:
            self.draw_rect(qp)
        # 结束在窗口的绘制
        qp.end()

    def draw_rect(self, qp):
        # 创建红色，宽度为4像素的画笔
        pen = QPen(Qt.blue, 1)
        qp.setPen(pen)
        qp.drawRect(*self.select_rect)
        # print(self.select_rect)
        if abs(self.select_rect[2]) > 5 and abs(self.select_rect[3]) > 5 or \
                abs(self.select_rect[2]) * abs(self.select_rect[3]) > 25:
            x0, y0 = self.select_rect[0:2]
            x1 = x0 + self.select_rect[2]
            y1 = y0 + self.select_rect[3]
            if x1 < x0:
                temp = x1
                x1 = x0
                x0 = temp
            if y1 < y0:
                temp = y1
                y1 = y0
                y0 = temp
            self.signal.emit({'background_select': {'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1}})
            # print({'background_select': {'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1}})


class SvgDevice(QSvgWidget):
    signal = pyqtSignal(dict)
    lib_path = ''

    def __init__(self, parent=None, host_info=None,
                 is_connected=False, device_type='unknown', device_no='unknown', project_name=''):
        super().__init__(parent)

        self.iniDragCor = [0, 0]
        self.center_x = 0
        self.center_y = 0

        # 设备在设备树的控件
        self.tree_item = None
        self.device_online_icon = None
        self.device_offline_icon = None

        if tools_common.check_file_exist(self.lib_path, 'device.svg'):
            self.svg_root = etree.parse(os.path.join(self.lib_path, 'device.svg'))
            self.svg_device = etree.ETXPath("//{http://www.w3.org/2000/svg}polygon[@id='device_device']")
            self.svg_circle = etree.ETXPath("//{http://www.w3.org/2000/svg}circle[@id='device_circle']")
            self.svg_type = etree.ETXPath("//{http://www.w3.org/2000/svg}text[@id='device_type']")
            self.svg_no = etree.ETXPath("//{http://www.w3.org/2000/svg}text[@id='device_no']")
            self.svg_ip = etree.ETXPath("//{http://www.w3.org/2000/svg}text[@id='device_ip']")

            self.load(etree.tostring(self.svg_root))

            self.is_connected = is_connected
            self.device_type = device_type
            self.device_no = device_no
            self.device_ip = host_info['host']
            self.net_name = host_info['net_name']
            self.project_name = project_name

            self.set_connected_state()
            self.set_clicked_state(False)
            self.set_selected_state(False)
            self.set_device_type()
            self.set_device_no()
            self.set_device_ip()

    def mousePressEvent(self, e):
        """点击事件"""
        self.iniDragCor[0] = e.x()
        self.iniDragCor[1] = e.y()
        # print('mousePressEvent: ' + str(self.iniDragCor) + '\n')

        self.set_clicked_state(True)
        self.signal.emit({'mousePressEvent': self.device_ip})

    def mouseMoveEvent(self, e):
        """移动事件"""
        x = e.x() - self.iniDragCor[0]
        y = e.y() - self.iniDragCor[1]

        cor = QPoint(x, y)
        # 需要maptoparent一下才可以的,否则只是相对位置。
        new_start = self.mapToParent(cor)
        # self.move(self.mapToParent(cor))
        self.move(new_start)
        self.center_x = int(new_start.x() + self.size().width() / 2)
        self.center_y = int(new_start.y() + self.size().height() / 2)

    def mouseReleaseEvent(self, e):
        """鼠标按钮释放事件"""
        # self.set_clicked_state(False)

    def set_connected_state(self):
        """改变路由器的颜色"""
        try:
            if self.is_connected:
                self.svg_device(self.svg_root)[0].attrib['fill'] = 'rgb(199,7,24)'
                if self.device_online_icon and self.tree_item:
                    self.tree_item.setIcon(0, self.device_online_icon)
            else:
                self.svg_device(self.svg_root)[0].attrib['fill'] = 'rgb(128,128,128)'
                if self.device_offline_icon and self.tree_item:
                    self.tree_item.setIcon(0, self.device_offline_icon)
            self.load(etree.tostring(self.svg_root))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'set_connected_state')
            print(error_msg)

    def set_clicked_state(self, is_clicked=False):
        """设置左键点击的颜色"""
        try:
            if is_clicked:
                self.svg_device(self.svg_root)[0].attrib['stroke'] = 'rgb(0,0,128)'
            else:
                self.svg_device(self.svg_root)[0].attrib['stroke'] = 'none'

            self.load(etree.tostring(self.svg_root))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'set_clicked_state')
            print(error_msg)

    def set_selected_state(self, is_selected=False):
        """设置在设备列表点击的颜色"""
        try:
            if is_selected:
                self.svg_circle(self.svg_root)[0].attrib['stroke'] = 'rgb(0,0,255)'
            else:
                self.svg_circle(self.svg_root)[0].attrib['stroke'] = 'none'

            self.load(etree.tostring(self.svg_root))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'set_selected_state')
            print(error_msg)

    def set_device_type(self):
        """设置文本"""
        try:
            self.svg_type(self.svg_root)[0].text = self.device_type
            x = tools_common.get_text_x(self.device_type)
            self.svg_type(self.svg_root)[0].attrib['x'] = str(x)
            self.load(etree.tostring(self.svg_root))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'set_device_type')
            print(error_msg)

    def set_device_no(self):
        """设置文本"""
        try:
            self.svg_no(self.svg_root)[0].text = self.device_no
            x = tools_common.get_text_x(self.device_no)
            self.svg_no(self.svg_root)[0].attrib['x'] = str(x)
            self.load(etree.tostring(self.svg_root))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'set_device_no')
            print(error_msg)

    def set_device_ip(self):
        """设置文本"""
        try:
            self.svg_ip(self.svg_root)[0].text = self.device_ip
            x = tools_common.get_text_x(self.device_ip)
            self.svg_ip(self.svg_root)[0].attrib['x'] = str(x)
            self.load(etree.tostring(self.svg_root))
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'set_device_ip')
            print(error_msg)

    def get_device_center(self):
        """计算设备的中点"""
        return int(self.x() + self.size().width() / 2), int(self.y() + self.size().height() / 2)

    def delete(self):
        """删除"""
        # print('delete_device')
        try:
            if isinstance(self.tree_item, QTreeWidgetItem):
                tree_item = self.tree_item
                parent_item = tree_item.parent()
                parent_item.removeChild(tree_item)
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'delete: tree_item')
            print(error_msg)
        try:
            self.close()
        except Exception as e:
            error_msg = tools_common.get_error_msg(e.args, 'delete: close')
            print(error_msg)
