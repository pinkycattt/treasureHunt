# def astar(start_x, start_y, start_dir):
#     global treasure_location
#     priority_queue = []

#     # Push the starting position, cost, and inventory to the priority queue
#     heapq.heappush(priority_queue, (0, start_x, start_y, start_dir, [], copy.deepcopy(INVENTORY)))
#     visited = set()

#     while priority_queue:
#         cost, x, y, dir, path, current_inv = heapq.heappop(priority_queue)

#         if (x, y, tuple(current_inv.items())) in visited:
#             continue
#         visited.add((x, y, tuple(current_inv.items())))

#         # Get the environment at the current node
#         env = global_map.get((x, y), '?')

#         # if treasure is obtained and the current path leads to (0, 0)
#         # follow this path
#         if INVENTORY['treasure'] and (x, y) == (0, 0):
#             stuck = False
#             return path[0]
        
#         # if treasure is not obtained and the current path leads to treasure
#         # follow this path
#         if env == TOOLS['treasure']:
#             stuck = False
#             return path[0]

#         # if treasure is not obtained and the current path leads to a tool
#         # follow this path
#         if env in TOOLS.values():
#             stuck = False
#             return path[0]

#         # If the current node is unexplored, return the first move in the path
#         if env == '?':
#             stuck = False
#             return path[0] if path else 'F'

#         # Explore neighbors with obstacle handling
#         for direction, (dx, dy) in {'N': (0, -1), 'E': (1, 0), 'S': (0, 1), 'W': (-1, 0)}.items():
#             search_x, search_y = x + dx, y + dy
#             new_env = global_map.get((search_x, search_y), '?')
#             new_path = path.copy()

#             if (search_x, search_y, tuple(current_inv.items())) in visited:
#                 continue

#             move_cost = 0

#             # Assign a base move_cost to reflect the amount of moves required
#             if DIRECTIONS[direction] == DIRECTIONS[dir]:
#                 move_cost += 1  # Forward = 1
#             elif DIRECTIONS[direction] == (DIRECTIONS[dir] - 1) % 4:
#                 move_cost += 2  # Left = 2
#                 new_path += ['l']
#             elif DIRECTIONS[direction] == (DIRECTIONS[dir] + 1) % 4:
#                 move_cost += 2  # Right = 2
#                 new_path += ['r']
#             elif DIRECTIONS[direction] == (DIRECTIONS[dir] + 2) % 4:
#                 move_cost += 3  # Backward = 3
#                 new_path += ['r', 'r']
#             else:
#                 print("ERROR: something went wrong assigning a base cost")
#                 return

#             # check for any obstacles and update move_cost to reflect any additional moves
#             # required to reach this node - if the node cannot be reached currently, skip this node
#             if new_env in OBSTACLES.values():
#                 if new_env == OBSTACLES['tree']:
#                     if current_inv['axe'] or current_inv['dynamite'] > 0:
#                         # minus 1 dynamite if axe not owned - TODO: potentially update this to seek axe before using dynamite
#                         if not current_inv['axe']:
#                             current_inv['dynamite'] -= 1
#                             new_path += ['b']
#                         else:
#                             current_inv['raft'] = True
#                             new_path += ['c']
#                         move_cost += 1
#                     else:
#                         # move_cost = float('inf')
#                         continue
#                 elif new_env == OBSTACLES['door']:
#                     if current_inv['key'] or current_inv['dynamite'] > 0:
#                         # minus 1 dynamite if axe not owned - TODO: same as before
#                         if not current_inv['key']:
#                             current_inv['dynamite'] -= 1
#                             new_path += ['b']
#                         else:
#                             new_path += ['u']
#                         move_cost += 1
#                     else:
#                         # move_cost = float('inf')
#                         continue
#                 elif new_env == OBSTACLES['wall']:
#                     if current_inv['dynamite'] > 0:
#                         current_inv['dynamite'] -= 1
#                         new_path += ['b']
#                         move_cost += 1
#                     else:
#                         # move_cost = float('inf')
#                         continue
#                 elif new_env == OBSTACLES['water']:
#                     if not current_inv['raft']:
#                         # move_cost = float('inf')
#                         continue

#             # If the agent leaves water, remove the raft from the inventory
#             if env == OBSTACLES['water'] and new_env != OBSTACLES['water']:
#                 current_inv['raft'] = False

#             # Calculate the heuristic for the neighbor
#             heuristic = calculate_heuristic(search_x, search_y, current_inv)

#             new_path += ['f']
#             heapq.heappush(priority_queue, (cost + move_cost + heuristic, search_x, search_y, direction, new_path.copy(), copy.deepcopy(current_inv)))

#     # at this point, A* search could not find:
#     #   - viable path to origin if treasure is obtained
#     #   - viable path to treasure if found
#     #   - viable path to any tools
#     #   - viable path to any unexplored nodes

#     logging.debug("Default move triggered")
#     return 'f'  # Default forward move

# def calculate_heuristic(x, y, current_inv):
#     global treasure_location

#     penalty = 0

#     new_env = global_map.get((x, y), '?')
#     if new_env == OBSTACLES['wall']:
#         penalty += 100

#     # assuming worst case scenario of agent/origin and treasure being in opposite corners
#     # of the map
#     max_dist_to_treasure = 160
#     max_dist_to_origin = 160

#     # 1. If the treasure is in the inventory, prioritize returning to (0, 0)
#     if current_inv['treasure']:
#         return abs(x) + abs(y) + penalty  # Manhattan distance to (0, 0)

#     # 2. If the treasure is located, prioritize pathfinding to it
#     if treasure_location is not None:
#         treasure_x, treasure_y = treasure_location
#         dist_to_treasure = abs(x - treasure_x) + abs(y - treasure_y)
#         # return the distance to the treasure and back to (0, 0)

#         # heuristic_to_treasure(x, y, current_inv)

#         return dist_to_treasure + abs(treasure_x) + abs(treasure_y) + penalty

#     # 4. Pathfind toward any unexplored territory
#     for radius in range(3, 81):
#         for dx in range(-radius, radius + 1):
#             for dy in range(-radius, radius + 1):
#                 if abs(dx) != radius and abs(dy) != radius:
#                     continue
#                 unexplored_x, unexplored_y = x + dx, y + dy
#                 if (unexplored_x, unexplored_y) not in global_map:
#                     return abs(dx) + abs(dy) + max_dist_to_treasure + max_dist_to_origin + penalty
    
#     # Default heuristic value if no other priorities are found
#     return float('inf')