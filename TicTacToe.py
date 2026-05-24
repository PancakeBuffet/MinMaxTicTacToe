"""TicTacToe 4x4 created by Matt Govia
Inspired by the website https://emu.edu/gaming-hub/tic-tac-toe
"""

import time
import random

my_board = [' ' for _ in range(16)]
player1_recentMoveset = []
player2_recentMoveset = []
amountToRemember = 5
gamemode_Choice = -1
gamemodeAI_difficulty = 'a'
gameRunning = True
transposition_table = {}

def minimax(board, depth, is_maximizing, alpha, beta, max_depth=6):
    """
    Minimax algorithm with alpha-beta pruning for 4x4 Tic-Tac-Toe
    'O' is the AI (maximizing player)
    'X' is the human (minimizing player)
    """
    winner = checkForWinner(board)
    board_key = get_board_key(board)
    
    # Check if we've seen this position before
    if board_key in transposition_table:
        entry = transposition_table[board_key]
        # You can also return the best move if stored
        return entry['score']
    
    # Base cases
    if winner == 'O':
        result = 10 - depth
        transposition_table[board_key] = {'score': result, 'best_move': None}
        return result
    elif winner == 'X':
        result = -10 + depth
        transposition_table[board_key] = {'score': result, 'best_move': None}
        return result
    elif depth >= max_depth:
        result = evaluate_board_heuristic(board)
        transposition_table[board_key] = {'score': result, 'best_move': None}
        return result
    elif is_board_full(board):
        result = 0
        transposition_table[board_key] = {'score': result, 'best_move': None}
        return result
    
    if is_maximizing:
        max_eval = -float('inf')
        best_move_for_position = None
        
        for move in get_ordered_moves(board):
            board[move] = 'O'
            eval = minimax(board, depth + 1, False, alpha, beta, max_depth)
            board[move] = ' '
            
            if eval > max_eval:
                max_eval = eval
                best_move_for_position = move
            
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        
        # Store both score and best move
        transposition_table[board_key] = {'score': max_eval, 'best_move': best_move_for_position}
        return max_eval
    else:
        min_eval = float('inf')
        best_move_for_position = None
        
        for move in get_ordered_moves(board):
            board[move] = 'X'
            eval = minimax(board, depth + 1, True, alpha, beta, max_depth)
            board[move] = ' '
            
            if eval < min_eval:
                min_eval = eval
                best_move_for_position = move
            
            beta = min(beta, eval)
            if beta <= alpha:
                break
        
        transposition_table[board_key] = {'score': min_eval, 'best_move': best_move_for_position}
        return min_eval

def get_oldest_player_move(player_moveset):
    """Return the oldest move position for a player"""
    if player_moveset:
        return player_moveset[0]  # First element is the oldest
    return None

def get_next_move_to_disappear(board, player_moveset, player_symbol):
    """
    Return the position that will disappear on the NEXT move
    Returns None if no piece will disappear
    """
    if len(player_moveset) >= amountToRemember:
        return player_moveset[0]  # This piece will be removed on next move
    return None

def evaluate_board_with_removal(board, player_moveset, ai_moveset):
    """
    Enhanced heuristic that considers upcoming piece removal
    """
    score = 0
    
    # Standard center preference
    center_positions = [5, 6, 9, 10]
    for pos in center_positions:
        if board[pos] == 'O':
            score += 2
        elif board[pos] == 'X':
            score -= 2
    
    # Check upcoming removals
    player_next_remove = get_next_move_to_disappear(board, player_moveset, 'X')
    ai_next_remove = get_next_move_to_disappear(board, ai_moveset, 'O')
    
    # If human's piece will disappear next move, it's less valuable to block
    if player_next_remove is not None:
        # Don't waste moves blocking a piece that will vanish anyway
        score += 3  # Advantage to AI
    
    # If AI's piece will disappear, it's a disadvantage
    if ai_next_remove is not None:
        score -= 2  # Disadvantage to AI
    
    # Evaluate winning lines with removal consideration
    win_list = [
        [0,1,2,3], [4,5,6,7], [8,9,10,11], [12,13,14,15],
        [0,4,8,12], [1,5,9,13], [2,6,10,14], [3,7,11,15],
        [0,5,10,15], [3,6,9,12]
    ]
    
    for combo in win_list:
        o_count = 0
        x_count = 0
        o_positions = []
        x_positions = []
        
        for pos in combo:
            if board[pos] == 'O':
                o_count += 1
                o_positions.append(pos)
            elif board[pos] == 'X':
                x_count += 1
                x_positions.append(pos)
        
        # If AI almost has a line
        if o_count == 3 and x_count == 0:
            # Check if the missing piece is about to disappear
            score += 10  # Very close to winning
        elif x_count == 3 and o_count == 0:
            # Check if human's line is about to be broken by removal
            missing_pos = [p for p in combo if board[p] == ' '][0]
            if missing_pos == player_next_remove:
                score += 5  # Human's potential win will self-destruct
            else:
                score -= 8  # Human is close to winning
    
    return score

