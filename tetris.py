#!/usr/bin/env python2
import pygame
from pygame.locals import *
from copy import deepcopy
import random

SQUARE_SIZE = 32 # Size of each square on the board
EXTRA_BOTTOM_SPACE = 0
EXTRA_RIGHT_SPACE = 0
PIECE_SPAWN_DELAY = 0
PIECE_FALL_DELAY = 10
PIECE_BORDER_WIDTH = 2
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
        tempBoard = deepcopy(self.boardState)
        for x,y in self.fallingPiece:
            tempBoard[y][x] = self.fallingPieceColor

        return tempBoard


    def spawnPiece(self):
        piece = random.choice(PIECES)
        self.fallingPiece = piece["points"]
        self.fallingPieceColor = piece["color"]
        self.fallingPieceOrigin = piece["origin"]

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


    def step(self):
        if self.pieceSpawnTimer == 0:
            self.spawnPiece()
            self.pieceSpawnTimer = -1

        elif self.pieceSpawnTimer > 0:
            self.pieceSpawnTimer -= 1

        if self.isPieceFalling():
            if self.pieceFallTimer <= 0:
                if self.canShiftFallingPiece(0,1):
                    self.shiftFallingPiece(0,1)
                else:
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
                    self.rotateFallingPieceIfPossible()
                elif event.key == K_a:
                    self.shiftFallingPieceIfPossible(-1,0)
                elif event.key == K_s:
                    pass
                elif event.key == K_d:
                    self.shiftFallingPieceIfPossible(1,0)
                elif event.key == K_SPACE:
                    if self.isPieceFalling():
                        while self.canShiftFallingPiece(0,1):
                            self.shiftFallingPiece(0,1)

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

                if not color == COLORS[0] or True:
                    pygame.draw.rect(screen, GRAY, rect, PIECE_BORDER_WIDTH)

def main():
    pygame.init()
    board = TetrisBoard()
    screen = pygame.display.set_mode((board.screenWidth, board.screenHeight))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Tetris")

    quit = False

    while board.step():
        clock.tick(60)
        board.render(screen)
        pygame.display.flip()

    # TODO cleanup, save ML model, quit


if __name__ == "__main__":
    main()
