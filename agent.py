#!/usr/bin/python3
# ^^ note the python directive on the first line
# COMP3411/9814 agent initiation file 
# requires the host to be running before the agent
# typical initiation would be (file in working directory, port = 31415)
#        python3 agent.py -p 31415
# created by Leo Hoare
# with slight modifications by Alan Blair

import sys
import socket

import logging

from collections import deque
import heapq
import copy
from mapUpdateHelpers import (
    global_map,
    update_global_map,
    process_action,
    print_global_map,
    get_agent_direction,
    get_agent_position,
    is_on_water,
    INVENTORY
)

logging.basicConfig(level=logging.DEBUG)

# declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

treasure_location = None

# define tools
TOOLS = {
    'axe': 'a',
    'key': 'k',
    'dynamite': 'd',
    'treasure': '$'
}

# define obstacles
OBSTACLES = {
    'tree': 'T',
    'door': '-',
    'wall': '*',
    'water': '~',
    'void': '.'
}

# define directions
DIRECTIONS = {
    'N': 0,
    'E': 1,
    'S': 2,
    'W': 3
}

def get_action(view):
    """
    Retrieves the next action to take via an A* search.
    """
    global move_count, treasure_location

    if not treasure_location:
        treasure_location = next((k for k, v in global_map.items() if v == '$'), None)

    agent_x, agent_y = get_agent_position()
    agent_dir = get_agent_direction()
    return astar(agent_x, agent_y, agent_dir)

def astar(start_x, start_y, start_dir):
    """
    Establishes an A* search with the objective function f(n) = g(n) + h(n)
    where g(n) is a penalised cost of reaching the current node and h(n) is the
    penalised heuristic of reaching the final target
    """
    global treasure_location
    priority_queue = []

    # push the starting position, direction, cost, and inventory to the priority queue
    heapq.heappush(priority_queue, (0, start_x, start_y, start_dir, [], copy.deepcopy(INVENTORY), is_on_water()))
    visited = set()

    while priority_queue:
        cost, x, y, dir, path, current_inv, on_water = heapq.heappop(priority_queue)

        # get the environment at the current node
        env = global_map.get((x, y), '?')

        # skip already visited states
        if (x, y, tuple(current_inv.items())) in visited:
            continue
        visited.add((x, y, tuple(current_inv.items())))

        # if the treasure is obtained and the current path leads to (0, 0), follow this path
        if current_inv['treasure'] and (x, y) == (0, 0):
            return path[0]

        # if the treasure is not obtained and the current path leads to treasure, follow this path
        if env == TOOLS['treasure']:
            return path[0]

        # if the treasure is not obtained and the current path leads to a tool, follow this path
        if env in TOOLS.values():
            return path[0]

        # if the current node is unexplored, return the first move in the path
        if env == '?':
            return path[0]
        
        # if the current node is an obstacle (it should be a critical one to remove), follow
        # this path 
        if env in ['T', '-', '*']:
            return path[0]

        # expand the current node in each direction
        for direction, (dx, dy) in {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}.items():
            search_x, search_y = x + dx, y + dy
            new_env = global_map.get((search_x, search_y), '?')     # environment at neighbour
            new_path = path.copy()                                  # copy of path
            new_inv = copy.deepcopy(current_inv)                    # copy of inventory
            new_on_water = on_water

            # skip already visited states
            if (search_x, search_y, tuple(current_inv.items())) in visited:
                continue

            move_cost = 0

            # assign a base move_cost to reflect the amount of moves required
            if DIRECTIONS[direction] == DIRECTIONS[dir]:
                move_cost += 1  # forwards = 1
            elif DIRECTIONS[direction] == (DIRECTIONS[dir] - 1) % 4:
                move_cost += 2  # left = 2
                new_path += ['l']
            elif DIRECTIONS[direction] == (DIRECTIONS[dir] + 1) % 4:
                move_cost += 2  # right = 2
                new_path += ['r']
            elif DIRECTIONS[direction] == (DIRECTIONS[dir] + 2) % 4:
                move_cost += 3  # backwards = 3
                new_path += ['r', 'r']
            else:
                print("ERROR: something went wrong assigning a base cost")
                return

            # check for obstacles and update move_cost to reflect interactions
            if new_env == OBSTACLES['tree']:
                if current_inv['axe']:
                    if current_inv['raft']:
                        move_cost += 300    # if raft is owned, penalise chopping trees
                    new_inv['raft'] = True
                    new_path += ['c']
                    move_cost += 1
                elif current_inv['dynamite'] > 0:
                    new_inv['dynamite'] -= 1
                    new_path += ['b']
                    move_cost += dynamite_usage_heuristic(search_x, search_y, x, y)
                else:
                    continue
            elif new_env == OBSTACLES['door']:
                if current_inv['key']:
                    new_path += ['u']
                    move_cost += 1
                elif current_inv['dynamite'] > 0:
                    new_inv['dynamite'] -= 1
                    new_path += ['b']
                    move_cost += dynamite_usage_heuristic(search_x, search_y, x, y)
                else:
                    continue
            elif new_env == OBSTACLES['wall']:
                if current_inv['dynamite'] > 0:
                    new_inv['dynamite'] -= 1
                    new_path += ['b']
                    move_cost += dynamite_usage_heuristic(search_x, search_y, x, y)
                else:
                    continue
            elif new_env == OBSTACLES['water']:
                if not current_inv['raft']:
                    continue
                else:
                    new_on_water = True
                    move_cost += 1
            elif new_env == OBSTACLES['void']:
                continue

            # if the agent leaves water, remove the raft from the inventory
            if on_water and new_env != OBSTACLES['water']:
                new_inv['raft'] = False
                new_on_water = False
                move_cost += 500        # heavily penalise leaving water

            # calculate the heuristic for the neighbor
            heuristic = calculate_heuristic(search_x, search_y, new_inv)

            # push the neighbor to the priority queue
            new_path += ['f']
            heapq.heappush(priority_queue, (cost + move_cost + heuristic, search_x, search_y, direction, new_path, new_inv, new_on_water))

    # if no viable path is found, return a default action - WILL CAUSE ISSUES IF TRIGGERED MOST LIKELY
    return 'f'

