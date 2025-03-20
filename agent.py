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
    INVENTORY
)

logging.basicConfig(level=logging.DEBUG)

# declaring possible environment area
map_size = 80
map_radius = map_size >> 1

# declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

phase = "exploration"
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
    'water': '~'
}

# define directions
DIRECTIONS = {
    'N': 0,
    'E': 1,
    'S': 2,
    'W': 3
}

full_path = []
move_count = 0

# function to take get action from AI or user
def get_action(view):
    global move_count, treasure_location

    move_count += 1
    if not treasure_location:
        treasure_location = next((k for k, v in global_map.items() if v == '$'), None)

    print(move_count)
    return explore()
    
def explore():
    agent_x, agent_y = get_agent_position()
    agent_dir = get_agent_direction()
    return astar(agent_x, agent_y, agent_dir)

def astar(start_x, start_y, start_dir):
    global treasure_location
    priority_queue = []

    # Push the starting position, cost, and inventory to the priority queue
    heapq.heappush(priority_queue, (0, start_x, start_y, start_dir, [], copy.deepcopy(INVENTORY)))
    visited = set()

    count = 0

    while priority_queue:
        cost, x, y, dir, path, current_inv = heapq.heappop(priority_queue)
        count += 1
        # logging.debug(count)
        # logging.debug(f"currently checking: (x: {x}, y: {y})")

        # Get the environment at the current node
        env = global_map.get((x, y), '?')

        # Skip already visited states
        if (x, y, tuple(current_inv.items())) in visited:
            continue
        visited.add((x, y, tuple(current_inv.items())))

         # If the treasure is obtained and the current path leads to (0, 0), follow this path
        if current_inv['treasure'] and (x, y) == (0, 0):
            logging.debug("returning")
            logging.debug(f"moving toward: ({x}, {y})")
            return path[0]

        # If the treasure is not obtained and the current path leads to treasure, follow this path
        if env == TOOLS['treasure']:
            logging.debug("to treasure")
            logging.debug(f"moving toward: ({x}, {y})")
            return path[0]

        # If the treasure is not obtained and the current path leads to a tool, follow this path
        if env in TOOLS.values():
            logging.debug("to tool")
            logging.debug(f"moving toward: ({x}, {y})")
            return path[0]

        # If the current node is unexplored, return the first move in the path
        if env == '?':
            logging.debug(f"is the current node unexplored? {(x, y) in global_map}")
            logging.debug("exploring")
            logging.debug(f"moving toward: ({x}, {y})")
            return path[0] if path else 'F'

        # Explore neighbors with obstacle handling
        for direction, (dx, dy) in {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}.items():
            search_x, search_y = x + dx, y + dy
            new_env = global_map.get((search_x, search_y), '?')
            new_path = path.copy()

            # Skip already visited states
            if (search_x, search_y, tuple(current_inv.items())) in visited:
                continue

            move_cost = 0

            # Assign a base move_cost to reflect the amount of moves required
            if DIRECTIONS[direction] == DIRECTIONS[dir]:
                move_cost += 1  # Forward = 1
            elif DIRECTIONS[direction] == (DIRECTIONS[dir] - 1) % 4:
                move_cost += 2  # Left = 2
                new_path += ['l']
            elif DIRECTIONS[direction] == (DIRECTIONS[dir] + 1) % 4:
                move_cost += 2  # Right = 2
                new_path += ['r']
            elif DIRECTIONS[direction] == (DIRECTIONS[dir] + 2) % 4:
                move_cost += 3  # Backward = 3
                new_path += ['r', 'r']
            else:
                print("ERROR: something went wrong assigning a base cost")
                return

            # Check for obstacles and update move_cost to reflect interactions
            if new_env == OBSTACLES['tree']:
                if current_inv['axe']:
                    current_inv['raft'] = True
                    new_path += ['c']
                    move_cost += 1
                elif current_inv['dynamite'] > 0:
                    current_inv['dynamite'] -= 1
                    new_path += ['b']
                    move_cost += 300        # most heavily penalise bombing trees
                else:
                    continue
            elif new_env == OBSTACLES['door']:
                if current_inv['key']:
                    new_path += ['u']
                    move_cost += 1
                elif current_inv['dynamite'] > 0:
                    current_inv['dynamite'] -= 1
                    new_path += ['b']
                    move_cost += 200        # heavily penalise bombing doors
                else:
                    continue
            elif new_env == OBSTACLES['wall']:
                if current_inv['dynamite'] > 0:
                    current_inv['dynamite'] -= 1
                    new_path += ['b']
                    move_cost += 100        # penalise bombing walls
                else:
                    continue
            elif new_env == OBSTACLES['water']:
                if not current_inv['raft']:
                    continue

            # If the agent leaves water, remove the raft from the inventory
            if env == OBSTACLES['water'] and new_env != OBSTACLES['water']:
                current_inv['raft'] = False

            # Calculate the heuristic for the neighbor
            heuristic = calculate_heuristic(search_x, search_y, current_inv)

            # Push the neighbor to the priority queue
            new_path += ['f']
            heapq.heappush(priority_queue, (cost + move_cost + heuristic, search_x, search_y, direction, new_path.copy(), copy.deepcopy(current_inv)))

    # If no viable path is found, return a default action
    logging.debug("No viable path found. Returning default action.")
    return 'f'  # Default forward move


