#!/usr/bin/env python2
import pygame
from pygame.locals import *
from copy import deepcopy
import random
import os.path
import pickle
import sys

from util import window

ML_MODEL_FILENAME = "ml_model.p"

SQUARE_SIZE = 32 # Size of each square on the board
EXTRA_BOTTOM_SPACE = 0
EXTRA_RIGHT_SPACE = 0
PIECE_SPAWN_DELAY = 0
PIECE_FALL_DELAY = 0
PIECE_BORDER_WIDTH = 1
EXTRA_HIDDEN_ROWS = 2


# https://en.wikipedia.org/wiki/Tetris#Colors_of_Tetriminos
# Using the Tetris Company standardization
COLORS = [
    (0,0,0), # Empty square
    (0,255,255), # Line piece (I)
    (0,0,255), # J piece (J)
    (255,165,0), # L piece (L)
    (255,255,0), # Square piece (O)
    (0,255,0), # S piece (S)
    (96, 0, 200), # T piece (T)
    (255,0,0) # Z piece (Z)
]
GRAY = (128,128,128)

PIECES = [
    # I
    {
        "points": [(3,1), (4,1), (5,1), (6,1)],
        "color": 1,
        "origin": (5,1)
    },
    # J
    {
        "points": [(4,0), (5,0), (6,0), (6,1)],
        "color": 2,
        "origin": (5,0)

    },
    # L
    {
        "points": [(4,0), (5,0), (6,0), (4,1)],
        "color": 3,
        "origin": (5,0)
    },
    # O
    {
        "points": [(4,0), (5,0), (4,1), (5,1)],
        "color": 4,
        "origin": (5,0)
    },
    # S
    {
        "points": [(5,0), (6,0), (4,1), (5,1)],
        "color": 5,
        "origin": (5,0)
    },
    # T
    {
        "points": [(4,0), (5,0), (6,0), (5,1)],
        "color": 6,
        "origin": (5,0)
    },
    # Z
    {
        "points": [(4,0), (5,0), (5,1), (6,1)],
        "color": 7,
        "origin": (5,0)
    }
]

class ReinforcementLearner:
    def __init__(self, explorationRate=0.05, learningRate = 0.2, discount = 0.8):
        self.explorationRate = explorationRate
        self.learningRate = learningRate
        self.discount = discount

        if os.path.isfile(ML_MODEL_FILENAME):
            print("Loading ML model...")
            f = open(ML_MODEL_FILENAME)
            self.policy = pickle.load(f)
            f.close()
            print("Done loading.")
        else:
            self.policy = {}

        self.episodes = 0

        self.seenStates = 0
        self.newStates = 0

    def saveModel(self):
        print("Saving ML model...")
        f = open(ML_MODEL_FILENAME, "w")
        pickle.dump(self.policy, f)
        print("Done saving.")

    def onEpisodeStart(self):
        self.stateActions = []

    def onEpisodeEnd(self, reward):
        for curPair, nextPair in window(self.stateActions):
            state,action = curPair
            nextState, nextAction = nextPair

            if not state in self.policy:
                self.policy[state] = self.getDefaultActions()

            if not nextState in self.policy:
                self.policy[nextState] = self.getDefaultActions()

            qThis = self.policy[state][action]
            qNext = self.policy[nextState][nextAction]

            updateValue = self.learningRate * (reward + self.discount * qNext - qThis)
            self.policy[state][action] += updateValue

        self.episodes += 1

        if self.episodes % 100000 == 0:
            print("Episodes: " + str(self.episodes))
            self.saveModel()


    def getNextAction(self, state):
        #print(len(self.policy))
        possibleActions = self.getActionsWithScores(state)
        if random.random() < self.explorationRate:
            action = random.choice(list(possibleActions))
        else:
            action = max(possibleActions)

        self.stateActions.append((state, action))

        return action


    def getDefaultActions(self):
        return {
            "ROTATE": 0,
            "DROP": 0,
            "LEFT": 0,
            "RIGHT": 0
        }

    def getActionsWithScores(self, state):
        if not state in self.policy:
            self.policy[state] = self.getDefaultActions()
            self.newStates += 1
        else:
            self.seenStates += 1

        if (self.seenStates + self.newStates) % 1000 == 0:
            seenStates = float(self.seenStates)
            totalStates = float(self.seenStates + self.newStates)
            print("total states this run: " + str(totalStates))
            print("percent seen states this run: " + str((seenStates / totalStates) * 100))
        return self.policy[state]

