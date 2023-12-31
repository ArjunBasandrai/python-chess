from . import bitboard, fen_encoder
import numpy as np
import copy

directionOffsets = [8, -8, -1, 1, 7, -7, 9, -9]
numSquaresToEdge = []

for rank in range(8):
    for file in range(8):
        N = 7 - rank
        S = rank
        W = file
        E = 7 - file

        numSquaresToEdge.append([
            N,S,W,E,
            min(N,W),
            min(S,E),
            min(N,E),
            min(S,W)
        ])

def getSlidingMoves(board,start_square,piece,player,legalMoves,maskonly=False):
    start = 4 if abs(piece)==3 else 0
    end = 4 if abs(piece)==6 else 8
    for direction in range(start,end):
        for n in range(0,numSquaresToEdge[start_square][direction]):
            target_square = start_square + directionOffsets[direction] * (n+1)
            target_piece = board[target_square]
            if target_piece and target_piece//abs(target_piece) == player:
                break
            legalMoves.append([start_square,target_square])
            if target_piece and target_piece//abs(target_piece) == -player:
                if not maskonly:
                    break
                elif target_piece!=-player:
                    break
    return legalMoves

def getPawnMoves(board,start_square,player,legalMoves,attackonly=False):
    if not attackonly:
        direction = 0 if player==1 else 1
        offsets = range(2) if ((start_square in range(8,16) and player == 1)) or ((start_square in range(48,56) and player == -1)) else range(1)
        for n in offsets:
            target_square = start_square + directionOffsets[direction] * (n+1)
            target_piece = board[target_square]
            if target_piece and target_piece//abs(target_piece) == player:
                break
            if target_piece and target_piece//abs(target_piece) == -player:
                break
            legalMoves.append([start_square,target_square])
    
    directions = [4,6] if player==1 else [5,7]
    for direction in directions:
        if numSquaresToEdge[start_square][direction] > 0:
            target_square = start_square + directionOffsets[direction]
            target_piece = board[target_square]
            if attackonly:
                legalMoves.append([start_square,target_square])
            else:
                if target_piece and target_piece//abs(target_piece) == -player:
                    legalMoves.append([start_square,target_square])
    
    return legalMoves

def getKingMoves(board,start_square,player,legalMoves):
    for direction in range(8):
        if numSquaresToEdge[start_square][direction] > 0:
            target_square = start_square + directionOffsets[direction]
            target_piece = board[target_square]
            if target_piece and target_piece//abs(target_piece) == player:
                continue
            legalMoves.append([start_square,target_square])
    return legalMoves

def getKnightMoves(board,start_square,player,legalMoves):
    for direction in range(4):
        if numSquaresToEdge[start_square][direction] >= 2:
            intermediate_square = start_square + directionOffsets[direction] * 2
            halfstep_directions = [2,3] if direction in [0,1] else [0,1]
            for halfstep in halfstep_directions:
                if numSquaresToEdge[intermediate_square][halfstep] > 0:
                    target_square = intermediate_square + directionOffsets[halfstep] * 1
                    target_piece = board[target_square]
                    if target_piece and target_piece//abs(target_piece) == player:
                        continue
                    legalMoves.append([start_square,target_square])       
    return legalMoves

def getKnightAttackMap(board,start_square,player):
    legalMoves = []
    knightMoves = getKnightMoves(board,start_square,player,legalMoves)
    targets = [move[1] for move in knightMoves]
    knight_attack_mask = bitboard.getBitBoard(targets)
    return knight_attack_mask

def getSlidingAttackMap(board,start_square,piece,player):
    legalMoves = []
    slidingMoves = getSlidingMoves(board,start_square,piece,player,legalMoves,True)
    targets = [move[1] for move in slidingMoves]
    sliding_attack_mask = bitboard.getBitBoard(targets)
    return sliding_attack_mask

def getPawnAttackMap(board,start_square,piece,player):
    legalMoves = []
    pawnMoves = getPawnMoves(board,start_square,player,legalMoves,True)
    targets = [move[1] for move in pawnMoves]
    pawn_attack_mask = bitboard.getBitBoard(targets)
    return pawn_attack_mask

def getKingAttackMap(board,start_square,player):
    legalMoves = []
    slidingMoves = getKingMoves(board,start_square,player,legalMoves)
    targets = [move[1] for move in slidingMoves]
    king_attack_mask = bitboard.getBitBoard(targets)
    return king_attack_mask

def isChecked(king_pos,attack_mask):
    king_bit = 1 << king_pos
    if king_bit & attack_mask > 0:
        return True
    return False

def getAttackMask(board,player):
    attack_mask = 0
    for square in range(64):
        piece = board[square]
        if piece != 0:
            if piece//abs(piece) == -player:
                if abs(piece) in (3,5,6):
                    attack_mask |= (getSlidingAttackMap(board,square,piece,-player))
                if abs(piece) == 2:
                    attack_mask |= (getPawnAttackMap(board,square,piece,-player))
                if abs(piece) == 1:
                    attack_mask |= (getKingAttackMap(board,square,-player))
                if abs(piece) == 4:
                    attack_mask |= (getKnightAttackMap(board,square,-player))
    return attack_mask

def getCastle(board,player,castle,legalMoves):
    square = board.index(player)
    mask = getAttackMask(board,player)
    for i, side in enumerate(castle[:1] if player==1 else castle[2:]):
        if i % 2 == 0:
            if board[square+3]*player!=6:
                castle[i]=0
                continue
            if numSquaresToEdge[square][3] > 1:
                if (side and board[square+1]==0 and board[square+2]==0):
                    if not (isChecked(square,mask) or isChecked(square+1,mask) or isChecked(square+2,mask)):
                        legalMoves.append([square,square+2])
        else:
            if board[square-4]*player!=6:
                castle[i] =0
                continue
            if numSquaresToEdge[square][2] > 2:
                if (side and board[square-1]==0 and board[square-2]==0 and board[square-3]==0 and board[square-4]*player==6):
                    if not (isChecked(square,mask) or isChecked(square-1,mask) or isChecked(square-2,mask) or isChecked(square-3,mask)):
                        legalMoves.append([square,square-2])
    return legalMoves,castle
                                
