#!/usr/bin/python3

global_map = {}

# agent orientation
directions = ['N', 'E', 'S', 'W']
agent_dir = 0

# agent position
agent_x, agent_y = 0, 0
global_map[(0, 0)] = '^'

# agent inventory
INVENTORY = {
    'axe': False,
    'key': False,
    'dynamite': 0,
    'treasure': False,
    'raft': False
}

on_water = False

# Update values in global map to reflect the current view
def update_global_map(view):
    rotated_view = rotate_view(view, directions[agent_dir])

    for y in range(-2, 3):
        for x in range(-2, 3):
            world_x = agent_x + x
            world_y = agent_y + y
            if not (world_x, world_y) == (agent_x, agent_y):
                global_map[(world_x, world_y)] = rotated_view[y + 2][x + 2]

# Rotate the current 5x5 view to reflect correct global view
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
        print("CRITICAL ERROR: invalid direction")

# Update agent's position and direction on the global map
def process_action(action, direction):
    if action in ['f', 'F', 'r', 'R', 'l', 'L']:
        process_movement(action, direction)
    elif action in ['c', 'C', 'u', 'U', 'b', 'B']:
        process_interaction(action, direction)
    else:
        print(f"ERROR: invalid action - '{action}'")

# Process movement specific actions
def process_movement(action, direction):
    global agent_dir
    direction_map = {'N': '^', 'E': '>', 'S': 'v', 'W': '<'}
    new_x_map = {'N': 0, 'E': 1, 'S': 0, 'W': -1}
    new_y_map = {'N': -1, 'E': 0, 'S': 1, 'W': 0}
    
    if action in ['f', 'F']:
        if process_positional_update(agent_x + new_x_map[direction], agent_y + new_y_map[direction]):
            global_map[(agent_x, agent_y)] = direction_map.get(direction)
        else:
            print("ERROR: Agent attempted to move into an obstacle.")
    elif action in ['r', 'R']:
        agent_dir = (agent_dir + 1) % 4
        global_map[(agent_x, agent_y)] = direction_map.get(directions[agent_dir])
    elif action in ['l', 'L']:
        agent_dir = (agent_dir - 1) % 4
        global_map[(agent_x, agent_y)] = direction_map.get(directions[agent_dir])

# Process interaction specific actions
def process_interaction(action, direction):
    x_in_front_map = {'N': 0, 'E': 1, 'S': 0, 'W': -1}
    y_in_front_map = {'N': -1, 'E': 0, 'S': 1, 'W': 0}

    if action in ['c', 'C']:
        print("Agent is attempting to remove a tree.")
        if not INVENTORY['axe']:
            print("ERROR: Agent has no axe to remove tree.")
            return
        
        if global_map[(agent_x + x_in_front_map[direction], agent_y + y_in_front_map[direction])] == 'T':
            global_map[(agent_x + x_in_front_map[direction], agent_y + y_in_front_map[direction])] = ''
            INVENTORY['raft'] = True     # added a raft to inventory
            print("Tree removed.")
        else:
            print("ERROR: No tree to chop down in front of agent.")
            return
    elif action in ['u', 'U']:
        print("Agent is attempting to unlock a door.")
        if not INVENTORY['key']:
            print("ERROR: Agent has no key to unlock door.")
            return
        
        if global_map[(agent_x + x_in_front_map[direction], agent_y + y_in_front_map[direction])] == '-':
            global_map[(agent_x + x_in_front_map[direction], agent_y + y_in_front_map[direction])] = ''
            print("Door unlocked.")
        else:
            print("ERROR: No door to unlock in front of agent.")
            return
    elif action in ['b', 'B']:
        print("Agent is attempting to blast an obstacle.")
        if not INVENTORY['dynamite']:
            print("ERROR: Agent has no dynamite to blast obstacle.")
            return
        
        if global_map[(agent_x + x_in_front_map[direction], agent_y + y_in_front_map[direction])] in ['T', '-', '*']:
            global_map[(agent_x + x_in_front_map[direction], agent_y + y_in_front_map[direction])] = ''
            INVENTORY['dynamite'] -= 1
            print("Obstacle blasted.")
        else:
            print("ERROR: No obstacle to blast in front of agent.")
            return

# updates the agent's position in the global map - returns True if agent moved, False if otherwise
def process_positional_update(new_x, new_y):
    global agent_x, agent_y, on_water

    if global_map[(new_x, new_y)] in ['T', '-', '*']:
        print(f"ERROR: you have an obstacle '{global_map[(new_x, new_y)]}' in front of you")
        return False
    else:
        if on_water and global_map[(new_x, new_y)] != '~':
            INVENTORY['raft'] = False
            on_water = False

        if global_map[(new_x, new_y)] == 'a':
            INVENTORY['axe'] = True
        elif global_map[(new_x, new_y)] == 'k':
            INVENTORY['key'] = True
        elif global_map[(new_x, new_y)] == 'd':
            INVENTORY['dynamite'] += 1
        elif global_map[(new_x, new_y)] == '$':
            INVENTORY['treasure'] = True
        
        if global_map[(new_x, new_y)] == '~':
            if not INVENTORY['raft']:
                print("You drowned.")
            else:
                on_water = True
        
        global_map[(agent_x, agent_y)] = ''
        agent_x, agent_y = new_x, new_y
        return True

def get_agent_direction():
    return directions[agent_dir]

def get_agent_position():
    return agent_x, agent_y

def is_on_water():
    return on_water

# Get the bounds of the global map
def get_map_bounds(global_map):
    if not global_map:
        return 0, 0, 0, 0  # Default if map is empty

    all_x = [pos[0] for pos in global_map.keys()]
    all_y = [pos[1] for pos in global_map.keys()]

    return min(all_x), max(all_x), min(all_y), max(all_y)

# Print the global map with the agent's position and direction
def print_global_map(global_map):
    min_x, max_x, min_y, max_y = get_map_bounds(global_map)

    symbol_map = {' ': ' '}

    for y in range(min_y, max_y + 1):
        row = '|'
        for x in range(min_x, max_x + 1):
            if (x, y) in global_map:
                row += symbol_map.get(global_map.get((x, y), ''), global_map[(x, y)])
            else:
                row += '?'  # Default '?' for unexplored
        row += '|'
        print(row)