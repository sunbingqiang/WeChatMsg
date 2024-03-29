#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2019年7月26日
@author: Irony
@site: https://pyqt5.com https://github.com/892768447
@email: 892768447@qq.com
@file: CustomWidgets.CAvatar
@description: 头像
"""
import os

from PyQt5.QtCore import QUrl, QRectF, Qt, QSize, QTimer, QPropertyAnimation, \
    QPointF, pyqtProperty
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPainterPath, QMovie
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkDiskCache, \
    QNetworkRequest
from PyQt5.QtWidgets import QWidget, qApp

__Author__ = 'Irony'
__Copyright__ = 'Copyright (c) 2019 Irony'
__Version__ = 1.0


class CAvatar(QWidget):
    Circle = 0  # 圆圈
    Rectangle = 1  # 圆角矩形
    SizeLarge = QSize(128, 128)
    SizeMedium = QSize(64, 64)
    SizeSmall = QSize(32, 32)
    StartAngle = 0  # 起始旋转角度
    EndAngle = 360  # 结束旋转角度

    def __init__(self, *args, shape=0, url='', img_bytes=None, cacheDir=False, size=QSize(64, 64), animation=False,
                 **kwargs):
        super(CAvatar, self).__init__(*args, **kwargs)
        self.url = ''
        self._angle = 0  # 角度
        self.pradius = 0  # 加载进度条半径
        self.animation = animation  # 是否使用动画
        self._movie = None  # 动态图
        self._pixmap = QPixmap()  # 图片对象
        self.pixmap = QPixmap()  # 被绘制的对象
        self.isGif = url.endswith('.gif')
        # 进度动画定时器
        self.loadingTimer = QTimer(self, timeout=self.onLoading)
        # 旋转动画
        self.rotateAnimation = QPropertyAnimation(
            self, b'angle', self, loopCount=1)
        self.setShape(shape)
        self.setCacheDir(cacheDir)
        self.setSize(size)
        if img_bytes:
            self.setBytes(img_bytes)


        else:
            self.setUrl(url)

    def paintEvent(self, event):
        super(CAvatar, self).paintEvent(event)
        # 画笔
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        # 绘制
        path = QPainterPath()
        diameter = min(self.width(), self.height())
        if self.shape == self.Circle:
            radius = int(diameter / 2)
        elif self.shape == self.Rectangle:
            radius = 4
        halfW = self.width() / 2
        halfH = self.height() / 2
        painter.translate(halfW, halfH)
        path.addRoundedRect(
            QRectF(-halfW, -halfH, diameter, diameter), radius, radius)
        painter.setClipPath(path)
        # 如果是动画效果
        if self.rotateAnimation.state() == QPropertyAnimation.Running:
            painter.rotate(self._angle)  # 旋转
            painter.drawPixmap(
                QPointF(-self.pixmap.width() / 2, -self.pixmap.height() // 2), self.pixmap)
        else:
            painter.drawPixmap(-int(halfW), -int(halfH), self.pixmap)
        # 如果在加载
        if self.loadingTimer.isActive():
            diameter = 2 * self.pradius
            painter.setBrush(
                QColor(45, 140, 240, int((1 - self.pradius / 10) * 255)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(
                QRectF(-self.pradius, -self.pradius, diameter, diameter), self.pradius, self.pradius)

    def enterEvent(self, event):
        """鼠标进入动画
        :param event:
        """
        if not (self.animation and not self.isGif):
            return
        self.rotateAnimation.stop()
        cv = self.rotateAnimation.currentValue() or self.StartAngle
        self.rotateAnimation.setDuration(
            540 if cv == 0 else int(cv / self.EndAngle * 540))
        self.rotateAnimation.setStartValue(cv)
        self.rotateAnimation.setEndValue(self.EndAngle)
        self.rotateAnimation.start()

    def leaveEvent(self, event):
        """鼠标离开动画
        :param event:
        """
        if not (self.animation and not self.isGif):
            return
        self.rotateAnimation.stop()
        cv = self.rotateAnimation.currentValue() or self.EndAngle
        self.rotateAnimation.setDuration(int(cv / self.EndAngle * 540))
        self.rotateAnimation.setStartValue(cv)
        self.rotateAnimation.setEndValue(self.StartAngle)
        self.rotateAnimation.start()

    def onLoading(self):
        """更新进度动画
        """
        if self.loadingTimer.isActive():
            if self.pradius > 9:
                self.pradius = 0
            self.pradius += 1
        else:
            self.pradius = 0
        self.update()

    def onFinished(self):
        """图片下载完成
        """
        self.loadingTimer.stop()
        self.pradius = 0
        reply = self.sender()

        if self.isGif:
            self._movie = QMovie(reply, b'gif', self)
            if self._movie.isValid():
                self._movie.frameChanged.connect(self._resizeGifPixmap)
                self._movie.start()
        else:
            data = reply.readAll().data()
            reply.deleteLater()
            del reply
            self._pixmap.loadFromData(data)
            if self._pixmap.isNull():
                self._pixmap = QPixmap(self.size())
                self._pixmap.fill(QColor(204, 204, 204))
            self._resizePixmap()

    def onError(self, code):
        """下载出错了
        :param code:
        """
        self._pixmap = QPixmap(self.size())
        self._pixmap.fill(QColor(204, 204, 204))
        self._resizePixmap()

    def refresh(self):
        """强制刷新
        """
        self._get(self.url)

    def isLoading(self):
        """判断是否正在加载
        """
        return self.loadingTimer.isActive()

    def setShape(self, shape):
        """设置形状
        :param shape:        0=圆形, 1=圆角矩形
        """
        self.shape = shape

    def setBytes(self, img_bytes):
        self._pixmap = QPixmap()
        if isinstance(img_bytes, bytes):
            if img_bytes[:4] == b'\x89PNG':
                self._pixmap.loadFromData(img_bytes, format='PNG')
            else:
                self._pixmap.loadFromData(img_bytes, format='jfif')
        elif isinstance(img_bytes, QPixmap):
            self._pixmap = img_bytes
        self._resizePixmap()

    def setUrl(self, url):
        """设置url,可以是本地路径,也可以是网络地址
        :param url:
        """
        return
        self.url = url
        self._get(url)

    def setCacheDir(self, cacheDir=''):
        """设置本地缓存路径
        :param cacheDir:
        """
        self.cacheDir = cacheDir
        self._initNetWork()

    def setSize(self, size):
        """设置固定尺寸
        :param size:
        """
        if not isinstance(size, QSize):
            size = self.SizeMedium
        self.setMinimumSize(size)
        self.setMaximumSize(size)
        self._resizePixmap()

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    def _resizePixmap(self):
        """缩放图片
        """
        if not self._pixmap.isNull():
            self.pixmap = self._pixmap.scaled(
                self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.update()

    def _resizeGifPixmap(self, _):
        """缩放动画图片
        """
        if self._movie:
            self.pixmap = self._movie.currentPixmap().scaled(
                self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.update()

    def _initNetWork(self):
        """初始化异步网络库
        """
        if not hasattr(qApp, '_network'):
            network = QNetworkAccessManager(self.window())
            setattr(qApp, '_network', network)
        # 是否需要设置缓存
        if self.cacheDir and not qApp._network.cache():
            cache = QNetworkDiskCache(self.window())
            cache.setCacheDirectory(self.cacheDir)
            qApp._network.setCache(cache)

    def _get(self, url):
        """设置图片或者请求网络图片
        :param url:
        """
        if not url:
            self.onError('')
            return
        if url.startswith('http') and not self.loadingTimer.isActive():
            url = QUrl(url)
            request = QNetworkRequest(url)
            # request.setHeader(QNetworkRequest.UserAgentHeader, b'CAvatar')
            # request.setRawHeader(b'Author', b'Irony')
            request.setAttribute(
                QNetworkRequest.FollowRedirectsAttribute, True)
            if qApp._network.cache():
                request.setAttribute(
                    QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.PreferNetwork)
                request.setAttribute(
                    QNetworkRequest.CacheSaveControlAttribute, True)
            reply = qApp._network.get(request)
            self.pradius = 0
            self.loadingTimer.start(50)  # 显示进度动画
            reply.finished.connect(self.onFinished)
            reply.error.connect(self.onError)
            return
        self.pradius = 0
        if os.path.exists(url) and os.path.isfile(url):
            if self.isGif:
                self._movie = QMovie(url, parent=self)
                if self._movie.isValid():
                    self._movie.frameChanged.connect(self._resizeGifPixmap)
                    self._movie.start()
            else:
                self._pixmap = QPixmap(url)
                self._resizePixmap()
        else:
            self.onError('')


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = CAvatar(
        img_bytes=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x84\x00\x00\x00\x84\x08\x00\x00\x00\x00t/\xdc{\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00 cHRM\x00\x00z&\x00\x00\x80\x84\x00\x00\xfa\x00\x00\x00\x80\xe8\x00\x00u0\x00\x00\xea`\x00\x00:\x98\x00\x00\x17p\x9c\xbaQ<\x00\x00\x00\x02bKGD\x00\xff\x87\x8f\xcc\xbf\x00\x00\x0e\x8fIDATx\xda\xed\x9b[\x8c]\xd7Y\xc7\xbf\xff\xb7\xd6\xde\xfb\x9c3w\xdf&\xbe\xdf\x9d\xa4\xbe\xc4\x89krmI\xdc\x06\xa5i\xa0$\x95\xa0\x95\x02U\x0bBH(\\\xfa\x80\x10<\xf0\xd6\x07\xfa\x80D\x1e\xa0P\xa2\x02-\xa1)%j\x13\xd2\xe6~O\x9a\xc4J\x9a\xc4\x8e\xeb\xcb8\xf8\x9eq\xec\x8c\xe7~\xf6\xdek}\x7f\x1e\xce\x8c\xc7g<c\x8f\x8dP\x04:K\x9a\x87\xd93k\xed\xdf\xf9\xd6w\xfff0&\x1f\xff\xd2\x8f\x1b\xa0\x05\xd1\x82hA\xb4 Z\x10-\x88\x16D\x0b\xa2\x05\xd1\x82hA\xb4 Z\x10-\x88\x16D\x0b\xe2\xe3\x06hA\\.\x04\xe6\xf0\x1c""\x049\xf5\x90\x14\x10 \x85\x8d\xef.\x05\x02"\x94\xcbZJU\x9b8\x81\x02\x08\x1d\xa9J\x15\x11\xcc\xf0Q\xfc\xecG]&\x81\x88P h\x9c\x00\x8a\x88\xd0DL@\n\x00\x9b;\x04\x84\x00\xe2eb\x14\xe2\x05b\x02\x884d!@C4v\xbe(f\x85\xa0\x88ApY\xf2\x88.\x01HN^(\xa1AT"\x01\x88\x9e\x7f\xe2\xec\xd7\x01\x11\x9a\x9f\x90\xe7\xa5-\x1fI:\x00\x93*a\xe6\xa4\xa4\xa6\x9c\xd0\xceikv\xc5\xa48\x970\x10\x86\te\xe2\xac\xbf9e"\x14\xc6(\x92\xb0b\x89D\x03\x80\x08\x08T\x99i\x11\x01^\x92b\x82%\x08/\xd4\x86\xbd\x11r\xa1\xd5 \x84\xc1\x07"\xee\xdc\xb3ce\xee\xa1\xa6$\xd5$\xab\x7f0\xd0\xb9\x04*\xa22\xa9\xb3s\x81\x88\xe2)4\x99\x80\x9f\xc3\xad\x80b\xa0\xa9\xc5\xf0\xcc\xf3\xd9b\xe6\x95\xe0\x84\xa2F\xb5\xe2\x91\xe7\x97\xfe\xe1\x9a\xc2<\x02\x08a\x93s\x99\xfd:\xdc\x81\xe7\xfb\xe1\xa2\xa9QA\x02\x17e\x10\x08\x84j\xeaC\x91?\xbd\xab\xe2\xe8i".\x98+G\xfaN\x1c\x19\x89\xe2\xactP@\x9bN\x9b\x15\x02\xac}\xeb\x89\x93P\x95\t\xfb\xba\x08D\xe3\xb6,\xd4sG\xab\xf5\xf2\xf03C\x88^D\x85J\x89\xffu\xc4wVM\xc49\x13r\x9a\xdb\x9c\xddD\xd1\xbb\xf5\xdfG\x7f\xcfATJ\xc5\x1cl\x15B\x08\x9f\x1e\xde\xb8\xba\x1b5W\x7f*[\xd2\xbdpu\x1b\x18\xb3\x82\xf9\xeb\x03\\?\xdf\xd2\xa2\xf4<\xdf\xf0/\xe01\xfd\x1d{~\xd8sw%w\x14\xa5\x98^\x84\x82""\x8a\r\xdf\xfc\xce\xf2\xcd\x0b\xdfN+\xe3\x0f\x87\xb8\xee\xbek\xcb\x04\xe3\xb5\xf8\xeeK\xf9\xaaO\xb7\xa7uT\x82*\x85l:\xcd\xfd\xc5,g*\x13\x9cy\x7f\xff\xc2\xe5>:\x05\xe7\xa0\x11\x8d\xaf\x85m\xa1o\xcf\xdb\xc7d(]\xb8\xe2\xc6\x1d\xd7\xd4\x9cYR\x0e~{/v\xdce\x89c\xa4\x93(\x8a\xb9YG\xe9\x87zox\xf9\xe4\xc3\xab\xd6\xa4!\xb1\x8b\xdb\x06H\x81\x18\xc2\x8e\xab\xde\xdd\xd7\x7f\xf4x\xfb\x95_Y0\xbf\xcd\x8fV\x10\x92\xfa\xab\xafiu\xad\xef\xff\xa8\xad\xc3k.N\x8c\xde\xe6\x02\x91X\xfb\xc8\x96\xbb\xef\xef{q%9W\xa7I8qq\xe9\xaa\xba\x7f\xe4\xaf\xd0}CI\xa9w\x94\x92\xe4|M\x92\xc1\x1f\xffp\xa0\\\xbaz\xed-\xcb\x02\xc5I\x9c\x93\x89F\xc9\xdb\xf4\xa6u#oEK"/\xae\x97\x13a\x8aP\xab{\x89\x9ai\x10I\xd2h\xa4\xd7M\xcep\xf0\xe0P\xb1\xf7\x89\x87\xfb\xcdT\xa35\xbd\xf7\x02Q\xb42Z\xe9\xbd\xb3\\e\x19\xa3\x83\\,\x88Lz\xd5<d*\xb44/I+-Q\xf1E\xe5\xd3#\xa3Y]\xdf\xda[\x1d\xd9\xb4\x04f\x829\xea\x84\x88y\xf8\xbb\xb6\xf5V\x0c)\x82\xb9\xa8S/k\xf8\x8e\xa6\x83\x1a\x8f\rYf\xa5\xb7\x93A\xc3\xdb\xfd\x8b6%y\x8a\xd1\x8e\xb1\xc5\xbf\x0b\xe6\xfb\x7f\xe1\xdd\xb5\xf7\\\x91Wcd\xb3f^\x00\x02\x1a\x83\xae\xb2\xd2\xab\x01:\xc10\xf9\xb2Y\x82\tPHQ\xba\x91\x93>\xec\xfa\xe6\xa9E\x7f\xb2\xcd\x19\xd3\xa0\xa5y\xdb\xf7\xd0\x01\xae\xfe\xf2\x1as\x05\xc5ISVq\x81\xeb(\x13\x83\x99\xa51\n`\x93\x12\xa4\xc1\x899\x03g\xf4\x1c\xc1\r?\xb87\xb5\xfdeU\x8f\xc9\xday\xae,3Ww\xce\x87\x03\x7f\xb3/n\xf9\xdaV\x9a+t:\xfd\xec\x1e\x93,\xd5\x99(c\xc6\xd2CCC\x14\xce\xd1D\x83\xe8\xcc1-\xa9\xa3~hl,\xf3y\\w\xe7\x1d\xedCY-\x94\xd5\x10\x8b\x9d\x0f\x1c\xf5\xb7\xfd\xc1<\x12\x92\x80\xd6\x1c\x04fuV\x02OD\x07\x19T\x11\x188q\x1dQ\xd5\x04\xe6\xc1\x99<\x18$\xb4]\xb5\xf2\xe4@\x84\xdf\xf6\xa5\xb5C\xbe\xeaL\xbc!>\xfb\xd0\x01\xd7yko\xae\xa9\x16\x89L\x0b\xa2\x82\xd9\xc6\xd4 \xb32d\x05\x1f\x18\xea\xd9\xbe\x99>LlCd\x1c\x1e\xec\xad\x00\xcef\xda\x86 \xbe\xef\x9f_\tze\xd7\xe9p\xd3\xe7{\x05\x9a\x87\xe7\xff\xb1\xdf\xa5\xd6\xd3\xd9\xbd\xf6\xc6++\x88\xe2%\x9ck\xa3~\xfa\x9b\x01S\x98\x90*c\x99\xaf\x8f<\xf2\x83\xb0\xf9\x97\x95\xa1\xf1\xc9A\xd3\xf2\xfb\x8f\xf7\xddq\xcf\xd5\xa9\x988kd\xb2\x84PI\x15C\x89dt\xc9\x8a\x97\x93\xb0/P\x0f\xad\xee\x8db\x95#\x8f\x7f8?J\xc6\xc1\x93\xaf\xfd\xe4\x86\xdf\\\xee\x94\xe6&\xee\x92\xa2\xc2&\x08\x98\x12A%B`\xa20=\xfe\xd8\x13\xf3v|nY\x14g"0g\xaaq\xffw\xeb\xdd/\x9e\xba\xf7\xc6\x89\x84\xeb\x9c\xfc\x9eP\xf3&\xd9\xce\x9d\x06\xcb\x13\xcf\rW\x88de\xb9\xe8W7V\xbb*\x95\x04\xa3\xfb\x1e~\xe6\xc3\xfb\xd6\xda\x94m@8M\x12\x06(\x9dF:\x13GI\xeb\xbb\xbfs\xb0\xe7\xf77v$\xb9\x06O:3\x04\x05\xaf\x1b\xda\'{~\xb2\xb9\xcdEN\xe6j\x80\x882B\x11\xad|\xf1\xfb\x07T\xb6v\xbdw|\xc1\xe7\xd6\xa9\x14\xd0\xb6\xed\xb7\xb8\xb2f\x92\xc4m\xaf\x1fy\xe7G_\xeb\xd0sL\x94\xc04\xeb(\xb2\xc2\x9bc\x84)\xf3\xddO\xbdT\xbd\xe3\x8b\xf3\x13\xe6ItA\x11|\x84\x037\xfd\xe5\xb1\xbf\xdec;\x87k\xc0\x84;\x07i>\x06u\x8cq\xfc\xcd\x9f\xf6\xf5\xa7\xba\xed\x8f\x16\xbe;\xb8hSn\xc1%%{\xf2\x98Y\t\x14X\xb4\xdf?\xbf\xf6\xf38\x1b:(Nl\x1aD\x02\xc4$OH\x8d\xbb\xdex\xb2\xbe\xfc\xcb\xd7u0\xba`e\xadT\x8d\x12\x1c(l\x93")RD\xe7\x08C#h0\x00.\x8e\x1f\xdb\xb3\xfb\xb5\x81\xaa\xc0_\xb7H\xb6\x92\xa52\x95 RG\xc5\xe2/\x0e/\x08\xbbv\xb3}\xe0\xe0x\xdb\x94q@8]\'\xdc@\xa5V*a\x07~\xfc\xf6\xc9\xee;\xefXn\xfd\x03\xebU\xd4["\xa7\xdf]\xb1\xba\xf0j \xa3\xf94u\r\xff\xa5\xc2(p&c\xc7\xf7\xee~kt\xacm\xd5\xe9T\xe5\x13\t\xcaX\x89"\xb1D\xd5\x0c6\xbe\xf3?\xde[06d\xc9G\xeboH\xa9\x93NFAk\x86\x10\x8d\xffj7\xadh\x1b\xf9\xf93?\x8f=\xb7\xff\xc6Ro\xc3\x0f\x8c\xfd\xf1\xbc$\xf8\xdc\xeb\xfb\xf7/\xf8\xf35#\x15\x8dZ\x96\x11\xddU\x11\xa3\x8a\xd0\x9c\xe3\x9b\x8f~\x84\xb1#\xa3\x95\x9eUk~e\xe9\xb7\x9e)\xbb\xf2\x07O\xec\xd8\x94\x8b\xa3\xa4\x16\x89\xfc\xf0s\x8f\xf6\xf7\x1c\xae@\xfc\xf2?\xbdR4\xb8Is\x8c\xb1\xa2\xbe\x99!\xa9<\xf7\xea\xfa\xcec\xfbG\xe7\x7f\xea\xfa\rm\x12\xb0\xf7\xf5\rB\xaay\x97\x9f\x1a\xdf\xf7\xd3{ky\xa6(\x8dZ\xf3\x93^\xdbEV\x96\xac\x7f\xeeH\xd1\xb1l\xd5\x96\r+\xab\'NE;\xfd\xf7\x1f\x9c9\xf1\xd5\xf5\xde\xa2\x9a\xa5CG_}\xf9h\xdeY\xaaI\xb2\xe0\xb7\xd6\x01\xe6\xa7,\xd4Yl\x82\xa0\xc8\x17\xd7?\xfdz\xde\xbe\xfc\xfam\xcbj\x96\xd4\xb5xe\xb8\xb7\xad\xf4\x11\xde\x92\x81\x9co~j\xa3D53a\xd5M\xe6:!\xb1\xf1\xc5wo=:x\xc5\xf2\x9ev\'\xe1\xe8\xb1\xb2"\xfb\x1c_\xdd\xb4\xc2\xb2$\x1f;\xbd\xf7\xcd\x83\x83\x03d\x99*C\xf5\x9e\x9b\xb3hv\xd6\xdbR46[Gte\xe7\xcd\xdb\x8f\xd4\x17t\xa5!#\xea\xa9\xbe\xf1\xfa\xf85\xa9DoQR\xa5\x9d8q\x95\x830\x880=\x1b:\xd2zE\xcbl\xf3U\x96\xb0t$\xf6\x9d\xaa\x85\xf2K\xd9\x8bG\x9f\xba9\x7f\xf6\xf8\xf0\xc0\xe9\xd14\xe9\xea9\xed0\xae\xa2\x8b\xcbg\xb6\xcdO\xf4\xac\xc7WFi\x86pTZ\xba\xca\x993\x15\x81\x8f\xe5sG\xe6_i\nz\xcb\x13\x85\x1b?Z8\x15\x94\x14\xd5\xb3\xc9VH\x83x+UIOp\xf4\xa0\x85$Y\x97\xbe\x15O\xed\xb9\xde\x8e\x9c\t\xc9\xc6\r\x1b\x92G\xcf\x98T"]\xdf!\xfd\xb3OM\xa5\xeeT-\x1d\xa79+1\xd0\x91E\xca\xe8$w\xfb_\xaal\xe9\xf4\x88\xce\xe8\x83P\xfdXLJg\x12\'*\xfe\t\xe5\x92F\xb6AB\xa8g\x8e\x88+\xf0\x0fE\x9e\r\xbf\xf3\x85\xaf|\xf6\x0c\xb1\xaa-\xff\xbb}\xc1G\x13\xb8z\xfb\x86\x95\x0eg}\x15\x08\xfa\xb2\xd9D)\x80D\xaf\xb4\xac \xb2\x0f\xbf;\xda~}\x879\xb1\xa4\x9eh`6:f\xd1G\x1d\x8f\x8ej\xaa\xb0\x08B\x04l\x04v\x08\xcc\x1f\xeaW\xbba\xf1cQ\x87\xab\x03\x83m\xeb\xbc9;\xfa\xed\xc7\xb3\xb4\x84\xa8\x8dm\xfc\xf5\xdbj\xa5\x9emR\x10\x94\xc25C4B\x98\xc9\xe8\x07m\xdd\x15\x94/\xec\xd1y\xeb4\x1a\x90\'\xc6U=\x1fU\xbb3\x8a\xa0\x1e`TD\xc5\xf4n\x1a\x95\x87sm\xbf\xed\x97^\x18f\xc5\xf5\x8d\xb5k\x94\x88\xa3\xbbk\x89Q\x1ct\xdeo\x7f2\r\x06L\xe6\x86\xa0x\x86\xe9\xd7A\x80\xe2\xfb\x1e\x1a\xbcv\xf5R{\xb6\xbf\xb2\xf9\n\x1a\x9dDO\xbb\xfa\xb3Ovm\xf0\x14\xf3\xa5\x08\x89F\xf0l\x86\x80\xf0x\xb0x\xfa\xbdz\x18\xaf\xb8b\xb8\xc7\xa7\xac\xcb\x8a\xd5\xa7G\xa5=\x8f\xea\xee\xd8R\xb3\xe8t*\xab1&h\x0e`P\t\xa2\xd4|+\x9f\xfc\x9et\x97\xb1\xd6\xb3\xbd\xdd\x92\x02\x96F\xb0\xfb\xabwe\x0b\x05T\xb3\x02"4\x17\xb5\x11\xc6\xcf5\xf2\xe2X\xe9\x86\xff%=\xb3\xa4\xf3\xc4\x90\r\xfbXH\xac\xcd\xbf\xefo\x0f\xb7\xa7\xfd\xfda\xf1u]#i\xd4\xa9\x9e\n\x9c\x19\x9b!h\x02E)p\xd7,]\xfd\xfc\x81\xc1\xb6|\xde\x92\xb4\xee\xd0hD\x96\xd9R\x88\x98\xa8\xa5\xa6g\x1bR\xcd\x08\x8a\xb1\x0f\xa1\xba\xa0\xb6\xe4\xa6\xe5\xdf\xa8&\x87\xb7\xa83\x89\x95\x15_?\xe1:\xef\x1f@\xe7\x92\x90\xd1\x89\x9e\xcdX\xa3\xea\xf4\xa4F#\x1d\x98E\x1d\x98\xdfqO\xf1^w\xbd}\xe0\x85\xb6\xe5\x05(\xd1\x19\xd4\x94B\x88Z{57j\x9c^\x99QDlt$)z>s\xab.x\xdf\xb4\xb4\xe8\x02\x13\x11\xce\x9f\xe7\x07+ERs \xc4\xa6r\x1aG\x89:\xbd\x02\xf3e\xb0\xc2b\xcfx\xb5\xef\r7\x86\xd1\xfe\x07\xbf\xf1\xbe\x0b\n\x13\x15\xa2\x91>\x98u\xb8\xe8\xb3\xe8\xcb\xc4\xceM4)B\xd1\xfa`\x90+n\\\xb5\xb8+\xb2\x88=\tM\x0c\x02c=D/\xb5\x84"T\xea\xd4\x1e\xea\xb42\xd0`\x89w\x11(\xed\xd8\xbf\xedcm\xdb\'+\xd8\xf5\xc8GY\x107\x95Z#$\x1d\xed\xc2\xae\x00\x15\x9e\xdbjhTi\x83\x92b\xc9Rbx Ij\x8b\x11+\tb\x8c\xaa\xcey\'\xa9\nM\xcek>5{\xcc\x18\x92Rq\xc6\xe7\x87\x1e\xf9\xd9p\xc7=_\x18\xfb\xa7\x97\xf4\x95\x9b\x17E\x7fN\xa9C\xfaR\xa4gm\x12M8\xbd\xa0\xd3\x98\xa4!\xac\xaf\xf9\x0f\x1ey\xb3\xae+\x17\x05\xa3@E\xa20\x86R3\x9d\xb1\xc5\xd0\x04\x11\x90&c\x08?xmtt\xa0\xed\xda_\xdb\xa1\xbd__\xfb\x9f~$:\xb3svk\xfc`\x90\xb5e\x1a\xd0\xe8\x07\x9c#\n\x9a.\xdf\xfaN\xba\xd9\x15\xed\xe9\t\xad\xdd\xd8\x053\nI\x07U\xe7\xac\xa63\xb6g\xa7\xc5\x8e\xa8\x80\xdbpr_\xbef\xfbg\xd6%\xa5u\xde\xb9|dC\xb3\xde\xc0\x99H\x1c\xab\xd7\xbd64\xe5\xdc\x9fA\xba\x7f\xe7)Y\xa9\xec\xba\xbdvp\xc5\xed,\x12\x90\x02%\x85P\xa9\x81\xa4^\x18\x820&!\xbde\xfb{\x83\xcbV\'&i\xa9\xdd\xb7\x8e\xd7\xc6*\xe7\x1a"`\xf3\xdaF\\ThP\xb5f\x131\xc8\x86\xd5E\xad^\xb1ewGICb\x10\x80\x86\x86<2\x87\x8bJB\x90D\xd1\x02\xb5\x1b-\x82N"\x83\xe6\xde &Sb\xa4\xc8\xc2\x8a3\xe7\x83sFLS\n\xd1\\\xdaC\x1aM\xbd\x17q\x9cL\xc6)\x0e!\xebp\x86\x19*\xd8&\xd9 \xc2\xb1\xac$,\xa2(,\x8a\x8395\x1f\xa1r\xb6cD\x8d\xce\x99\xf7\x9c\xa9\xbf\xa2\xa4\xf3\xa2l\xb4\xa2qN^\xaf\x14\xf8\nDf\xa8\xdb\x9aN"\x023\x1f\xc4\xab\xc5(NH\x07\xa7Z\x89q\xaax\x84D\xc4H\xf5\xb34\x91\xe8@B\xed\xbc\x89\x82\x95\xb1\xda6s\xff\xad\tB#,W\xd2\xe8\xb3FAS7Z\x18\xcf\xdc\x94\xd4\xa9\x96\x8e\x97\xd0Tg\xaa\xca\'Z(!:\rM2\x16\x0b\xb9\xfav\xc1E\'?11QS\x80f*F \x05\xa9\x12\x85S\x9b\xe9C=h-\x99\xf13\tH\x8a\xa9\xd0\xa6\xc9\x98\xc5\x88\xf75@f\x18\xba4\xeb\x84\x89\x98\x906YcR\x8ch\x8c\xd1l\nbl\xbcd\xcd\xdb\xcc=7*\xe8Hh\xd3\xd0\x8d\xe0\xf8\x10;\xdb`3\xb5\xa7\xcf;\xa9Y^\x13i\\C\xbf\xd98"\xe8\xa1\x11\xeb\xae\xaa5\xa6~\xcd\x97B\xd8\xe4\xeco\xf2\x84\xc6\x800=U/{:\xa8q.\x10\x17X\xa0\x13\x03J\xd9\x1b\xa4\xbb\x1a\xe6\xb6\x15\x12@\xb8\xc8\x8f\xa2-H8\xd3\xf4\xe9\xd2\x86\xb3&\xa6\x81\xc9\x81\x83.[\x98\xccq.Eq"f\x8eG\x86\xb18\x99\xb9\x1dz\t\x10\x84\xa8+S\x8c<\xdeWV\xd7\xcc\xa5\xdf\xdd\xd8\xe6\n\xa81\xef\xa3\xaeP\\\xea\\\xf4\xbc\x15]\x8c\x9e\x1f>\xfd\xac\xc3\xda\x95\xca\x8b\xb5\xfd\x1b\x0b\x16T\x04\xf8\xb0/\xce[,\x98\xd1\xbb\\\x02\x044z\x1c\x7fl\xd7\xf1q\xb8\x1bz\\\xa0\xcdI\x8c\xae\xac\x14\x86\xf8\xce \x16\xcf\x9b6\xc0\xbe,Id\xa3i\xa5\xd6\xd1\xdb\xbb\xf6\x13;\x1cA77\xad\xa8\x8cV\xeb\xd9\xae\x87$\xb9\xba\xcbh\xfa?\xbc\x0e\x1d\xcf\xd8s\xef@\xe1\xabH\x181G\xcd4&\xca\xa7~tX\x16m\xb3Y&i\x97\x00AT\xc7\x1dc\x97\xc1\x11\x91P\x9b\xd36U\x8e\xa7?;\xbc\xa0\xbeu\xa3\xcd\xa2\xca\x98\xfb\xbf\xdb\xc0\x8a\xaa\x04U"\x84D\x04s\x1b\x1e\x13E\xd5dh$\xef\xaeVl\x96=\x97\x00A\x8d\xde\x08\x81\x01\x86\x99\x1d\xf0\x0c\x82\x08\xe2\x83\x13\xf3\xf5t6A\\\x8a\x9f@\xf4\x91\r\xf7M\x05q\xf1I\xa9\x88H\xd4$x#\xa2\x9f}\xb4z\t\x92\xf8\xdf[\xff\xe7\xfe\xa6\xa6\x05\xd1\x82hA\xb4 Z\x10\x1f\xfbjA\xb4 Z\x10-\x88\x16D\x0b\xa2\x05\xd1\x82\xf8\x7f\x01\xf1\xdf\x91\xd3\xe9`7\x9a\x1c\x88\x00\x00\x00\x12tEXtexif:ExifOffset\x00620\x1a\xa3x\x00\x00\x00\x12tEXtexif:ImageLength\x000\xc1\xc5N\xce\x00\x00\x00\x11tEXtexif:ImageWidth\x000/\xffv\xa0\x00\x00\x00\x12tEXtexif:LightSource\x000x\x05kH\x00\x00\x00\x00IEND\xaeB`\x82'
        ,
        url='https://wx.qlogo.cn/mmhead/ver_1/DpDqmvTDORNWfLrMj26YicorEUREffl1G8FapawdKgINVH9g1icudfWesGrH9LqeGAz16z4PmkW9U1KAIM3btWgozZ1GaLF66bdKdxlMdazmibn2hpFeiaa4613dN6HM4Vfk/132')
    w.show()
    sys.exit(app.exec_())
