from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QDialog

from py_ui import add_ui


class AddDeviceUi(QDialog):
    signal = pyqtSignal(dict)

    def __init__(self):
        QDialog.__init__(self)

        self.win_main = add_ui.Ui_Dialog()
        self.win_main.setupUi(self)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.project_name = ''
        self.net_name = ''

        self._initial()

    def _initial(self):
        """初始化"""
        self.win_main.login_confirm_btn.clicked.connect(self._add_device)
        self.win_main.login_exit_btn.clicked.connect(self.close)

    def display(self):
        """显示界面"""
        self.win_main.login_host_label.setText('')
        self.win_main.login_name_label.setText('')
        self.win_main.login_net_label.setText('')
        self.win_main.login_project_label.setText('')

        self.win_main.login_project_edit.setText(self.project_name)
        self.win_main.login_net_edit.setText(self.net_name)

        self.win_main.login_host_edit.setFocus()

        self.show()

    def _add_device(self):
        """添加设备"""
        self.win_main.login_host_label.setText('')
        # 第一步，获取用户输入，检查是否有误
        host_info = self._get_host_info()

        # 第四步，获取信息，后台操作
        if host_info:
            # 显示提示信息
            self.win_main.login_host_label.setText('添加中')
            self.signal.emit({'add_device': host_info})
        else:
            self.win_main.login_host_label.setText('错误')

    def _get_host_info(self):
        """获取host信息"""
        host_info = {}
        host = self.win_main.login_host_edit.text().strip()
        name = self.win_main.login_name_edit.text().strip()
        net_name = self.win_main.login_net_edit.text().strip()
        project_name = self.win_main.login_project_edit.text().strip()
        if not project_name:
            project_name = '项目1'
        if not net_name:
            net_name = '类别1'
        self.project_name = project_name
        self.net_name = net_name

        if not host:
            self.win_main.login_host_label.setText('错误')

        elif not name:
            self.win_main.login_host_label.setText('')
            self.win_main.login_name_label.setText('错误')

        else:
            self.win_main.login_host_label.setText('')
            self.win_main.login_name_label.setText('')

            host_info['host'] = host
            host_info['name'] = name
            host_info['net_name'] = net_name
            host_info['project_name'] = project_name

        return host_info
