#!/usr/bin/python3

# declaring possible environment area
map_size = 80
global_map = {}

# agent orientation
directions = ['N', 'E', 'S', 'W']
agent_dir = 0
# agent_dir = directions[agent_dir]

# agent position
agent_x, agent_y = 0, 0

# Update values in global map to reflect the current view
def update_global_map(view):
    rotated_view = rotate_view(view, directions[agent_dir])

    for y in range(-2, 3):
        for x in range(-2, 3):
            world_x = agent_x + x
            world_y = agent_y + y
            global_map[(world_x, world_y)] = rotated_view[y + 2][x + 2]

    print(global_map) # REMOVE ON SUBMISSION

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
        print("ERROR (CRITICAL): invalid direction")
        return

# Update agent's position and direction on the global map
def update_position_direction(view, action, direction):
    if action in ['f', 'F']:
        if direction == 'N' and process_positional_update(view, agent_y - 1, agent_x):
            global_map[(agent_x, agent_y)] = '^'
        elif direction == 'E' and process_positional_update(view, agent_y, agent_x + 1):
            global_map[(agent_x, agent_y)] = '>'
        elif direction == 'S' and process_positional_update(view, agent_y + 1, agent_x):
            global_map[(agent_x, agent_y)] = 'v'
        elif direction == 'W' and process_positional_update(view, agent_y, agent_x - 1):
            global_map[(agent_x, agent_y)] = '<'
        else:
            print("ERROR: agent either attempted to move into an obstacle or drown in water.")
    elif action in ['r', 'R']:
        agent_dir = (agent_dir + 1) % 4
    elif action in ['l', 'L']:
        agent_dir = (agent_dir - 1) % 4
    else:
        print(f"'{action}' is an invalid action for updating position or direction - skipping...")

# updates the agent's position in the global map - returns True if agent moved, False if otherwise
def process_positional_update(view, new_x, new_y):
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