def makeMove(board,start,target,value,player,castle,en,halfmove,fullmove,history):
    if board[target] > 0 or value==abs(2):
        halfmove = 0
    else:
        halfmove += 1

    board[target] = value

    if (value == 1):
        if target-start==2 and castle[0]:
            board[start+1]=board[target+1]
            board[target+1]=0
            castle[0],castle[1]=0,0

        if target-start==-2 and castle[1]:
            board[start-1]=board[target-2]
            board[target-2]=0
            castle[0],castle[1]=0,0
        
    if (value == -1):
        if target-start==2 and castle[2]:
            board[start+1]=board[target+1]
            board[target+1]=0
            castle[2],castle[3]=0,0
        
        if target-start==-2 and castle[3]:
            board[start-1]=board[target-2]
            board[target-2]=0
            castle[2],castle[3]=0,0
    
    if value == 1:
        castle[0],castle[1] = 0,0
    elif value == -1:
        castle[2],castle[3] = 0,0

    if value == 6 and (castle[0] or castle[1]):
        if start == 0:
            castle[1] = 0
        elif start == 7:
            castle[0] = 0;
    elif value == -6 and (castle[2] or castle[3]):
        if start == 56:
            castle[3] = 0
        elif start == 63:
            castle[2] = 0

    if value*player == 2 and en and target==(en+(player*8)):
        board[en]=0

    if value == 2 and start in range(8,16) and target==start+16:
        en=target
    elif value == -2 and start in range(48,55) and target==start-16:
        en=target
    else:
        en=None

    board[start] = 0
    if player == -1:
        fullmove+=1
    
    board = Promote(board,target,player,5)
    history.append(fen_encoder.encoder(board))
    return board,castle,en,halfmove,fullmove,history

def getMaterial(board,player):
    p = board.count(player*2)
    b = board.count(player*3)
    n = board.count(player*4)
    q = board.count(player*5)
    r = board.count(player*6)
    wb,bb=0,0
    if b:
        for rank in range(8):
            for file in range(8):
                square = rank*8+file
                if  player*board[square] == 3:
                    if (rank+file)%2==0:
                        bb+=1
                    else:
                        wb+=1
    return p,b,n,q,r,wb,bb

def isSufficientMaterial(board):
    whiteMaterial = getMaterial(board,1)
    blackMaterial = getMaterial(board,-1)
    if blackMaterial[:5] == (0,0,0,0,0) and whiteMaterial[:5] == (0,0,0,0,0):
        return False
    if (whiteMaterial[:5] == (0,1,0,0,0) and blackMaterial[:5] == (0,0,0,0,0)) or (whiteMaterial[:5] == (0,0,0,0,0) and blackMaterial[:5] == (0,1,0,0,0)):
        return False
    if (whiteMaterial[:5] == (0,0,1,0,0) and blackMaterial[:5] == (0,0,0,0,0)) or (whiteMaterial[:5] == (0,0,0,0,0) and blackMaterial[:5] == (0,0,1,0,0)):
        return False
    if (whiteMaterial == (0,1,0,0,0,1,0) and blackMaterial == (0,1,0,0,0,0,1)) or (whiteMaterial == (0,1,0,0,0,0,1) and blackMaterial == (0,1,0,0,0,1,0)):
        return False
    return True

def en_passsant(board,en,square,player,legalMoves):
    if board[square]*player == 2 and en:
        if square-1 == en or square+1 == en:
            legalMoves.append([square,en+(player*8)])
    return legalMoves

def getLegalMoves(board,player,castle,en,halfmove,history):
    attack_mask = 0
    legalMoves=[]
    
    for move in set(history):
        if history.count(move) > 2:
            return [2,[]]
        
    if halfmove == 100:
        return [2,[]]
    
    if not isSufficientMaterial(board):
        return [2,[]]
    
    for square in range(64):
        piece = board[square]
        if piece!=0:
            if piece//abs(piece) == player:
                if abs(piece) in (3,5,6):
                    legalMoves = getSlidingMoves(board,square,piece,player,legalMoves)
                if abs(piece) == 2:
                    legalMoves = getPawnMoves(board,square,player,legalMoves,False)
                    legalMoves = en_passsant(board,en,square,player,legalMoves)
                if abs(piece) == 1:
                    legalMoves = getKingMoves(board,square,player,legalMoves)
                if abs(piece) == 4:
                    legalMoves = getKnightMoves(board,square,player,legalMoves)
    illegals = []
    legalMoves,castle = getCastle(board,player,castle,legalMoves)
    for move in legalMoves:
        temp_board = board[:]
        start,target = move
        temp_board[target] = temp_board[start]
        temp_board[start] = 0

        attack_mask = getAttackMask(temp_board,player)  
        incheck = isChecked(temp_board.index(player),attack_mask)
        if incheck:
            illegals.append(move)

    legals = [x for x in legalMoves if x not in illegals]
    attack_mask = getAttackMask(board,player)
    if len(legals)==0:
        return [0,castle] if isChecked(board.index(player),attack_mask) else [1,castle]
    return legals,castle

def Promote(board,square,player,promoteTo):
    piece = board[square]
    if abs(piece) == 2:
        if (player==1 and square in range(56,64)) or (player==-1 and square in range(0,8)):
            board[square] = player*promoteTo
    return board