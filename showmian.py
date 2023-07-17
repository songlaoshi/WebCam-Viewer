# !/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import requests
import cv2
import numpy as np
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mainform import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage, QPen,QBrush, QPolygon, QPolygonF, QColor, QPainter, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, QPointF, QRect


# 设置全局变量
WIDTH_ORI , HEIGHT_ORI= 1296, 960 
WIDTH, HEIGHT = 451, 391
WIDTH_GCC, HEIGHT_GCC = 851, 200
# 字体
fontdict = {'family':'Times New Roman', 'size':10}


class My_Application(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        ################# show image ####################
        ##### phenocam01
        self.image_url1 = "http://192.168.0.103//netcam.jpg"
        self.label_image1 = QLabel(self)
        self.label_image1.setAlignment(Qt.AlignCenter)
        self.label_gcc1 = QLabel(self)
        self.label_gcc1.setAlignment(Qt.AlignCenter)
        self.gcc_values1 = []  # 用于保存计算得到的GCC值
        self.time_points1 = []  # 用于保存时间点
        self.roi_1 = np.array([[135, 505],[295, 495],[298, 555],[115, 581]]) # roi range
        ##### phenocam02
        self.image_url2 = "http://192.168.0.103//netcam.jpg"
        self.label_image2 = QLabel(self)
        self.label_image2.setAlignment(Qt.AlignCenter)
        self.label_gcc2 = QLabel(self)
        self.label_gcc2.setAlignment(Qt.AlignCenter)
        self.gcc_values2 = []  # 用于保存计算得到的GCC值
        self.time_points2 = []  # 用于保存时间点
        self.roi_2 = np.array([[135, 505],[295, 495],[298, 555],[115, 581]]) # roi range
        ##### phenocam03
        self.image_url3 = "http://192.168.0.103//netcam.jpg"
        self.label_image3 = QLabel(self)
        self.label_image3.setAlignment(Qt.AlignCenter)
        self.label_gcc3 = QLabel(self)
        self.label_gcc3.setAlignment(Qt.AlignCenter)
        self.gcc_values3 = []  # 用于保存计算得到的GCC值
        self.time_points3 = []  # 用于保存时间点
        self.roi_3 = np.array([[135, 505],[295, 495],[298, 555],[115, 581]]) # roi range
        ##### phenocam04
        self.image_url4 = "http://192.168.0.103//netcam.jpg"
        self.label_image4 = QLabel(self)
        self.label_image4.setAlignment(Qt.AlignCenter)
        self.label_gcc4 = QLabel(self)
        self.label_gcc4.setAlignment(Qt.AlignCenter)
        self.gcc_values4 = []  # 用于保存计算得到的GCC值
        self.time_points4 = []  # 用于保存时间点
        self.roi_4 = np.array([[135, 505],[295, 495],[298, 555],[115, 581]]) # roi range
        ##### to groups
        self.urls = [self.image_url1,self.image_url2,self.image_url3,self.image_url4]
        self.label_images = [self.ui.label_image1,self.ui.label_image2,self.ui.label_image3,self.ui.label_image4]
        self.label_gccs = [self.ui.label_gcc1,self.ui.label_gcc2,self.ui.label_gcc3,self.ui.label_gcc4]
        self.gcc_values =[self.gcc_values1,self.gcc_values2,self.gcc_values3,self.gcc_values4]
        self.time_points = [self.time_points1,self.time_points2,self.time_points3,self.time_points4]
        self.rois = [self.roi_1,self.roi_2,self.roi_3,self.roi_4]

        # 计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1000)  # 设置定时器间隔为1秒

        self.update_image()  # 首次加载图片

    def update_image(self):
        doy = self.getDoy()
        self.show_image_gcc(0, doy)
        self.show_image_gcc(1, doy)
        self.show_image_gcc(2, doy)
        self.show_image_gcc(3, doy)

    def show_image_gcc(self, num, doy):
        try:
            response = requests.get(self.urls[num])
            if response.status_code == 200:
                image = QPixmap()
                image.loadFromData(response.content)
                # 获取当前时间
                # doy = self.getDoy()
                # 绘制原始图像
                scaled_image = image.scaled(WIDTH, HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # 在图像上绘制ROI图层
                painter = QPainter(scaled_image)
                painter.setPen(QPen(Qt.red, 2))  # 设置画笔颜色和宽度
                roi_points, layer_points = self.roiCorTransf(self.rois[num])
                polygon = QPolygon(layer_points)
                painter.drawPolygon(polygon)
                painter.end()
                self.label_images[num].setPixmap(scaled_image)
                # 使用OpenCV加载图像并转换为NumPy数组
                numpy_image = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), -1)
                roi = self.get_roi_from_image(numpy_image, roi_points)
                gcc_result = self.calculate_gcc(roi)
                # 添加新的GCC值和时间点到列表中
                self.gcc_values[num].append(gcc_result)
                self.time_points[num].append(doy)
                # 将GCC折线图转换为QPixmap并显示在gcc_label上
                gcc_image = self.display_gcc_plot(num)
                self.label_gccs[num].setPixmap(gcc_image)
            else:
                print("Failed to fetch image. Status code:", response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error:", e)

    def getDoy(self):
        datetime_now = datetime.datetime.now()
        time_now = (datetime_now.strftime('%H:%M:%S')).split(":")
        doy_h = (int(time_now[0])+int(time_now[1])/60+int(time_now[2])/3600)/24
        doy_d = datetime_now.timetuple().tm_yday
        return doy_h#doy_d+doy_h

    def get_roi_from_image(self, image, points):
        # 创建掩码图像
        mask = np.zeros_like(image, dtype=np.uint8)
        roi_points = np.array([[point.x(), point.y()] for point in points], np.int32)
        roi_points = roi_points.reshape((-1, 1, 2))
        cv2.fillPoly(mask, [roi_points], (255, 255, 255))

        # 应用掩码
        roi = cv2.bitwise_and(image, mask)
        return roi
    
    def roiCorTransf(self, roi):
        roi_points, layer_points = [], []
        for i in range(len(roi)):
            roi_points.append(QPoint(roi[i,0],roi[i,1]))
            layer_points.append(QPoint(int(roi[i,0]/WIDTH_ORI*WIDTH),int(roi[i,1]/HEIGHT_ORI*HEIGHT)))
        return roi_points, layer_points
    
    def calculate_gcc(self, image):
        # 在这里实现计算GCC的代码
        r,g,b = np.sum(image[:,:,0]),np.sum(image[:,:,1]),np.sum(image[:,:,2])
        return g/(r+g+b)

    def display_gcc_plot(self, num):
        # 将GCC折线图显示在gcc_label上
        fig, ax = plt.subplots(figsize=[WIDTH_GCC/100, HEIGHT_GCC/100])
        plt.plot(self.time_points[num], self.gcc_values[num],color='g', marker='.', linestyle='-',label='GCC')
        # plt.xlabel('Time', **fontdict)
        # plt.ylabel('GCC Value',**fontdict)
        # plt.ticklabel_format(style='plain') # 不用科学计数法
        plt.title('GCC Variation Over Time',**fontdict)

        plt.rcParams['xtick.direction'] = 'in'
        plt.rcParams['ytick.direction'] = 'in'
        plt.tick_params(labelsize=10)
        labels = ax.get_xticklabels() + ax.get_yticklabels()
        [label.set_fontname('Times New Roman') for label in labels]

        # plt.xticks(fontproperties = "Times New Roman", size = 10)
        # plt.yticks(fontproperties = "Times New Roman", size = 10)
        plt.ylim([0,0.5])
        plt.grid(linestyle="--")
        plt.legend(prop=fontdict ,loc=1)
        # Ensure the plot fills the entire figure
        fig.tight_layout()

        # 将matplotlib的图表转换为QPixmap并显示在gcc_label上
        canvas = FigureCanvas(fig)
        canvas.draw()
        image = QImage(canvas.buffer_rgba(), canvas.width(), canvas.height(), QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)
        return pixmap

def main():
    app = QApplication(sys.argv)
    my_window = My_Application()
    my_window.setWindowTitle("Webimage Viewer")
    my_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()