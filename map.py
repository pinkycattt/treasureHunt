import numpy as np
import random

class State:

    def __init__(self,a):
        self.a = a
        self.global_map = {}
        self.h = self.heuristic()

    def start_state(args):
        # TODO: implement
        pass

    def goal_state(rows=3,cols=0):
        # TODO: implement
        pass

    def is_equal_to(self,other):
        # TODO: implement
        pass
    
    def expand( self ):
        # TODO: implement
        pass

    def is_goal( self ):
        # TODO: implement
        pass

    def heuristic( self ):
        # TODO: implement
        pass
        
    def man_dist( self ):
        # TODO: implement
        pass

    # def print_action(self,action):
    #     print(' (',action,')')

    def print_state(self):
        min_x, max_x, min_y, max_y = self.get_map_bounds(self.global_map)

        symbol_map = {' ': ' '}

        for y in range(min_y, max_y + 1):
            row = '|'
            for x in range(min_x, max_x + 1):
                if (x, y) in self.global_map:
                    row += symbol_map.get(self.global_map.get((x, y), ''), self.global_map[(x, y)])
                else:
                    row += '?'  # Default '?' for unexplored
            row += '|'
            print(row)

    # Get the bounds of the global map
    def get_map_bounds(global_map):
        if not global_map:
            return 0, 0, 0, 0  # Default if map is empty

        all_x = [pos[0] for pos in global_map.keys()]
        all_y = [pos[1] for pos in global_map.keys()]

        return min(all_x), max(all_x), min(all_y), max(all_y)