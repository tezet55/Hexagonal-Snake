from PySide2.QtGui import QPixmap, QImage
from PySide2 import QtCore
from PySide2.QtWidgets import *
import numpy as np
import random

class Board(QGraphicsScene):
    def __init__(self, width, height, a):
        super().__init__()
        self.setSceneRect(0, 0, width, height)
        # hexagon side length
        self.a = a
        self.mainShape = (height, width)
        # radius of a circumcircle and inscribed circle on hexagon
        self.verticalA = a
        self.horizontalA = a * np.sqrt(3) / 2
        # size of hexagon net
        self.height = int((height - self.verticalA//2)/(self.verticalA * 2 - self.horizontalA / 2))
        self.width = int((width-(self.height - 1) * self.horizontalA) / (2 * self.horizontalA))
        self.boardShape = (self.height - 1, self.width - 1)
        # create main map for game
        self.makeMap()
        # load border img
        self.borderImg = QPixmap(QImage(":hexagon.png").rgbSwapped())
        # create apple item
        self.appleImg = QPixmap(QImage(":Apple.png"))
        self.appleImg = self.appleImg.scaled(self.horizontalA * 2, self.verticalA * 2)
        self.apple = QGraphicsPixmapItem()
        self.makeApple()
        self.addItem(self.apple)
        self.draw()

    def makeMap(self):
        """
        Create main game map with borders
        """
        self.map = np.zeros((self.boardShape[1]+1, self.boardShape[0]+1))
        for i in range(self.map.shape[1]):
            self.map[0, i] = 1
            self.map[-1, i] = 1
        for j in range(self.map.shape[0]):
            self.map[j, 0] = 1
            self.map[j, -1] = 1

    def setValues(self, width, height):
        """
        Radius of a circumcircle and inscribed circle after window resize
        """
        self.verticalA = self.a * height // self.mainShape[0]
        self.horizontalA = self.a * np.sqrt(3) / 2 * width // self.mainShape[1]

    def draw(self):
        """
        Draw map with border and apple on screen
        """
        borderImg = self.borderImg.scaled(self.horizontalA * 2, self.verticalA * 2)
        self.borderImages = []
        for i in range(self.width):
            for j in range(self.height):
                if i == 0 or i == self.width - 1 or j == 0 or j == self.height - 1:
                    border = QGraphicsPixmapItem()
                    border.setPixmap(borderImg)
                    y, x = self.getAcctualPosition([i, j])
                    border.setPos(QtCore.QPointF(y, x))
                    self.addItem(border)
                    self.borderImages.append(border)
        y, x = self.getAcctualPosition(self.applePos)
        self.apple.setPos(y, x)
        appleImg = self.appleImg.scaled(self.horizontalA * 2, self.verticalA * 2)
        self.apple.setPixmap(appleImg)

    def getAcctualPosition(self, pos):
        """
        Mappint points for actual position on screen
        """
        return (int(pos[0] * self.horizontalA * 2 + pos[1] * self.horizontalA),
                    int(pos[1] * (self.verticalA * 2 - self.horizontalA / 2)))

    def makeApple(self):
        """
        Get new position for apple
        """
        pos = [random.randint(1, self.boardShape[1] - 1), random.randint(1, self.boardShape[0] - 1)]
        while self.map[pos[0], pos[1]] != 0:
            pos = [random.randint(1, self.boardShape[1] - 1), random.randint(1, self.boardShape[0] - 1)]
        self.map[pos[0], pos[1]] = -1
        self.applePos = pos
        y, x = self.getAcctualPosition(self.applePos)
        self.apple.setPos(y, x)

    def updateApplePos(self, pos):
        """
        Update apple position for multiplayer an replay
        """
        self.map[self.applePos[0], self.applePos[1]] = 0
        self.map[pos[0], pos[1]] = -1
        self.applePos = pos
        y, x = self.getAcctualPosition(self.applePos)
        self.apple.setPos(y, x)