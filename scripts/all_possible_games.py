import contextlib
import copy
import domino
import multiprocessing
import random
import time

FIXED_MOVES = 30
SERIAL_DEPTH = 5
NUM_PROCESSES = 12
CHUNK_SIZE = 1

@contextlib.contextmanager
def stopwatch(message):
    print(message)
    start = time.time()
    yield
    elapsed = time.time() - start
    print(message, 'took {:.2f} seconds'.format(elapsed))

def run_bfs(node):
    node.bfs()
    node.prune()
    return node

def all_possible_games(fixed_moves=FIXED_MOVES, serial_depth=SERIAL_DEPTH,
                       num_processes=NUM_PROCESSES):
    with stopwatch('Initializing random game'):
        game = domino.Game()

    with stopwatch('Playing {} moves at random'.format(fixed_moves)):
        for i in range(fixed_moves):
            moves = game.valid_moves()
            move = random.choice(moves)
            result = game.make_move(*move)

            if result is not None:
                print('Fixed moves ended the game - returning early.')
                return

    with stopwatch('Saving original game state'):
        orig_game = copy.deepcopy(game)

    with stopwatch('Changing to skinny board representation'):
        game.skinny_board()

    with stopwatch('Initializing game tree'):
        root = domino.GameNode(game=game)

    with stopwatch('Running BFS to depth {} serially'.format(serial_depth)):
        root.bfs(max_depth=serial_depth, parent_pointers=True)
        nodes = list(root.leaf_nodes())

    with stopwatch('Running remaining BFS using {} processes'.format(num_processes)):
        with multiprocessing.Pool(num_processes) as pool:
            searched_nodes = []
            for i, searched_node in enumerate(pool.imap(run_bfs, nodes, CHUNK_SIZE)):
                searched_nodes.append(searched_node)

                complete = i + 1
                pct_complete = round(100 * complete / len(nodes), 2)
                print('{}/{} ({}%) tasks completed'.format(complete, len(nodes), pct_complete))

    with stopwatch('Combining BFS results'):
        for i, node in enumerate(nodes):
            node.parent_node.children[node.parent_move] = searched_nodes[i]

    with stopwatch('Computing optimal play'):
        moves, result = root.optimal_play()

    with stopwatch('Printing optimal play'):
        for move in moves:
            orig_game.make_move(*move)
            print(orig_game)

        print(result)

    return root

if __name__ == '__main__':
    all_possible_games()