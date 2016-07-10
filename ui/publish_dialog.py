# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources/publish_dialog.ui'
#
# Created: Sat Jul  9 13:52:06 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_PublishDialog(object):
    def setupUi(self, PublishDialog):
        PublishDialog.setObjectName("PublishDialog")
        PublishDialog.resize(400, 200)
        PublishDialog.setMinimumSize(QtCore.QSize(400, 200))
        PublishDialog.setMaximumSize(QtCore.QSize(400, 225))
        self.verticalLayout = QtGui.QVBoxLayout(PublishDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.comment_label = QtGui.QLabel(PublishDialog)
        self.comment_label.setEnabled(True)
        self.comment_label.setObjectName("comment_label")
        self.verticalLayout.addWidget(self.comment_label)
        self.publish_comment = QtGui.QTextEdit(PublishDialog)
        self.publish_comment.setObjectName("publish_comment")
        self.verticalLayout.addWidget(self.publish_comment)
        self.result_msg = QtGui.QLabel(PublishDialog)
        self.result_msg.setEnabled(True)
        self.result_msg.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.result_msg.setStyleSheet("")
        self.result_msg.setText("")
        self.result_msg.setTextFormat(QtCore.Qt.PlainText)
        self.result_msg.setAlignment(QtCore.Qt.AlignCenter)
        self.result_msg.setWordWrap(True)
        self.result_msg.setObjectName("result_msg")
        self.verticalLayout.addWidget(self.result_msg)
        self.publish_btn = QtGui.QPushButton(PublishDialog)
        self.publish_btn.setStyleSheet("")
        self.publish_btn.setObjectName("publish_btn")
        self.verticalLayout.addWidget(self.publish_btn)
        self.close_btn = QtGui.QPushButton(PublishDialog)
        self.close_btn.setObjectName("close_btn")
        self.verticalLayout.addWidget(self.close_btn)
        self.info_btn = QtGui.QDialogButtonBox(PublishDialog)
        self.info_btn.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.info_btn.setObjectName("info_btn")
        self.verticalLayout.addWidget(self.info_btn)

        self.retranslateUi(PublishDialog)
        QtCore.QObject.connect(self.publish_btn, QtCore.SIGNAL("clicked()"), self.publish_comment.hide)
        QtCore.QObject.connect(self.publish_btn, QtCore.SIGNAL("clicked()"), self.comment_label.hide)
        QtCore.QObject.connect(self.publish_btn, QtCore.SIGNAL("clicked()"), self.publish_btn.hide)
        QtCore.QObject.connect(self.close_btn, QtCore.SIGNAL("clicked()"), PublishDialog.close)
        QtCore.QObject.connect(self.info_btn, QtCore.SIGNAL("rejected()"), PublishDialog.close)
        QtCore.QMetaObject.connectSlotsByName(PublishDialog)

    def retranslateUi(self, PublishDialog):
        PublishDialog.setWindowTitle(QtGui.QApplication.translate("PublishDialog", "Publish Scene", None, QtGui.QApplication.UnicodeUTF8))
        self.comment_label.setText(QtGui.QApplication.translate("PublishDialog", "What\'s new in this version?", None, QtGui.QApplication.UnicodeUTF8))
        self.publish_comment.setToolTip(QtGui.QApplication.translate("PublishDialog", "<html><head/><body><p>Comment</p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.publish_comment.setHtml(QtGui.QApplication.translate("PublishDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.publish_btn.setText(QtGui.QApplication.translate("PublishDialog", "Publish", None, QtGui.QApplication.UnicodeUTF8))
        self.close_btn.setText(QtGui.QApplication.translate("PublishDialog", "Close", None, QtGui.QApplication.UnicodeUTF8))

