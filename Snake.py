from Board import *

class Snake(QGraphicsItem):
    def __init__(self, board:Board, playerId=1):
        self.id = playerId

        # get correct img
        if self.id == 1:
            self.headImg = QPixmap(QImage(":SnakeHead.png").scaled(board.horizontalA * 2, board.verticalA * 2))
        elif self.id == 2:
            self.headImg = QPixmap(QImage(":SnakeHead2.png").scaled(board.horizontalA * 2, board.verticalA * 2))

        if self.id == 1:
            self.bodyImg = QPixmap(QImage(":Snake.png").scaled(board.horizontalA * 2, board.verticalA * 2))
        elif self.id == 2:
            self.bodyImg = QPixmap(QImage(":Snake2.png").scaled(board.horizontalA * 2, board.verticalA * 2))
        # get starting position
        if self.id == 1:
            self.snakeBody = [np.array([1, 1])]
            self.dir = 4
            self.lastDir = 4
        else:
            self.snakeBody = [np.array([board.boardShape[1] - 1, board.boardShape[0] - 1])]
            self.dir = 3
            self.lastDir = 3
        # create head item
        self.snakeHead = QGraphicsPixmapItem()
        y, x = board.getAcctualPosition(self.snakeBody[-1])
        self.snakeHead.setPos(y, x)
        self.snakeHead.setPixmap(self.headImg)
        board.addItem(self.snakeHead)
        self.snakeBodyItems = []
        self.score = 0
        self.inGame = True

    def control(self, key, multi):
        """
        Translate pressed key into next snakes moving direction
        """
        if (key == "'q'" and (self.id == 1 or multi) or key == "'i'" and self.id == 2) and self.lastDir != 6:
            self.dir = 1
        elif (key == "'w'" and (self.id == 1 or multi) or key == "'o'" and self.id == 2) and self.lastDir != 5:
            self.dir = 2
        elif (key == "'a'" and (self.id == 1 or multi) or key == "'k'" and self.id == 2) and self.lastDir != 4:
            self.dir = 3
        elif (key == "'s'" and (self.id == 1 or multi) or key == "'l'" and self.id == 2) and self.lastDir != 3:
            self.dir = 4
        elif (key == "'z'" and (self.id == 1 or multi) or key == "','" and self.id == 2) and self.lastDir != 2:
            self.dir = 5
        elif (key == "'x'" and (self.id == 1 or multi) or key == "'.'" and self.id == 2) and self.lastDir != 1:
            self.dir = 6

    def move(self, board:Board):
        """
        Move snake
        """
        # add new position of snakes head
        if self.dir == 1:
            self.snakeBody.append(self.snakeBody[-1] - [0, 1])
        elif self.dir == 2:
            self.snakeBody.append(self.snakeBody[-1] - [-1, 1])
        elif self.dir == 3:
            self.snakeBody.append(self.snakeBody[-1] - [1, 0])
        elif self.dir == 4:
            self.snakeBody.append(self.snakeBody[-1] + [1, 0])
        elif self.dir == 5:
            self.snakeBody.append(self.snakeBody[-1] + [-1, 1])
        elif self.dir == 6:
            self.snakeBody.append(self.snakeBody[-1] + [0, 1])
        self.lastDir = self.dir
        # check if snake doesn't hit borders
        if 1 > self.snakeBody[-1][0] or self.snakeBody[-1][0] >= board.boardShape[1] or \
                1 > self.snakeBody[-1][1] or self.snakeBody[-1][1] >= board.boardShape[0]:
            self.destroy(board)
            return
        # check collision
        if board.map[self.snakeBody[-1][0], self.snakeBody[-1][1]] != 0 and board.map[
            self.snakeBody[-1][0], self.snakeBody[-1][1]] != -1:
            self.destroy(board)
            return
        board.map[self.snakeBody[-1][0], self.snakeBody[-1][1]] = 1
        board.map[self.snakeBody[0][0], self.snakeBody[0][1]] = 0
        # check if apple was eaten
        if np.array_equal(self.snakeBody[-1], np.array(board.applePos)):
            board.makeApple()
            self.snakeBody.insert(0, self.snakeBody[0])
            self.snakeBodyItems.append(QGraphicsPixmapItem())
            self.snakeBodyItems[-1].setPixmap(self.bodyImg)
            board.addItem(self.snakeBodyItems[-1])
            self.score += 10
        y, x = board.getAcctualPosition(self.snakeBody[-1])
        self.snakeHead.setPos(y, x)
        self.snakeBody.pop(0)
        # update items position
        for item, bodyPos in zip(self.snakeBodyItems, self.snakeBody[0:-1]):
            y, x = board.getAcctualPosition(bodyPos)
            item.setPos(y,x)

    def destroy(self, board:Board):
        """
        Destroy snake
        """
        # remove items from scene
        board.removeItem(self.snakeHead)
        for item in self.snakeBodyItems:
            board.removeItem(item)
        # remove snake from map
        for pos in self.snakeBody[:-1]:
            board.map[pos[0], pos[1]] = 0
        self.snakeBody.pop(-1)
        self.inGame = False
        self.snakeBody = []

    def updatePos(self, body, board):
        """
        Update snake position for multiplayer and replay
        """
        for pos in self.snakeBody:
            board.map[pos[0], pos[1]] = 0
        # if apple eaten, add new item
        if len(body) > len(self.snakeBody):
            self.snakeBodyItems.append(QGraphicsPixmapItem())
            self.snakeBodyItems[-1].setPixmap(self.bodyImg)
            board.addItem(self.snakeBodyItems[-1])
        # update body
        self.snakeBody = body
        for pos in self.snakeBody:
            board.map[pos[0], pos[1]] = self.id
        y, x = board.getAcctualPosition(self.snakeBody[-1])
        self.snakeHead.setPos(y, x)
        for item, bodyPos in zip(self.snakeBodyItems, self.snakeBody[0:-1]):
            y, x = board.getAcctualPosition(bodyPos)
            item.setPos(y, x)
