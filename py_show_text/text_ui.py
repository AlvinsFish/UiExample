# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'text_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(759, 428)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(10)
        Form.setFont(font)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(20, 407, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)
        self.show_text = QtWidgets.QTextBrowser(Form)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.show_text.setFont(font)
        self.show_text.setObjectName("show_text")
        self.verticalLayout.addWidget(self.show_text)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.groupBox = QtWidgets.QGroupBox(Form)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem3)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.display_convert_checkbox = QtWidgets.QCheckBox(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.display_convert_checkbox.setFont(font)
        self.display_convert_checkbox.setObjectName("display_convert_checkbox")
        self.gridLayout_2.addWidget(self.display_convert_checkbox, 1, 0, 1, 1)
        self.display_enable_checkbox = QtWidgets.QCheckBox(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.display_enable_checkbox.setFont(font)
        self.display_enable_checkbox.setObjectName("display_enable_checkbox")
        self.gridLayout_2.addWidget(self.display_enable_checkbox, 0, 0, 1, 1)
        self.display_oversize_save_checkbox = QtWidgets.QCheckBox(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.display_oversize_save_checkbox.setFont(font)
        self.display_oversize_save_checkbox.setObjectName("display_oversize_save_checkbox")
        self.gridLayout_2.addWidget(self.display_oversize_save_checkbox, 2, 0, 1, 1)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_7)
        self.display_oversize_edit = QtWidgets.QLineEdit(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.display_oversize_edit.setFont(font)
        self.display_oversize_edit.setObjectName("display_oversize_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.display_oversize_edit)
        self.gridLayout_2.addLayout(self.formLayout, 2, 1, 1, 1)
        self.display_multi_checkbox = QtWidgets.QCheckBox(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.display_multi_checkbox.setFont(font)
        self.display_multi_checkbox.setObjectName("display_multi_checkbox")
        self.gridLayout_2.addWidget(self.display_multi_checkbox, 1, 1, 1, 1)
        self.display_time_checkbox = QtWidgets.QCheckBox(self.groupBox)
        self.display_time_checkbox.setObjectName("display_time_checkbox")
        self.gridLayout_2.addWidget(self.display_time_checkbox, 0, 1, 1, 1)
        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_2)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem4)
        self.confirm_btn = QtWidgets.QPushButton(self.groupBox)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.confirm_btn.setFont(font)
        self.confirm_btn.setObjectName("confirm_btn")
        self.verticalLayout_3.addWidget(self.confirm_btn)
        self.verticalLayout_4.addLayout(self.verticalLayout_3)
        self.horizontalLayout.addWidget(self.groupBox)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout.addItem(spacerItem5)
        self.groupBox_2 = QtWidgets.QGroupBox(Form)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.text_edit = QtWidgets.QTextEdit(self.groupBox_2)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.text_edit.setFont(font)
        self.text_edit.setObjectName("text_edit")
        self.verticalLayout_2.addWidget(self.text_edit)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.clear_btn = QtWidgets.QPushButton(self.groupBox_2)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.clear_btn.setFont(font)
        self.clear_btn.setObjectName("clear_btn")
        self.horizontalLayout_2.addWidget(self.clear_btn)
        self.send_btn = QtWidgets.QPushButton(self.groupBox_2)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.send_btn.setFont(font)
        self.send_btn.setObjectName("send_btn")
        self.horizontalLayout_2.addWidget(self.send_btn)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout_5.addLayout(self.verticalLayout_2)
        self.horizontalLayout.addWidget(self.groupBox_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        spacerItem6 = QtWidgets.QSpacerItem(20, 407, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout_3.addItem(spacerItem6)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Text显示"))
        self.groupBox.setTitle(_translate("Form", "显示设置"))
        self.display_convert_checkbox.setText(_translate("Form", "读时转换"))
        self.display_enable_checkbox.setText(_translate("Form", "使能显示"))
        self.display_oversize_save_checkbox.setText(_translate("Form", "超限保存"))
        self.label_7.setText(_translate("Form", "超限长度："))
        self.display_multi_checkbox.setText(_translate("Form", "批量显示"))
        self.display_time_checkbox.setText(_translate("Form", "显示时间"))
        self.confirm_btn.setText(_translate("Form", "确认"))
        self.groupBox_2.setTitle(_translate("Form", "用户输入"))
        self.clear_btn.setText(_translate("Form", "清空显示"))
        self.send_btn.setText(_translate("Form", "发送"))