def get_best_move_with_removal_strategy(board, player_moveset, ai_moveset, max_depth=4):
    """
    Enhanced minimax that considers piece removal in strategy
    """
    best_score = -float('inf')
    best_move = None
    
    # Get critical positions
    player_next_remove = get_next_move_to_disappear(board, player_moveset, 'X')
    
    # Try all possible moves for AI
    for move in get_ordered_moves_with_strategy(board, player_next_remove):
        # Try the move
        board[move] = 'O'
        
        # Evaluate with removal consideration
        move_score = minimax_with_removal(
            board, 0, False, -float('inf'), float('inf'), 
            max_depth, player_moveset, ai_moveset
        )
        
        # Undo the move
        board[move] = ' '
        
        # Update best move
        if move_score > best_score:
            best_score = move_score
            best_move = move
    
    return best_move

def get_ordered_moves_with_strategy(board, player_next_remove):
    """Order moves strategically, prioritizing positions that matter"""
    empty_spots = get_empty_positions(board)
    
    def move_value(move):
        value = 0
        
        # Prioritize center positions
        center_positions = [5, 6, 9, 10]
        if move in center_positions:
            value += 3
        
        # Prioritize the position that will free up if human loses a piece
        if player_next_remove is not None:
            # Check if this move is adjacent to or creates a line with the soon-to-be-removed piece
            adjacent_positions = get_adjacent_positions(player_next_remove)
            if move in adjacent_positions:
                value += 2
        
        # Prioritize corners
        corners = [0, 3, 12, 15]
        if move in corners:
            value += 1
        
        return value
    
    return sorted(empty_spots, key=move_value, reverse=True)

def get_adjacent_positions(position):
    """Return positions that are adjacent in winning lines"""
    # This is a simplified version - returns positions that share rows/cols/diags
    row = position // 4
    col = position % 4
    
    adjacent = []
    
    # Same row
    for c in range(4):
        if c != col:
            adjacent.append(row * 4 + c)
    
    # Same column
    for r in range(4):
        if r != row:
            adjacent.append(r * 4 + col)
    
    return adjacent

