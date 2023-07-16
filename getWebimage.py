import sys
import requests
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QPolygonF
from PyQt5.QtCore import QTimer, Qt, QPoint

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.image_url = "http://192.168.0.103/netcam.jpg"
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.gcc_label = QLabel(self)
        self.gcc_label.setAlignment(Qt.AlignCenter)

        self.gcc_values = []  # 用于存储GCC值的列表

        self.roi_points = [
            QPoint(100, 100),
            QPoint(300, 100),
            QPoint(200, 300),
            QPoint(100, 300),
        ]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(1000)  # 设置定时器间隔为1秒

        self.update_image()  # 首次加载图片

        self.setCentralWidget(QWidget(self))
        layout = QVBoxLayout(self.centralWidget())
        layout.addWidget(self.image_label)
        layout.addWidget(self.gcc_label)

    def update_image(self):
        try:
            response = requests.get(self.image_url)
            if response.status_code == 200:
                data = response.content
                numpy_image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), -1)

                # 计算不规则ROI的GCC
                roi = self.get_roi_from_image(numpy_image, self.roi_points)
                gcc = self.calculate_gcc(roi)

                # 显示原始图像
                image = QPixmap()
                image.loadFromData(data)
                self.image_label.setPixmap(image)

                # 存储GCC值，并绘制折线图
                self.gcc_values.append(gcc)
                self.draw_gcc()

            else:
                print("Failed to fetch image. Status code:", response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error:", e)

    def get_roi_from_image(self, image, points):
        # 创建掩码图像
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        roi_points = np.array([[point.x(), point.y()] for point in points], np.int32)
        cv2.fillPoly(mask, [roi_points], 255)

        # 应用掩码
        roi = cv2.bitwise_and(image, image, mask=mask)
        return roi

    def calculate_gcc(self, image):
        # 在这里实现计算GCC的代码
        # 你可以使用OpenCV和NumPy来处理图像数据
        # 这里只是一个示例，实际计算方法根据你的需求来确定
        return np.mean(np.mean(image, axis=(0, 1)))

    def draw_gcc(self):
        if len(self.gcc_values) >= 2:
            gcc_values_normalized = (self.gcc_values - np.min(self.gcc_values)) / (np.max(self.gcc_values) - np.min(self.gcc_values))
            gcc_values_normalized = np.clip(gcc_values_normalized, 0, 1)

            # 绘制折线图
            plt.clf()
            plt.plot(gcc_values_normalized, color='green')
            plt.xlabel('Time')
            plt.ylabel('GCC Value')
            plt.title('GCC Value over Time')

            # 设置背景颜色为白色
            plt.gca().set_facecolor((1, 1, 1))

            # 获取绘制的图形，并转换为QImage
            fig = plt.gcf()
            fig.canvas.draw()
            width, height = fig.canvas.get_width_height()
            buf = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            buf.shape = (height, width, 3)
            q_image = QImage(buf, width, height, QImage.Format_RGB888)

            # 在QLabel中显示绘制的图形
            pixmap = QPixmap.fromImage(q_image)
            self.gcc_label.setPixmap(pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageViewer()
    window.setWindowTitle("Image Viewer")
    window.show()
    sys.exit(app.exec_())
