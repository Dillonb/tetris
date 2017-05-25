#!/usr/bin/env python2
import pygame
from pygame.locals import *
from copy import deepcopy

SQUARE_SIZE = 32 # Size of each square on the board
EXTRA_BOTTOM_SPACE = 100
EXTRA_RIGHT_SPACE = 100
PIECE_SPAWN_DELAY = 20
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
    (00,255,00), # S piece (S)
    (255,0,0) # Z piece (Z)
]
GRAY = (128,128,128)

class TetrisBoard:
    def __init__(self, width=10,height=20):
        self.boardVisibleHeight = height
        self.boardHeight = height + EXTRA_HIDDEN_ROWS # hidden rows on top
        self.boardWidth = width

        self.screenHeight = height * SQUARE_SIZE + EXTRA_BOTTOM_SPACE
        self.screenWidth = width * SQUARE_SIZE + EXTRA_RIGHT_SPACE

        self.boardState = [[0] * self.boardHeight] * self.boardWidth

        self.boardState = []
        for x in xrange(self.boardWidth):
            column = []
            for y in range(self.boardHeight):
                column.append(0)
            self.boardState.append(column)

        self.pieceSpawnTimer = PIECE_SPAWN_DELAY
        self.pieceFallTimer = PIECE_FALL_DELAY

        self.fallingPiece = []
        self.fallingPieceColor = 0

    def isPieceFalling(self):
        return not self.fallingPiece == []

    def getBoardWithFallingPiece(self):
        tempBoard = deepcopy(self.boardState)
        for x,y in self.fallingPiece:
            tempBoard[x][y] = self.fallingPieceColor

        return tempBoard

    def spawnPiece(self):
        # Line piece:
        self.fallingPiece = [
            (2,1),(3,1),(4,1),(5,1)
        ]
        self.fallingPieceColor = 1

    def canShiftFallingPiece(self, xshift, yshift):
        newFallingPiece = []
        for x,y in self.fallingPiece:
            newFallingPiece.append((x + xshift,y + yshift))

        result = True

        for x,y in newFallingPiece:
            if x >= 0 and y >= 0:
                try:
                    result = result and self.boardState[x][y] == 0
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

    def shiftFallingPieceIfPossible(self, xshift,yshift):
        if self.canShiftFallingPiece(xshift,yshift):
            self.shiftFallingPiece(xshift,yshift)

    def fixFallingPiece(self):
        for x,y in self.fallingPiece:
            self.boardState[x][y] = self.fallingPieceColor
        self.fallingPiece = []
        self.pieceSpawnTimer = PIECE_SPAWN_DELAY


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
                    pass
                elif event.key == K_a:
                    self.shiftFallingPieceIfPossible(-1,0)
                elif event.key == K_s:
                    pass
                elif event.key == K_d:
                    self.shiftFallingPieceIfPossible(1,0)
                elif event.key == K_SPACE:
                    pass

        return True # Don't quit yet

    def render(self, screen):
        board = self.getBoardWithFallingPiece()
        for x in xrange(self.boardWidth):
            for y in xrange(EXTRA_HIDDEN_ROWS, self.boardHeight):
                color = COLORS[board[x][y]]
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

    while board.step():
        clock.tick(60)
        board.render(screen)
        pygame.display.flip()

    # TODO cleanup, save ML model, quit


if __name__ == "__main__":
    main()