def minimax_with_removal(board, depth, is_maximizing, alpha, beta, max_depth, 
                         player_moveset, ai_moveset):
    """
    Minimax that understands piece removal mechanics
    """
    winner = checkForWinner(board)
    
    # Base cases
    if winner == 'O':
        return 100 - depth  # AI wins
    elif winner == 'X':
        return -100 + depth  # Human wins
    elif depth >= max_depth:
        return evaluate_board_with_removal(board, player_moveset, ai_moveset)
    elif is_board_full(board):
        return 0
    
    if is_maximizing:  # AI's turn (O)
        max_eval = -float('inf')
        for move in get_ordered_moves_with_strategy(board, 
                                                     get_next_move_to_disappear(board, player_moveset, 'X')):
            board[move] = 'O'
            
            # Simulate the move and track removals
            temp_ai_moveset = ai_moveset.copy() + [move]
            temp_player_moveset = player_moveset.copy()
            
            # Check if AI's move causes a removal
            if len(temp_ai_moveset) > amountToRemember:
                removed = temp_ai_moveset.pop(0)
                board[removed] = ' '
            
            eval = minimax_with_removal(board, depth + 1, False, alpha, beta, 
                                       max_depth, temp_player_moveset, temp_ai_moveset)
            
            # Undo the move
            board[move] = ' '
            if len(ai_moveset) >= amountToRemember:
                # Restore removed piece
                removed = ai_moveset[0]
                if removed != move:
                    board[removed] = 'O'
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    
    else:  # Human's turn (X)
        min_eval = float('inf')
        for move in get_empty_positions(board):
            board[move] = 'X'
            
            # Simulate the move and track removals
            temp_player_moveset = player_moveset.copy() + [move]
            temp_ai_moveset = ai_moveset.copy()
            
            # Check if human's move causes a removal
            if len(temp_player_moveset) > amountToRemember:
                removed = temp_player_moveset.pop(0)
                board[removed] = ' '
            
            eval = minimax_with_removal(board, depth + 1, True, alpha, beta, 
                                       max_depth, temp_player_moveset, temp_ai_moveset)
            
            # Undo the move
            board[move] = ' '
            if len(player_moveset) >= amountToRemember:
                # Restore removed piece
                removed = player_moveset[0]
                if removed != move:
                    board[removed] = 'X'
            
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
    
def smart_ai_move(board):
    """AI that understands and uses piece removal to its advantage"""
    print("AI is thinking..")
    time.sleep(0.5)
    
    # Use the enhanced AI that considers removal
    best_move = get_best_move_with_removal_strategy(
        board, player1_recentMoveset, player2_recentMoveset, max_depth=3
    )
    
    if best_move is not None:
        # Show strategic reasoning
        player_next_remove = get_next_move_to_disappear(board, player1_recentMoveset, 'X')
        if player_next_remove is not None:
            print(f"💡 AI notices your piece at {player_next_remove} will disappear soon!")
        
        return best_move
    
    # Fallback to regular minimax
    return minMax_computer_move(board)

def get_best_move_iterative(board, max_time=4):
    """Use iterative deepening to find best move within time limit"""
    import time
    
    best_move = None
    start_time = time.time()
    
    for depth in range(1, 6):  # Try depths 1-5
        if time.time() - start_time > max_time:
            break
        
        # FIX THIS LINE - remove the depth parameter
        move = get_best_move(board)  # NOT get_best_move(board, depth)
        if move is not None:
            best_move = move
    
    return best_move

def get_board_key(board):
    """Create a hashable representation of the board"""
    return ''.join(board)

def evaluate_board_heuristic(board):
    """Simple heuristic evaluation for when depth limit is reached"""
    score = 0
    
    # Prefer center positions (more strategic)
    center_positions = [5, 6, 9, 10]
    for pos in center_positions:
        if board[pos] == 'O':
            score += 2
        elif board[pos] == 'X':
            score -= 2
    
    # Count potential winning lines
    win_list = [
        [0,1,2,3], [4,5,6,7], [8,9,10,11], [12,13,14,15],
        [0,4,8,12], [1,5,9,13], [2,6,10,14], [3,7,11,15],
        [0,5,10,15], [3,6,9,12]
    ]
    
    for combo in win_list:
        o_count = sum(1 for pos in combo if board[pos] == 'O')
        x_count = sum(1 for pos in combo if board[pos] == 'X')
        
        if o_count == 3 and x_count == 0:
            score += 5  # Almost winning
        elif x_count == 3 and o_count == 0:
            score -= 5  # Almost losing
    
    return score

def is_board_full(board):
    """Check if the board is full"""
    return ' ' not in board

def get_empty_positions(board):
    """Return list of all empty positions"""
    return [i for i in range(16) if board[i] == ' ']

def get_best_move(board, max_depth=4):
    """
    Get the best move for AI ('O') using minimax algorithm
    Returns the position (0-15) for the best move
    """
    best_score = -float('inf')
    best_move = None
    
    # Try all possible moves for AI
    for move in get_empty_positions(board):
        # Try the move
        board[move] = 'O'
        # Evaluate the move (minimizing player's turn next)
        move_score = minimax(board, 0, False, -float('inf'), float('inf'), max_depth)
        # Undo the move
        board[move] = ' '
        
        # Update best move
        if move_score > best_score:
            best_score = move_score
            best_move = move
    
    return best_move

