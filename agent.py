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

# declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

# declaring possible environment area
map_size = 80
global_map = {}

# agent orientation
directions = ['N', 'E', 'S', 'W']
agent_dir = 0
# agent_dir = directions[agent_dir]

# agent position
agent_x, agent_y = 0, 0

# function to take get action from AI or user
def get_action(view):

    ## REPLACE THIS WITH AI CODE TO CHOOSE ACTION ##
    if not global_map: update_global_map(view)

    # input loop to take input from user (only returns if this is valid)
    while True:
        inp = input("Enter Action(s): ")
        inp.strip()
        final_string = ''
        for char in inp:
            if char in ['f','l','r','c','u','b','F','L','R','C','U','B']:
                final_string += char
                if final_string:
                    return final_string[0]

def update_global_map(view):
    rotated_view = rotate_view(view, directions[agent_dir])

    for y in range(-2, 3):
        for x in range(-2, 3):
            world_x = agent_x + x
            world_y = agent_y + y
            global_map[(world_x, world_y)] = rotated_view[y + 2][x + 2]

    print(global_map)

def rotate_view(view, direction):
    if direction == 'N':
        return view
    elif direction == 'E':
        return [[view[4 - j][i] for j in range(5)] for i in range(5)]
    elif direction == 'S':
        return [[view[4 - i][4 - j] for j in range(5)] for i in range(5)]
    elif direction == 'W':
        return [[view[j][4 - i] for j in range(5)] for i in range(5)]
    else:
        print("ERROR (CRITICAL): invalid direction")
        return

def update_position_direction(action, direction):
    if action in ['f', 'F']:
        if direction == 'N' and process_positional_update(agent_y - 1, agent_x):
            global_map[(agent_x, agent_y)] = '^'
        elif direction == 'E' and process_positional_update(agent_y, agent_x + 1):
            global_map[(agent_x, agent_y)] = '>'
        elif direction == 'S' and process_positional_update(agent_y + 1, agent_x):
            global_map[(agent_x, agent_y)] = 'v'
        elif direction == 'W' and process_positional_update(agent_y, agent_x - 1):
            global_map[(agent_x, agent_y)] = '<'
        else:
            print("ERROR: agent either attempted to move into an obstacle or drown in water.")
    elif action in ['r', 'R']:
        agent_dir = (agent_dir + 1) % 4
    elif action in ['l', 'L']:
        agent_dir = (agent_dir - 1) % 4
    else:
        print(f"'{action}' is an invalid action for updating position or direction - skipping...")

    # agent_dir = directions[agent_dir]

# updates the agent's position in the global map - returns True if agent moved, False if otherwise
def process_positional_update(new_x, new_y):
    global agent_x
    global agent_y

    if view[new_y][new_x] in ['T', '-', '*']:
        print(f"ERROR: you have an obstacle '{view[new_y][new_x]}' in front of you")
        return False
    elif view[new_y][new_x] == '~':
        print("You fell into water.")
        return False
    else:
        global_map[(agent_x, agent_y)] = ''
        agent_x, agent_y = new_x, new_y
        return True

def get_map_bounds(global_map):
    """Returns min_x, max_x, min_y, max_y of explored map."""
    if not global_map:
        return 0, 0, 0, 0  # Default if map is empty

    all_x = [pos[0] for pos in global_map.keys()]
    all_y = [pos[1] for pos in global_map.keys()]

    return min(all_x), max(all_x), min(all_y), max(all_y)

def print_global_map(global_map):
    """Prints the global map with the agent's position and direction."""
    min_x, max_x, min_y, max_y = get_map_bounds(global_map)

    symbol_map = {' ': '#'}

    for y in range(min_y, max_y + 1):
        row = '|'
        for x in range(min_x, max_x + 1):
            if (x, y) in global_map:
                row += symbol_map.get(global_map.get((x, y), ''), global_map[(x, y)])
            else:
                row += '?'  # Default '?' for unexplored
        row += '|'
        print(row)

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
            update_position_direction(action, directions[agent_dir])
            sock.send(action.encode('utf-8'))

    sock.close()