def calculate_heuristic(x, y, current_inv):
    """
    Heuristic function to guide the agent's behavior based on the current inventory and map state.
    Prioritizes:
    - Treasure if reachable.
    - Tools if treasure is not reachable.
    - Dynamite usage if tools are not reachable.
    - Rafts before chopping trees.
    """
    global treasure_location

    # 1. If the treasure is collected, prioritize returning to (0, 0)
    if current_inv['treasure']:
        return abs(x) + abs(y)  # Manhattan distance to (0, 0)

    # 2. If the treasure is located, calculate the path to it
    if treasure_location is not None:
        treasure_x, treasure_y = treasure_location
        dist_to_treasure = abs(x - treasure_x) + abs(y - treasure_y)

        # Check if the treasure is reachable with the current inventory
        if is_reachable(treasure_x, treasure_y, current_inv):
            return dist_to_treasure  # Prioritize treasure if reachable

    # 3. If treasure is not reachable, prioritize tool collection
    for (tool_x, tool_y), tool in global_map.items():
        if tool in TOOLS.values() and is_reachable(tool_x, tool_y, current_inv):
            return abs(x - tool_x) + abs(y - tool_y)  # Prioritize tools

    # 4. If tools are not reachable, prioritize dynamite usage
    for (obstacle_x, obstacle_y), obstacle in global_map.items():
        if obstacle in OBSTACLES.values():
            if obstacle == OBSTACLES['wall'] and current_inv['dynamite'] > 0:
                return abs(x - obstacle_x) + abs(y - obstacle_y) + 10  # Penalize dynamite usage for walls
            elif obstacle == OBSTACLES['door'] and current_inv['dynamite'] > 0:
                return abs(x - obstacle_x) + abs(y - obstacle_y) + 20  # Heavily penalize dynamite usage for doors
            elif obstacle == OBSTACLES['tree'] and current_inv['dynamite'] > 0:
                return abs(x - obstacle_x) + abs(y - obstacle_y) + 30  # Most heavily penalize dynamite usage for trees

    # 5. If no treasure, tools, or obstacles are reachable, explore unexplored nodes
    for radius in range(3, 81):  # Expand search radius
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) != radius and abs(dy) != radius:
                    continue
                unexplored_x, unexplored_y = x + dx, y + dy
                if (unexplored_x, unexplored_y) not in global_map:
                    return abs(dx) + abs(dy)  # Prioritize unexplored nodes

    # Default heuristic value if no other priorities are found
    return float('inf')

def is_reachable(target_x, target_y, current_inv):
    """
    Determines if a target node is reachable with the current inventory.
    """
    # Check for obstacles and inventory requirements
    env = global_map.get((target_x, target_y), '?')
    if env == OBSTACLES['tree'] and not current_inv['axe'] and current_inv['dynamite'] == 0:
        return False  # Trees require an axe or dynamite
    if env == OBSTACLES['door'] and not current_inv['key'] and current_inv['dynamite'] == 0:
        return False  # Doors require a key or dynamite
    if env == OBSTACLES['wall'] and current_inv['dynamite'] == 0:
        return False  # Walls require dynamite
    if env == OBSTACLES['water'] and not current_inv['raft']:
        return False  # Water requires a raft
    return True

def go_to_treasure(view):
    print("Going to treasure")
    pass

def return_to_start(view):
    print("Returning to start")
    pass

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