def minMax_computer_move(board):
    """AI uses minimax algorithm with depth limiting"""
    print("AI is thinking...")
    
    # Use dynamic depth based on game state
    empty_count = len(get_empty_positions(board))
    if empty_count > 12:
        max_depth = 3  # Early game
    elif empty_count > 8:
        max_depth = 4  # Mid game  
    else:
        max_depth = 5  # End game
    
    best_move = get_best_move(board, max_depth)
    
    if best_move is not None:
        return best_move
    
    # Fallback to random
    return computer_move(board)

def get_ordered_moves(board):
    """Return moves in order of most promising first for better pruning"""
    empty_spots = get_empty_positions(board)
    
    # Prioritize center and strategic positions
    def move_value(move):
        # Center positions are more valuable
        center_positions = [5, 6, 9, 10]
        corners = [0, 3, 12, 15]
        
        if move in center_positions:
            return 3
        elif move in corners:
            return 2
        else:
            return 1
    
    return sorted(empty_spots, key=move_value, reverse=True)

#Everything above here created with AI and double checked 
def computer_move(board):
    """Simple AI: picks a random empty spot on the board"""
    # Find all empty positions
    empty_spots = [i for i in range(16) if board[i] == ' ']
    
    if empty_spots:
        # Pick a random empty spot
        move = random.choice(empty_spots)
        return move
    return None  # No empty spots (tie game, this will never be hit)  


def print_board(gameboard):
    print(f"\n {gameboard[0]} | {gameboard[1]} | {gameboard[2]} | {gameboard[3]}\t\t\t 0 | 1 | 2 | 3 ")
    print("---|---|---|---\t\t\t---|---|---|---")
    print(f" {gameboard[4]} | {gameboard[5]} | {gameboard[6]} | {gameboard[7]}\t\t\t 4 | 5 | 6 | 7 ")
    print("---|---|---|---\t\t\t---|---|---|---")
    print(f" {gameboard[8]} | {gameboard[9]} | {gameboard[10]} | {gameboard[11]}\t\t\t 8 | 9 |10 |11")
    print("---|---|---|---\t\t\t---|---|---|---")
    print(f" {gameboard[12]} | {gameboard[13]} | {gameboard[14]} | {gameboard[15]}\t\t\t 12|13 |14 |15\n")

def player_move(board, player):
    #get input of player (player1 = 'X' player2 = 'O')
    player_symbol = 'X' if player == 'player1' else 'O'
    #first will check if the move is valid (if already a player on there will loop through and not allow it)
    valid = False
    move = ''
    while not valid:
        try:
            move = int(input(f'Player {player}, pick location [0-15]: '))
            if 0 <= move <= 15 and board[move] == ' ':
                board[move] = player_symbol
                valid = True
                player1_recentMoveset.append(move) if player == 'player1' else player2_recentMoveset.append(move) 
                player_symbol = 'O' if player_symbol == 'X' else 'X'
            else:
                print("Location taken, please try again")
        except TypeError or ValueError:
            print("Invalid number, try again and pick a valid location")

    #now reset the earliest number on the player's list back to ' '
    if player == 'player1':
        if len(player1_recentMoveset) > amountToRemember:
            oldest_move = player1_recentMoveset.pop(0)
            board[oldest_move] = ' '
            print(f"Player1's oldest piece at position {oldest_move} has been removed!")
    else:  # player2
        if len(player2_recentMoveset) > amountToRemember:
            oldest_move = player2_recentMoveset.pop(0)
            board[oldest_move] = ' '
            print(f"Player2's oldest piece at position {oldest_move} has been removed!")

    print_board(board)

  

