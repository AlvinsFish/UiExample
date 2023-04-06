from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtCore

from py_about import about_ui


class AboutGui(QDialog):

    def __init__(self):
        QDialog.__init__(self)
        self.win_main = about_ui.Ui_Dialog()
        self.win_main.setupUi(self)

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.win_main.show_text.setText("本程序作为示例程序，主要包含：\n1、运用多进程编写界面程序；\n"
                                        "2、进程间的通信方案；\n3、看门狗守护子进程；\n"
                                        "4、数据显示到QTextBrowser；\n\n作者：ycl")
        self.win_main.exit_btn.clicked.connect(self.close)