class TetrisBoard:
    def __init__(self, width=10,height=20):
        self.boardVisibleHeight = height
        self.boardHeight = height + EXTRA_HIDDEN_ROWS # hidden rows on top
        self.boardWidth = width

        self.screenHeight = height * SQUARE_SIZE + EXTRA_BOTTOM_SPACE
        self.screenWidth = width * SQUARE_SIZE + EXTRA_RIGHT_SPACE

        self.boardState = [[0] * self.boardHeight] * self.boardWidth

        self.boardState = self.newBlankBoard()

        self.pieceSpawnTimer = PIECE_SPAWN_DELAY
        self.pieceFallTimer = PIECE_FALL_DELAY

        self.fallingPiece = []
        self.fallingPieceColor = 0

        self.learner = ReinforcementLearner()

    def newBlankBoard(self):
        boardState = []
        for y in xrange(self.boardHeight):
            row = []
            for x in range(self.boardWidth):
                row.append(0)
            boardState.append(row)

        return boardState

    def isPieceFalling(self):
        return not self.fallingPiece == []

    def getBoardWithFallingPiece(self):
        #tempBoard = deepcopy(self.boardState)
        tempBoard = [row[:] for row in self.boardState]
        for x,y in self.fallingPiece:
            tempBoard[y][x] = self.fallingPieceColor

        return tempBoard

    def getTrimmedBoard(self):
        board = self.getBoardWithFallingPiece()
        trimmedBoard = []

        highestBlock = [self.boardHeight] * self.boardWidth

        for y in xrange(self.boardHeight):
            for x in xrange(self.boardWidth):
                if board[y][x] != 0 and y < highestBlock[x]:
                    highestBlock[x] = y

        return board[min(highestBlock):max(highestBlock)]

    def getEncodedBoard(self):
        trimmed = self.getTrimmedBoard()
        encoded = ""
        for row in trimmed:
            for cell in row:
                encoded += ("0" if cell == 0 else "1")

        return encoded

    def getScore(self):
        numberOfSquaresFilled = 0
        height = 0

        for row in self.boardState:
            empty = True
            for cell in row:
                if cell != 0:
                    numberOfSquaresFilled += 1
                    empty = False
            if not empty:
                height += 1

        # This should optimize for a low stack packed tightly
        return -1 * numberOfSquaresFilled * height

    def spawnPiece(self):
        piece = random.choice(PIECES)
        self.fallingPiece = piece["points"]
        self.fallingPieceColor = piece["color"]
        self.fallingPieceOrigin = piece["origin"]

        for x,y in self.fallingPiece:
            if self.boardState[y][x] != 0:
                self.boardState = self.newBlankBoard() # Lose

    def canRotateFallingPiece(self):
        newFallingPiece = []
        originx, originy = self.fallingPieceOrigin

        neworiginx,neworiginy = originx,originy

        result = True
        for x,y in self.fallingPiece:
            newx = (y - originy) + originx
            newy = (-(x - originx)) + originy


            try:
                result = result and newx >= 0 and newy >= 0 and self.boardState[newy][newx] == 0
            except IndexError:
                result = False

        return result

    def rotateFallingPiece(self):
        newFallingPiece = []
        originx, originy = self.fallingPieceOrigin

        neworiginx,neworiginy = originx,originy

        for x,y in self.fallingPiece:
            newx = (y - originy) + originx
            newy = (-(x - originx)) + originy

            newFallingPiece.append((newx,newy))

        self.fallingPiece = newFallingPiece

    def rotateFallingPieceIfPossible(self):
        if self.canRotateFallingPiece():
            self.rotateFallingPiece()

    def canShiftFallingPiece(self, xshift, yshift):
        newFallingPiece = []
        for x,y in self.fallingPiece:
            newFallingPiece.append((x + xshift,y + yshift))

        result = True

        for x,y in newFallingPiece:
            if x >= 0 and y >= 0:
                try:
                    result = result and self.boardState[y][x] == 0
                except IndexError:
                    result = False
            else:
                result = False

        return result


    def shiftFallingPiece(self, xshift, yshift):
        newFallingPiece = []
        for x,y in self.fallingPiece:
            newFallingPiece.append((x + xshift,y + yshift))
            self.fallingPiece = newFallingPiece

        originx,originy = self.fallingPieceOrigin
        self.fallingPieceOrigin = (originx + xshift, originy + yshift)

    def shiftFallingPieceIfPossible(self, xshift,yshift):
        if self.canShiftFallingPiece(xshift,yshift):
            self.shiftFallingPiece(xshift,yshift)


    def checkForFullRows(self):
        fullRows = []
        newBoardState = []

        for y in xrange(self.boardHeight):
            full = True
            for x in xrange(self.boardWidth):
                if self.boardState[y][x] == 0:
                    full = False
            if full:
                fullRows.append(y)
                newBoardState.append([0] * self.boardWidth)


        if len(fullRows) > 0:
            for y in xrange(self.boardHeight):
                if y in fullRows:
                    continue
                else:
                    newBoardState.append(self.boardState[y])
            self.boardState = newBoardState

    def fixFallingPiece(self):
        for x,y in self.fallingPiece:
            self.boardState[y][x] = self.fallingPieceColor
        self.fallingPiece = []
        self.pieceSpawnTimer = PIECE_SPAWN_DELAY
        self.checkForFullRows()

    def actionShiftLeft(self):
        self.shiftFallingPieceIfPossible(-1,0)

    def actionShiftRight(self):
        self.shiftFallingPieceIfPossible(1,0)

    def actionDrop(self):
        if self.isPieceFalling():
            while self.canShiftFallingPiece(0,1):
                self.shiftFallingPiece(0,1)

    def actionRotate(self):
        self.rotateFallingPieceIfPossible()

    def step(self):
        if self.pieceSpawnTimer == 0:
            self.learner.onEpisodeStart()
            self.spawnPiece()
            self.pieceSpawnTimer = -1

        elif self.pieceSpawnTimer > 0:
            self.pieceSpawnTimer -= 1

        if self.isPieceFalling():
            if self.pieceFallTimer <= 0:
                if self.canShiftFallingPiece(0,1):
                    self.shiftFallingPiece(0,1)
                else:
                    self.learner.onEpisodeEnd(self.getScore())
                    self.fixFallingPiece()
                self.pieceFallTimer = PIECE_FALL_DELAY
            self.pieceFallTimer -= 1


        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            elif event.type == KEYDOWN and (event.key == K_ESCAPE or event.key == K_q):
                return False
            elif event.type == KEYDOWN:
                if event.key == K_w:
                    self.actionRotate()
                elif event.key == K_a:
                    self.actionShiftLeft()
                elif event.key == K_s:
                    pass
                elif event.key == K_d:
                    self.actionShiftRight()
                elif event.key == K_SPACE:
                    self.actionDrop()

        action = self.learner.getNextAction(self.getEncodedBoard())
        if action == "ROTATE":
            self.actionRotate()
        elif action == "DROP":
            self.actionDrop()
        elif action == "LEFT":
            self.actionShiftLeft()
        elif action == "RIGHT":
            self.actionShiftRight()

        return True # Don't quit yet

    def render(self, screen):
        board = self.getBoardWithFallingPiece()
        for y in xrange(EXTRA_HIDDEN_ROWS, self.boardHeight):
            for x in xrange(self.boardWidth):
                color = COLORS[board[y][x]]
                screenx = x * SQUARE_SIZE
                screeny = (y - EXTRA_HIDDEN_ROWS) * SQUARE_SIZE
                rect = pygame.Rect(screenx, screeny, SQUARE_SIZE, SQUARE_SIZE)

                pygame.draw.rect(screen, color, rect)

                if not color == COLORS[0]:
                    pygame.draw.rect(screen, GRAY, rect, PIECE_BORDER_WIDTH)

def main():
    pygame.init()
    board = TetrisBoard()
    screen = pygame.display.set_mode((board.screenWidth, board.screenHeight))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Tetris")

    quit = False

    quiet = "-q" in sys.argv
    fast = "-f" in sys.argv

    while board.step():
        if not quiet:
            board.render(screen)
            pygame.display.flip()
            if not fast and not quiet:
                clock.tick(60)

    board.learner.saveModel()

if __name__ == "__main__":
    main()