def checkForWinner(board):
    #will hard code all win choices for now 
    #TODO: automate it so that I can have different board sizes
    """  
    0  1  2  3
    4  5  6  7
    8  9  10 11
    12 13 14 15
    """
    win_list = [
        [0,1,2,3] , [4,5,6,7] , [8,9,10,11] , [12, 13, 14, 15],         #rows
        [0,4,8,12] , [1,5,9,13] , [2,6,10,14] , [3,7,11,15] ,           #cols
        [0,5,10,15] , [3, 6, 9, 12]
    ] 

    for choices in win_list:
        if board[choices[0]] == board[choices[1]] == board[choices[2]] == board[choices[3]] != ' ':
            return board[choices[0]]
    return None
    
def reset_board(board):
    board[:] = [' ' for _ in range(16)]

def print_instructions():
    global gamemode_Choice
    global gamemodeAI_difficulty 
    print('Hello! And Welcome to 4x4 Tic-Tac-Toe. Please choose an option:')
    gameChoiceChosen = False
    while(gameChoiceChosen is False):
        try:
            numba = int(input('[0]: Play against a local player \n[1]: Play against computer \n[2]: Hello There\n[3]: Quit\n'))
            if numba == 2:
                print('Howdy 🤠')
            elif numba == 3:
                print('I hope you enjoyed playing!')
                gamemode_Choice = 3
                gameChoiceChosen = True
                
            else:
                gamemode_Choice = numba
                gameChoiceChosen = True
                if numba == 1:
                    goodChoice = False
                    gamemodeAI_difficulty = 'zz'
                    while gamemodeAI_difficulty not in ['a', 'b','c']:
                        gamemodeAI_difficulty = str(input("Enter game difficulty:\n\t 'a': Easy \t'b': Medium\t 'c': Hard\n"))

        except (Exception):
            print('Please enter one of the values')





def main():
    print("\n\n\n")
    global gamemode_Choice
    print_instructions()
    #if gamemode_Choice == 3:
    #    return
    gameRunning = True
    reset_board(my_board)
    current_player = 'player1'
    if gamemode_Choice == 0:        #User chooses local
        while gameRunning is True:
            print_board(my_board)
            
            player_move(my_board, current_player)

            winner = checkForWinner(my_board)
            if winner:
                print_board(my_board)
                print(f"Player {winner} wins!")
                gameRunning = False
                break
            current_player = 'player2' if current_player == 'player1' else 'player1'

    elif gamemode_Choice == 1:      # VS Computer
        current_player = 'player1'  # Player is X, Computer is O
        if gamemodeAI_difficulty == 'a':
            print("\n=== Easy Mode: Computer plays randomly ===")
        elif gamemodeAI_difficulty == 'b':
            print("\n=== Medium Difficult Mode: Computer uses Minimax AI ===")
        else:
            print("\n===  Difficult Mode: Computer uses Minimax AI and Remembers move that will dissappear ===")
        print("=== You are X, Computer is O ===\n")
        while gameRunning:
            print_board(my_board)
            
            if current_player == 'player1':
                player_move(my_board, current_player)
            else:
                time.sleep(1)                 
                # Get random empty spot
                if(gamemodeAI_difficulty == 'a'):
                    move = computer_move(my_board)
                elif(gamemodeAI_difficulty == 'b'):
                    move =  minMax_computer_move(my_board)
                elif(gamemodeAI_difficulty == 'c'):
                    move = smart_ai_move(my_board)
                if move is not None:
                    # Place computer's piece
                    my_board[move] = 'O'
                    print(f"Computer places O at position {move}")
                    
                    # Track computer's move
                    player2_recentMoveset.append(move)
                    
                    # Remove oldest piece if computer has more than amountToRemember
                    if len(player2_recentMoveset) > amountToRemember:
                        oldest_move = player2_recentMoveset.pop(0)
                        my_board[oldest_move] = ' '
                        print(f"Computer's oldest piece at position {oldest_move} has been removed!")
            
            # Check for winner
            winner = checkForWinner(my_board)
            if winner:
                print_board(my_board)
                if winner == 'X':
                    print("Congratulations! You win!")
                else:
                    print("Computer wins! Better luck next time!")
                gameRunning = False
                break
            
            # Switch players
            current_player = 'player2' if current_player == 'player1' else 'player1'

if __name__ == "__main__":
    time.sleep(1.5)
    main()