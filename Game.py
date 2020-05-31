import time
from DesktopFinal import *
import sys
from pynput import keyboard
import resources
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import json
from Snake import *
from Board import *
from lxml import etree as ET
from tensorflow.keras import Sequential
from tensorflow.keras.layers import InputLayer, Dense, Conv2D, MaxPooling2D, Flatten
from tensorflow.keras.models import load_model
from matplotlib import pyplot as plt
from datetime import datetime

class Game:
    def __init__(self):
        # init GUI
        self.app = QApplication(sys.argv)
        self.win = QMainWindow()
        self.mainWin = Ui_MainWindow()
        self.mainWin.setupUi(self.win)
        self.mainWin.retranslateUi(self.win)
        self.mainWin.pushButton.clicked.connect(self.init1P)
        self.mainWin.pushButton_2.clicked.connect(self.init2P)
        self.mainWin.pushButton_3.clicked.connect(self.initAI)
        self.mainWin.pushButton_4.clicked.connect(self.multi_init)
        self.mainWin.pushButton_5.clicked.connect(self.replay)
        self.mainWin.pushButton_6.clicked.connect(exit)
        self.mainWin.label_4.hide()
        self.mainWin.label_4.setFont(QFont("Arial", 24))
        self.mainWin.label_4.setAlignment(Qt.AlignCenter)
        self.win.show()
        self.done = True
        self.multi = False
        self.view = True
        a = self.mainWin.graphicsView.size().width()//35
        self.board = Board(self.mainWin.graphicsView.size().width()-5,self.mainWin.graphicsView.size().height(), a)
        self.mainWin.graphicsView.setScene(self.board)
        self.name = "Player1"
        self.enemyName = "Player2"
        # read json config file
        with open('config.json') as f:
            self.config = json.load(f)
            msgBox = QMessageBox()
            msgBox.setText(f"JSON config\nip: {self.config['ip']}\nport: {self.config['port']}\nReplay file: {self.config['history']}\n AI model: {self.config['aimodel']}")
            msgBox.exec()
        self.win.show()
        sys.exit(self.app.exec_())

    def multi_init(self):
        """
        Connect to the server and initialize online multiplayer game

        """
        self.multi = True
        # Connect to server
        HOST = self.config["ip"]
        PORT = int(self.config["port"])
        self.BUFSIZ = 1024
        self.ADDR = (HOST, PORT)
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect(self.ADDR)

        # Enter name
        self.name, ok = QInputDialog().getText(self.win, "Name", "Enter your name:", text="Player")
        self.client_socket.send(bytes(f"{self.name};{str(self.board.applePos)}", "utf8"))
        msg = self.client_socket.recv(self.BUFSIZ).decode("utf8")
        # Wait for 2nd player
        while msg != "start":
            self.mainWin.graphicsView.hide()
            self.mainWin.label_4.setText("Waiting for another player...")
            self.mainWin.label_4.show()
            self.win.show()
            self.app.processEvents()
            msg = self.client_socket.recv(self.BUFSIZ).decode("utf8")
        self.mainWin.label_4.hide()
        self.mainWin.graphicsView.show()
        self.win.show()
        self.app.processEvents()
        self.id, self.enemyName, apple = self.client_socket.recv(self.BUFSIZ).decode("utf8").split(";")
        self.board.updateApplePos(json.loads(apple))
        self.mainWin.label_3.setText(self.name)
        self.mainWin.label_2.setText(self.enemyName)
        # Initialize snakes for each player
        if self.id == "1":
            self.mySnake = Snake(self.board, 1)
            self.enemySnake = Snake(self.board, 2)
        else:
            self.mySnake = Snake(self.board, 2)
            self.enemySnake = Snake(self.board, 1)
        self.newEnemyBody = self.enemySnake.snakeBody
        # Create receive threat
        self.receiveThread = Thread(target=self.receive)
        self.receiveThread.start()
        self.win.show()
        self.runMulti()

    def receive(self):
        """
        Receive second players snake state
        """
        while self.multi:
            snakeBody, applePos, score = self.client_socket.recv(self.BUFSIZ).decode("utf8").split(";")
            self.newEnemyBody = [np.array(x) for x in json.loads(snakeBody)]
            applePos = json.loads(applePos)
            if applePos != self.board.applePos:
                self.board.updateApplePos(applePos)
            self.enemySnake.score = int(score)
            self.win.show()

    def on_press(self, key):
        """
        Handle keyboard
        """
        if key == keyboard.Key.esc:
            self.done = True
        else:
            if not self.multi:
                for s in self.snake:
                    s.control(str(key), self.multi)
            else:
                self.mySnake.control(str(key), self.multi)

    def init1P(self):
        """
        Initialize single player game
        """
        # if game wasnt finished, destroy snakes
        if not self.done:
            for s in self.snake:
                if s.inGame: s.destroy(self.board)
            self.board.makeMap()
            self.board.makeApple()
        self.snake = [Snake(self.board, 1)]
        self.run(False)

    def init2P(self):
        """
        Initialize 2 player game
        """
        if not self.done:
            for s in self.snake:
                if s.inGame: s.destroy(self.board)
            self.board.makeMap()
            self.board.makeApple()
        self.snake = [Snake(self.board, 1), Snake(self.board, 2)]
        self.run(True)

    def initAI(self):
        """
        Initialize game with AI enemy
        """
        if not self.done:
            for s in self.snake:
                if s.inGame: s.destroy(self.board)
            self.board.makeMap()
            self.board.makeApple()
        self.snake = [Snake(self.board, 1), Snake(self.board, 2)]
        self.runAI()

    def writeXml(self, i, snakes):
        """
        Write one tour of game to xml file
        :param i: tour number
        :param snakes: list of snakes objects
        :return:
        """
        tour = ET.SubElement(self.xml, 'tour')
        tour.set('id', str(i))
        for s in snakes:
            # write position of every part in snake body
            snake = ET.SubElement(tour, 'snake')
            snake.set('id', str(s.id))
            snake.set('score', str(s.score))
            if s.inGame:
                snake.text = str([x.tolist() for x in s.snakeBody])
            else:
                snake.text = "None"
        # write apple position
        apple = ET.SubElement(tour, 'apple')
        apple.text = str(self.board.applePos)

    @staticmethod
    def getKey(move):
        """
        Translate pressed key for AI
        :param move: chosen move
        """
        if move == 0:
            return "'i'"
        if move == 1:
            return "'o'"
        if move == 2:
            return "'k'"
        if move == 3:
            return "'l'"
        if move == 4:
            return "','"
        if move == 5:
            return "'.'"


    def preprocess(self, snake):
        """
        Preprocess input data for dnn
        """
        # cut 10x10 part of a map with snakes head in the middle
        map = np.zeros((10 + self.board.map.shape[0],10 + self.board.map.shape[1]))
        map[5:5+self.board.map.shape[0], 5:5 + self.board.map.shape[1]] = self.board.map
        headPos = snake.snakeBody[-1]
        out = map[headPos[0] : headPos[0] + 10, headPos[1]: headPos[1] + 10]
        out = np.where(out == -1, 0, out)

        # get direction from snakes head to the apple
        apple = np.zeros(12)
        pos = self.board.getAcctualPosition(self.board.applePos)
        pos2 = self.board.getAcctualPosition(headPos)
        angle = np.arctan2(pos2[0]-pos[0], pos2[1]-pos[1])
        if -np.pi/6+0.1 < angle < np.pi/6-0.1:
            apple[0] = 1
        if np.pi/6-0.1 < angle < np.pi/6+0.1:
            apple[1] = 1
        if np.pi/6+0.1 < angle < 3*np.pi/6-0.1:
            apple[2] = 1
        if 3*np.pi/6-0.1 < angle < 3*np.pi/6+0.1:
            apple[3] = 1
        if 3*np.pi/6+0.1 < angle < 5*np.pi/6-0.1:
            apple[4] = 1
        if 5*np.pi/6-0.1 < angle < 5*np.pi/6+0.1:
            apple[5] = 1
        if 5*np.pi/6+0.1 < angle and angle < -5*np.pi/6+0.1:
            apple[6] = 1
        if -5*np.pi/6-0.1 < angle < -5*np.pi/6+0.1:
            apple[7] = 1
        if -5*np.pi/6+0.1 < angle < -3*np.pi/6-0.1:
            apple[8] = 1
        if -3*np.pi/6-0.1 < angle < -3*np.pi/6+0.1:
            apple[9] = 1
        if -3*np.pi/6+0.1 < angle < -np.pi/6-0.1:
            apple[10] = 1
        if -np.pi/6-0.1 < angle < -np.pi/6+0.1:
            apple[11] = 1
        train = np.append(out.reshape(-1),apple)
        return train.reshape((-1,112))

    def create_model(self):
        """
        Create dnn model for DQN learning
        """
        model = Sequential()
        model.add(Dense(64, input_shape=(112,),activation="relu"))
        model.add(Dense(128, activation="relu"))
        model.add(Dense(24, activation="relu"))
        model.add(Dense(6, activation="softmax"))
        model.compile(loss="mse", optimizer="adam")
        return model

    def prepareGame(self):
        # init xml file with game history
        self.xml = ET.Element('Game')
        self.xml.set("name1", self.name)
        self.xml.set("name2", self.enemyName)
        # reset core displays
        self.mainWin.lcdNumber_2.display(0)
        self.mainWin.lcdNumber.display(0)
        # init keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        self.mainWin.label_4.hide()
        self.mainWin.graphicsView.show()
        self.done = False

    def endGame(self):
        # hide game board
        self.mainWin.graphicsView.hide()
        # display game over
        self.mainWin.label_4.setText("Game Over!")
        self.mainWin.label_4.show()
        self.win.show()
        # stop keyboard listener
        self.listener.stop()
        # save history to xml file
        xmlData = ET.tostring(self.xml)
        xmlFile = open(f"history/snake_{datetime.now().strftime('%m%d_%H%M%S')}", "w")
        xmlFile.write(xmlData.decode('utf-8'))

    def runAI(self):
        """
        Game with AI enemy
        """
        self.prepareGame()
        model = load_model(self.config["aimodel"])
        i = 0
        while not self.done:
            self.app.processEvents()
            time.sleep(0.5)
            # move users snake
            if self.snake[0].inGame: self.snake[0].move(self.board)
            # move ai snake
            if self.snake[1].inGame:
                state = self.preprocess(self.snake[1])
                pred = model.predict(state)[0]
                action = np.argmax(pred)
                self.snake[1].control(self.getKey(action), False)
                self.snake[1].move(self.board)
            # check if both snakes are still in game
            if not self.snake[0].inGame and not self.snake[1].inGame:
                self.done = True
            # display score
            if self.snake[0].inGame: self.mainWin.lcdNumber_2.display(self.snake[0].score)
            if self.snake[1].inGame: self.mainWin.lcdNumber.display(self.snake[1].score)
            self.writeXml(i, self.snake)
            self.win.show()
            i += 1
        self.endGame()

    def run(self, is2p=False):
        """
        Singleplayer or hot-seat game
        :param is2p: if game is multiplayer
        """
        self.prepareGame()
        i = 0
        while not self.done:
            self.app.processEvents()
            time.sleep(0.5)
            # move each users snake
            for s in self.snake:
                if s.inGame: s.move(self.board)
            # check if any snake is in game
            if self.snake[0].inGame == False and (not is2p or self.snake[1].inGame == False):
                self.done = True
            # display scores
            if self.snake[0].inGame: self.mainWin.lcdNumber_2.display(self.snake[0].score)
            if is2p and self.snake[1].inGame: self.mainWin.lcdNumber.display(self.snake[1].score)
            self.writeXml(i, self.snake)
            self.win.show()
            i+=1
        self.endGame()

    def runMulti(self):
        self.prepareGame()
        i = 0
        while not self.done:
            self.app.processEvents()
            time.sleep(0.5)
            # move users snake
            if self.mySnake.inGame: self.mySnake.move(self.board)
            # send frame with snake and apple info
            self.client_socket.send(bytes(f"{str([x.tolist() for x in self.mySnake.snakeBody])};{str(self.board.applePos)};{str(self.mySnake.score)}", "utf8"))
            time.sleep(0.2)
            # update enemy snake position
            if self.enemySnake.inGame:
                if not self.newEnemyBody:
                    self.enemySnake.destroy(self.board)
                else:
                    self.enemySnake.updatePos(self.newEnemyBody, self.board)
            # check if any snake still in game
            if not self.mySnake.inGame and not self.enemySnake.inGame:
                self.done = True
            # display score
            if self.mySnake.inGame: self.mainWin.lcdNumber_2.display(self.mySnake.score)
            if self.enemySnake.inGame: self.mainWin.lcdNumber.display(self.enemySnake.score)
            self.writeXml(i, [self.mySnake, self.enemySnake])
            self.win.show()
            i += 1
        self.endGame()
        self.multi = False

    def replay(self):
        """
        Display game replay from xml file
        :return:
        """
        tree = ET.parse(self.config["history"])
        game = tree.getroot()
        # get players names
        self.mainWin.label_3.setText(game.attrib["name1"])
        self.mainWin.label_2.setText(game.attrib["name2"])
        self.snake = []
        # init snakes and apple
        for el in game[0]:
            if el.tag == "snake":
                self.snake.append(Snake(self.board, int(el.attrib["id"])))
            if el.tag == "apple":
                self.board.updateApplePos(json.loads(el.text))
        for tour in game:
            self.app.processEvents()
            self.win.show()
            for el in tour:
                if el.tag == "snake":
                    if el.text != "None":
                        # update snake position
                        newBody = [np.array(x) for x in json.loads(el.text)]
                        self.snake[int(el.attrib["id"]) - 1].updatePos(newBody, self.board)
                        # update snake score
                        self.snake[int(el.attrib["id"]) - 1].score = int(el.attrib["score"])
                        if int(el.attrib["id"]) - 1 == 0:
                            self.mainWin.lcdNumber_2.display(int(el.attrib["score"]))
                        if int(el.attrib["id"]) - 1 == 1:
                            self.mainWin.lcdNumber.display(int(el.attrib["score"]))
                    # destroy snake
                    elif self.snake[int(el.attrib["id"]) - 1].inGame:
                        self.snake[int(el.attrib["id"]) - 1].destroy(self.board)
                # update apple position
                elif el.tag == "apple":
                    self.board.updateApplePos(json.loads(el.text))
            time.sleep(0.5)
        self.mainWin.graphicsView.hide()
        self.mainWin.label_4.setText("End!")
        self.mainWin.label_4.show()
        self.win.show()

    def train(self):
        """
        DQN training
        :return:
        """
        model = self.create_model()
        y = 0.95
        eps = 0.004
        decay_factor = 0.96
        reward = []
        for i in range(10000):
            # save model every 200 turn
            if not i % 200:
                self.view = True
                model.save("model5.h5")
            else:
                self.view = False
            lastSnakeLen = 1
            self.snake = [Snake(self.board, 2)]
            self.board.makeApple()
            self.board.makeMap()
            pos = self.board.getAcctualPosition(self.board.applePos)
            pos2 = self.board.getAcctualPosition(self.snake[0].snakeBody[-1])
            lastDistToApple = np.sqrt(pow(pos[0] - pos2[0], 2) + pow(pos[1] - pos2[1], 2))
            eps *= decay_factor
            eps = max(0.05, eps)
            self.done = False
            while not self.done:
                if self.snake[0].inGame: states = self.preprocess(self.snake[0])
                # predict action
                pred = model.predict(states)[0]
                if np.random.random() < eps:
                    action = np.random.randint(0, 6)
                else:
                    action = np.argmax(pred)
                if self.view:
                    self.app.processEvents()
                    time.sleep(0.2)
                # update snake
                for s in self.snake:
                    if s.inGame:
                        s.control(self.getKey(action), False)
                        s.move(self.board)
                # calculate reward
                r = 0
                if self.snake[0].inGame:
                    pos = self.board.getAcctualPosition(self.board.applePos)
                    pos2 = self.board.getAcctualPosition(self.snake[0].snakeBody[-1])
                    dist = np.sqrt(pow(pos[0] - pos2[0], 2) + pow(pos[1] - pos2[1], 2))
                    # if snake is closer to apple
                    if dist < lastDistToApple:
                        r = 2
                    # if snake is further from apple
                    else:
                        r = -3
                    lastDistToApple = dist
                # if snake ate apple
                if len(self.snake[0].snakeBody) > lastSnakeLen:
                    lastSnakeLen = len(self.snake[0].snakeBody)
                    r = 5
                # if snake hit sth
                if not self.snake[0].inGame:
                    self.done = True
                    r = -8

                newStates = self.preprocess()
                target = r + y * np.max(model.predict(newStates)[0])
                if not self.snake[0].inGame: target = -12
                target_vec = pred
                target_vec[action] = target
                model.fit(states, target_vec.reshape(-1, 6), epochs=1, verbose=0)

                if self.snake[0].inGame: self.mainWin.lcdNumber_2.display(self.snake[0].score)
                if self.view:
                    self.win.show()
            if self.snake[0].inGame: self.snake[0].destroy(self.board)
            print("score", self.snake[0].score, "game nr:", i)
            reward.append(self.snake[0].score)
        model.save("model5.h5")
        plt.plot(range(len(reward)), reward, 'o')
        plt.show()

if __name__ == '__main__':
    Game()