def dynamite_usage_heuristic(x, y, prev_x, prev_y):
    """
    Determines if an obstacle at (x, y) blocks access to significant nodes
    (e.g., treasure, tools, or unexplored areas) using BFS. If so, it would be
    beneficial to use dynamite on this obstacle.
    """
    visited = set()
    queue = deque([(x, y)])

    # ensures that dynamite will opt to blast walls over doors over trees
    penalties = {
        'T': 300,
        '-': 200,
        '*': 100
    }

    while queue:
        current_x, current_y = queue.popleft()

        # skip already visited nodes and the node on the path that led to the obstacle
        # since we don't want to go back the way we came
        if (current_x, current_y) in visited or (current_x, current_y) == (prev_x, prev_y):
            continue
        visited.add((current_x, current_y))

        # check if the current node is significant
        env = global_map.get((current_x, current_y), '?')
        
        # prioritise breaking obstacles that lead to tools rather than new areas
        if env in TOOLS.values():
            return 100 + penalties[global_map[(x, y)]]
        elif env == '?':
            return 500 + penalties[global_map[(x, y)]]

        # add neighbors to the queue if they are not blocked
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor_x, neighbor_y = current_x + dx, current_y + dy
            neighbor_env = global_map.get((neighbor_x, neighbor_y), '?')

            # skip blocked paths unless they are the obstacle itself
            if neighbor_env in OBSTACLES.values() and (neighbor_x, neighbor_y) != (x, y):
                continue

            queue.append((neighbor_x, neighbor_y))

    return float('inf')

def calculate_heuristic(search_x, search_y, current_inv):
    global treasure_location

    # 1. if the treasure is collected, prioritise returning to (0, 0)
    if current_inv['treasure']:
        return abs(search_x) + abs(search_y)

    # 2. if the treasure is located, prioritise pathfinding towards it
    if treasure_location is not None:
        treasure_x, treasure_y = treasure_location
        return abs(treasure_x - search_x) + abs(treasure_y - search_y)

    # 3. if treasure is not reachable, prioritise tool collection
    for (tool_x, tool_y), tool in global_map.items():
        if tool in TOOLS.values():
            return abs(search_x - tool_x) + abs(search_y - tool_y)

    # 4. if no treasure, tools, or obstacles are reachable, explore unexplored nodes
    for radius in range(3, 81):  # skips the inner 5x5 box since this is all within the agent's view
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) != radius and abs(dy) != radius:
                    continue
                unexplored_x, unexplored_y = search_x + dx, search_y + dy
                if (unexplored_x, unexplored_y) not in global_map:
                    return abs(dx) + abs(dy)

    # default heuristic value if no other priorities are found
    return float('inf')

# helper function to print the grid
def print_grid(view):
    print('+-----+')
    for ln in view:
        print("|"+str(ln[0])+str(ln[1])+str(ln[2])+str(ln[3])+str(ln[4])+"|")
    print('+-----+')

if __name__ == "__main__":

    # checks for correct amount of arguments 
    if len(sys.argv) != 3:
        print("Usage Python3 "+sys.argv[0]+" -p port \n")
        sys.exit(1)

    port = int(sys.argv[2])

    # checking for valid port number
    if not 1025 <= port <= 65535:
        print('Incorrect port number')
        sys.exit()

    # creates TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
         # tries to connect to host
         # requires host is running before agent
         sock.connect(('localhost',port))
    except (ConnectionRefusedError):
         print('Connection refused, check host is running')
         sys.exit()

    # navigates through grid with input stream of data
    i=0
    j=0
    while True:
        data=sock.recv(100)
        if not data:
            exit()
        for ch in data:
            if (i==2 and j==2):
                view[i][j] = '^'
                view[i][j+1] = chr(ch)
                j+=1 
            else:
                view[i][j] = chr(ch)
            j+=1
            if j>4:
                j=0
                i=(i+1)%5
        if j==0 and i==0:
            print_grid(view) # COMMENT THIS OUT ON SUBMISSION
            update_global_map(view)
            print_global_map(global_map)
            action = get_action(view) # gets new actions
            process_action(action, get_agent_direction())
            sock.send(action.encode('utf-8'))

    sock.close()
