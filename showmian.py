# !/usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys
import requests
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem
# from PyQt5.QtWidgets import QVBoxLayout, QWidget
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage, QPen, QPolygonF, QColor, QPainter, QFont
from PyQt5.QtCore import Qt, QTimer, QPoint, QPointF
from mainform import Ui_MainWindow


class My_Application(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        ################# show image ####################
        ##### phenocam01
        self.image_url = "http://192.168.0.103//netcam.jpg"
        self.ui.graphicsView.setAlignment(Qt.AlignCenter)
        self.scene_image01 = QGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene_image01)
        ##### gcc01
        self.ui.graphicsView_gcc1.setAlignment(Qt.AlignCenter)
        self.scene_gcc01 = QGraphicsScene(self)
        self.ui.graphicsView_gcc1.setScene(self.scene_gcc01)
        # gcc list
        self.gcc_values = []  # 用于存储GCC值的列表
        # roi range
        self.roi_points = [
            QPoint(135, 565),
            QPoint(295, 555),
            QPoint(298, 615),
            QPoint(115, 641),
        ]
        # 计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_iamge01)
        self.timer.start(1000) # 设置定时器时间间隔为1s
        # 首次加载图片
        self.update_iamge01()


    def update_iamge01(self):
        try:
            response = requests.get(self.image_url)
            if response.status_code == 200:
                # 显示原始图像
                image = QPixmap()
                image.loadFromData(response.content)
                self.scene_image01.clear()
                self.scene_image01.addPixmap(image)
                self.ui.graphicsView.fitInView(self.scene_image01.sceneRect(),Qt.KeepAspectRatio)
                # 显示不规则ROI图层
                roi_polygon_item = QGraphicsPolygonItem(QPolygonF(self.roi_points))
                roi_polygon_item.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                roi_polygon_item.setOpacity(0.5)
                self.scene_image01.addItem(roi_polygon_item)
                # 计算gcc
                numpy_image = cv2.imdecode(np.frombuffer(response.content, dtype=np.uint8), -1)
                roi = self.get_roi_from_image(numpy_image, self.roi_points)
                gcc = self.calculate_gcc(roi)
                # 存储GCC值，并绘制折线图
                self.gcc_values.append(gcc)
                self.draw_gcc()
            else:
                print("Failed to fetch image. Status code:", response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error:", e)

    def get_roi_from_image(self, image, points):
        # 创建掩码图像
        mask = np.zeros_like(image, dtype=np.uint8)
        roi_points = np.array([[point.x(), point.y()] for point in points], np.int32)
        roi_points = roi_points.reshape((-1, 1, 2))
        cv2.fillPoly(mask, [roi_points], (255, 255, 255))

        # 应用掩码
        roi = cv2.bitwise_and(image, mask)
        return roi
    
    def calculate_gcc(self, image):
        # 在这里实现计算GCC的代码
        # 你可以使用OpenCV和NumPy来处理图像数据
        # 这里只是一个示例，实际计算方法根据你的需求来确定
        return np.mean(np.mean(image, axis=(0, 1)))
    
    def draw_gcc(self):
        height, width =195, 840 #raw 200,860
        gcc_image = QImage(width, height, QImage.Format_RGBA8888)  # 使用RGBA格式

        if len(self.gcc_values) >= 2:
            gcc_values_normalized = (self.gcc_values - np.min(self.gcc_values)) / (np.max(self.gcc_values) - np.min(self.gcc_values))
            gcc_values_normalized = np.clip(gcc_values_normalized, 0, 1)
            
            # 将gcc_image的所有像素设置为白色
            gcc_image.fill(Qt.white)
            # 绘制gcc_image
            painter = QPainter(gcc_image)

            # 设置折线的画笔颜色为绿色
            pen = QPen(QColor(0, 255, 0))
            pen.setWidth(2)
            painter.setPen(pen)

            # 绘制折线图
            for i in range(1, len(gcc_values_normalized)):
                x1 = (i - 1) * (width - 1) // (len(gcc_values_normalized) - 1)
                y1 = height - int(gcc_values_normalized[i - 1] * (height - 1))
                x2 = i * (width - 1) // (len(gcc_values_normalized) - 1)
                y2 = height - int(gcc_values_normalized[i] * (height - 1))
                painter.drawLine(x1, y1, x2, y2)
            
            # 绘制纵坐标轴刻度和标签
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.setPen(QColor(0, 0, 0))
            painter.drawLine(0, 0, 0, height)
            painter.drawText(0, 10, "1.0")
            painter.drawText(0, height - 10, "0.0")

            # 绘制横坐标轴刻度和标签
            painter.drawLine(0, height-1, width, height-1)
            painter.drawText(width - 30, height - 5, str(len(self.gcc_values)))
            painter.drawText(0, height - 5, "1")

            painter.end()

        # 将numpy数组转换为QImage
        # q_image = QImage(gcc_image.data, width, height, width, QImage.Format_Grayscale8)
        # pixmap = QPixmap.fromImage(q_image)
        pixmap = QPixmap.fromImage(gcc_image)

        self.scene_gcc01.clear()
        self.scene_gcc01.addPixmap(pixmap)

        # self.scene_gcc01.clear()
        # self.scene_gcc01.addPixmap(pixmap)
        # self.ui.graphicsView_gcc1.fitInView(self.scene_gcc01.sceneRect(),Qt.KeepAspectRatio)

def main():
    app = QApplication(sys.argv)
    my_window = My_Application()
    my_window.setWindowTitle("Webimage Viewer")
    my_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()