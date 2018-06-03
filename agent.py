#!/usr/bin/python3

###################################################################################################
# COMP9414_AI_Game_Agent
# Name: Nguyen Minh Thong Huynh
# ID: 5170141
#
# RESULT
#
# This program passes ALMOST ALL of the land map, water map *(S1,S2,S3,S4,S5,S7)* with very high effiency and small number of steps !
#
# So it only fails map S0 and S6 because:
#
# For S0: at the end, it needs to be patient enought not to grab treasure right away but wait till the end of the river to have another tree for a raft
# my program is a bit greedy so it is not patient enough so it grabs the treasure right away and get stuck without having a raft to go home (so close!!!)
#
# For S6: this is extremely tricky map since it is even tricky for me to do it manually by hand since I needs to know which exact location to 
# replace stones which can be reused later to build as a foundation for a bigger bridge, so one misplaced stone to cross the islands will doom the plan 
# so currently, it is a bit beyond me since it is tricky to have a solid strategy for reusing stones later to build longer bridge.
#
# SUMMARY
#
# The programs has strategy function which follows these main steps:
# 1. Explore the map
#   a. Received 5x5 mini-map from Step.java    
#   b. Use that small map to reconstruct the full map step by step
#   c. Store locations of special tiles (door,treasure,key...) to locations dict
#   d. After exploring walkable land tiles then exploring water tiles
#   e. Keep tracking which land or water tiles are already explored
#   f. Some tiles are unreachable early on so mark it unreachable so agent dont try it again
#   g. Reaching the end without having any new action, mark unreachable tiles to be reachable and explore them again  
#  
# 2. Always validate the path to pick the sensible path 
#   a. check if a path is valid based on a player's inventory
#   b. path with doors is invalid without a key
#   c. path with tree is invalid without cutting it first
#   d. path with water tiles is invalid without number of stones is enough
#   e. path with water segments >= 2 then with or without raft is invalid
#  
# 3. While exploring, try if there is an available path to it:
#   a. Collect treasure, then go home. 
#   b. Collect axe, then chop one tree at a time if possible till we have at least one raft
#   c. Collect key, then unlock a door if possible
#   d. Collect stone, using it first before using the raft for walking on water
#
#
# Algorithm:
# 1. Dijkstra algorithm to find the shorest available path from any two tiles
# 2. MOLAP algorithm with injective map to map any cell of 2-dimension env_map to unique tile id to be processed quickly
# 
#
# Data Structures:
# 1. env_map: The full environment map reconstructed from the local mini-map 5x5
#   a. It is 2 dimension array with size: ENV_MAP_SIZE x ENV_MAP_SIZE    
# 2. env_graph: The path graph constructed from env_map
#   a. It is 2 level nested dictionary 
#   b. Example: env_graph = { from_id_1 : {
#                                               to_id_2: {..},
#                                               to_id_3: {..}          
#                                          },
#                             from_id_4: {
#                                               to_id_5: {..},
#                                               to_id_6: {..}   
#                             }
#                           }
#   c. Every edge is 2-way so every edge (from-to) entry will have entry (to-from) in env_graph
#   d. Use env_graph for dijkstra algorithm to find the shorest available path 
# 
###################################################################################################

# import libraries here
import sys
import socket
import pprint
import copy

# Debug will print out variables for debugging
DEBUG = False

# Global variables

# total map size - should be set to be 2 times bigger than input map 
ENV_MAP_SIZE = 150

BIG_NUMBER = float('inf')

# number of retry to explore unreachable tiles after finishing exploration
exploration_quota = 4

# keep tracking of exploring water phrase
in_the_water = False
water_explore_phrase = False

actions_queue=""
path_queue=[]
env_graph = {}

# the current direction of the player (North, West, East, South) - Default = 'N'
current_direction = 'N'

# stating point is right in the middle of the global environment map
current_point = [int(ENV_MAP_SIZE/2),int(ENV_MAP_SIZE/2)]

# the global environment map with ? is the unknown tiles
env_map = [['?' for _ in range(ENV_MAP_SIZE)] for _ in range(ENV_MAP_SIZE)]

# declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

# instructions which direction will be for each rotation
change_directions = {
    'r':{'N':'E','E':'S','S':'W','W':'N'},
    'rr':{'N':'S','E':'W','S':'N','W':'E'},
    'l':{'N':'W','E':'N','S':'E','W':'S'},
}

# instructions what is the next point for moving forward based on current direction
change_current_point = {
    'f':{'N':[-1,0],'E':[0,1],'W':[0,-1],'S':[1,0]}
}

# number of rotations clockwise to rotate received mini-map to correct direction
num_of_rotations = {
    'S': 2,
    'E': 1,
    'N': 0,
    'W': 3
}


direction_symbols ={
    'N':'^',
    'S':'V',
    'E':'>',
    'W':'<'
}

# inventory of the player
inventory = {
    "treasure": 0,
    "stone": 0,
    "axe": 0,
    "key": 0,
    "raft": 0 
}

# locations of special tiles in the map (yet_walk, yet_water for tiles not yet stepped on)
locations = {
    "tree": [],
    "door": [],
    "water": [],
    "wall": [],
    "treasure": [],
    "axe": [],
    "key": [],
    "stone": [],
    "water": [],
    "yet_water": [],
    "walk": [],
    "yet_walk": [],
    "unreachable": []
}



def dijkstra_search(graph, source, destination, water_explore_phrase, env_map, visited=[], distances={}, predecessors={}):
    """
    Dijkstra algorithm to find the shorest path from source tile to destination tiles
    """

    # make sure both source and destination in the path graph
    if (source not in graph) or (destination not in graph):
        return ([],None)

    # reach the destination
    if source == destination: 
        path=[]
        pred=destination
        # roll back to produce path through predecessors
        while pred != None:
            path.append(pred)
            pred=predecessors.get(pred,None)
        return (path, distances[destination])
    else :     
        # starting with source with distance is 0
        if not visited: 
            distances[source]=0
        # loop through all neighbor of the source to update their distance from source
        for neighbor in graph[source] :
            if neighbor not in visited:
                [x, y] = convert_to_rowcol(neighbor)
                tile_type = env_map[x][y]

                # make sure agent player will take longer path instead of short path through land and water tiles
                if (water_explore_phrase==False):
                    if (tile_type =='~'):
                        distance_neighbor = 50
                    else:
                        distance_neighbor = 1
                else:
                    if (tile_type =='~'):
                        distance_neighbor = 1
                    else:
                        distance_neighbor = 50
                # update its distance from the source
                new_distance = distances[source] + distance_neighbor
                if new_distance < distances.get(neighbor, BIG_NUMBER):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = source

        # the source node is visted 
        visited.append(source)

        # go through the rest to pick out shortest distance to become new source
        unvisited={}
        for i in graph:
            if i not in visited:
                unvisited[i] = distances.get(i, BIG_NUMBER)

        # if the left node distance is infinity then the destination must be in another disconnected graph
        if all(dist==BIG_NUMBER for dist in unvisited.values()):
            return ([], None)
        
        # shortest distance to become new source
        new_source = min(unvisited, key=unvisited.get)

        # recurse call 
        (final_path, final_distances) = dijkstra_search(graph, new_source, destination, water_explore_phrase, env_map, visited, distances, predecessors)
    return (final_path, final_distances)


def step_on_result(current_point, inventory, locations, in_the_water):
    """
    results for stepping on a tile 
    """
    current_tileid = convert_to_tileid(current_point)
    
    # in water or not
    if current_tileid in locations["water"]:
        in_the_water=True
        if inventory["stone"]>0:
            inventory["stone"] -=1
    else:
        in_the_water=False

    # step on a key
    if current_tileid in locations["key"]:
        inventory["key"] +=1
        locations["key"].remove(current_tileid)

    # step on a stone
    if current_tileid in locations["stone"]:
        inventory["stone"] +=1
        locations["stone"].remove(current_tileid)

    # step on an axe
    if current_tileid in locations["axe"]:
        inventory["axe"] +=1
        locations["axe"].remove(current_tileid)

    # step on treasure
    if current_tileid in locations["treasure"]:
        inventory["treasure"] +=1
        locations["treasure"].remove(current_tileid)

    #remove needed explore land tiles
    if current_tileid in locations["yet_walk"]:
        locations["yet_walk"].remove(current_tileid)

    #remove needed explore water tiles
    if current_tileid in locations["yet_water"]:
        locations["yet_water"].remove(current_tileid)


    return (inventory, locations,in_the_water)

def action_result(action, current_point, current_direction, change_current_point, inventory, locations):
    """
    results for some specific actions (cutting tree or unlocking door) 
    """
    facing_point_distance = change_current_point['f'][current_direction]
    facing_tileid = convert_to_tileid([current_point[0] + facing_point_distance[0], current_point[1] + facing_point_distance[1]])
    
    if (action=='c'):
        inventory["raft"] = 1
        locations["tree"].remove(facing_tileid)
    
    if (action=='u'):
        locations["door"].remove(facing_tileid)

    return (inventory, locations)

def rotate_clockwise_view(view, no_times, current_symbol):
    """
    rotate received 5x5 mini-map view to corrected direction  
    """
    for _ in range(no_times):
        view = list(zip(*view[::-1]))
    for i in range(len(view)):
        view[i] = list (view[i])
    view[2][2]=current_symbol
    return view

def adjust_view(view, current_direction, num_of_rotations, direction_symbols):
    """
    adjust mini-map view to match the global environment map  
    """
    return rotate_clockwise_view(view, num_of_rotations[current_direction], direction_symbols[current_direction])

def convert_to_rowcol(tile_id):
    """
    Using MOLAP injective map to map unique tile id to 2 dimension array row and col  
    """
    return [int (tile_id/ENV_MAP_SIZE), int (tile_id % ENV_MAP_SIZE)]

def convert_to_tileid(rowcol):
    """
    Using MOLAP injective map to map 2 dimension array row and col to unique tile id   
    """
    [i,j]=rowcol
    return ENV_MAP_SIZE*i+j

def which_direction(from_location_id,to_location_id):
    """
    show which direction of a to-location relative to a from-location  
    """
    [from_x, from_y] = convert_to_rowcol(from_location_id)
    [to_x, to_y] = convert_to_rowcol(to_location_id)
    if to_y < from_y:
        return 'W'
    if to_y > from_y:
        return 'E'
    if to_x < from_x:
        return 'N'
    if to_x > from_x:
        return 'S'

def action_from_direction(next_direction, cur_direction, change_directions):
    """
    show which action to move from current direction to next direction  
    """
    if (next_direction == cur_direction):
        return 'f'
    if (change_directions['r'][cur_direction] == next_direction):
        return 'rf'
    if (change_directions['l'][cur_direction] == next_direction):
        return 'lf'
    if (change_directions['rr'][cur_direction] == next_direction):
        return 'rrf'

def record_view(adjusted_view, env_map, current_point):
    """
    store 5x5 mini-view to the global environment map
    """
    x = current_point[0]
    y = current_point[1]
    for i in range (-2,3):
        for j in range (-2,3):
            if env_map[x + i][j + y] in '<>^V?-o~Ta$k':
                env_map[x + i][j + y] =  adjusted_view[i+2][j+2]

            if adjusted_view[i+2][j+2] in '<>^V':
                env_map[x + i][j + y] =  adjusted_view[i+2][j+2]

    return env_map

def check_valid_path(path, inventory, env_map):
    """
    check if a path is valid based on a player's inventory
    path with doors is invalid without a key
    path with tree is invalid without cutting it first
    path with water tiles is invalid without number of stones is enough
    path with water segments >= 2 then with or without raft is invalid
    ...
    """
    num_raft = inventory["raft"]
    num_stone = inventory["stone"]
    num_water_tiles = 0
    on_water=False
    water_segments = 0

    for tile_id in path:
        [tile_row, tile_col]= convert_to_rowcol(tile_id)
        if env_map[tile_row][tile_col] in "-T":
            return False
        if env_map[tile_row][tile_col] in "~":
            num_water_tiles+=1
            if (on_water==False):
                water_segments+=1
                on_water=True
        else:
            on_water=False
    
    if ((num_stone)>=num_water_tiles):
        return True
    
    if (water_segments<=1) and (num_raft>0):
        return True
    return False

def analyse_view(env_map, locations, actions_queue, path_queue):
    """
    analyse 5x5 mini-map to store special tile locations
    reset current intention when new intersting tile appearing 
    """
    for i in range(ENV_MAP_SIZE):
        for j in range(ENV_MAP_SIZE):
            tile_id = convert_to_tileid([i,j])
            tile_type = env_map[i][j]         
            if (tile_type == 'T') and (tile_id not in locations["tree"]):
                locations["tree"].append(tile_id)
            if (tile_type == 'k') and (tile_id not in locations["key"]):
                locations["key"].append(tile_id)
            if (tile_type == 'a') and (tile_id not in locations["axe"]):
                locations["axe"].append(tile_id)
            if (tile_type == '-') and (tile_id not in locations["door"]):
                locations["door"].append(tile_id)
            if (tile_type == 'o') and (tile_id not in locations["stone"]):
                locations["stone"].append(tile_id)

                #reset current intention
                actions_queue=[]
                path_queue=[]

            if (tile_type == '$') and (tile_id not in locations["treasure"]):
                locations["treasure"].append(tile_id)
            if tile_type == '~':
                if tile_id not in locations["water"]:
                    locations["yet_water"].append(tile_id)
                    locations["water"].append(tile_id)
            if tile_type == ' ':
                if tile_id not in locations["walk"]:
                    locations["yet_walk"].append(tile_id)
                    locations["walk"].append(tile_id)
    return (locations, actions_queue, path_queue)

def generate_graph_paths(adjusted_view, current_point, env_graph):
    """
    update possible path graph using adjusted 5x5 received mini-map
    """
    x = current_point[0]
    y = current_point[1]
    for i in range(5):
        for j in range(5):
            if adjusted_view[i][j] not in '*?.':
                from_i = i + x - 2
                from_j = j + y - 2
                from_id = convert_to_tileid([from_i,from_j])
                for l in range (i-1,i+2):
                    for k in range(j-1,j+2):
                        if (l >= 0) and (k >= 0) and (l<5) and (k <5) and ((l !=i) or (k != j)) and abs((l-i)+(k-j))==1:
                            tile_type = adjusted_view[l][k]
                            if tile_type not in '*?.':
                                to_i = l + x - 2
                                to_j = k + y - 2
                                to_id = convert_to_tileid([to_i, to_j])
                                if from_id in env_graph:
                                    env_graph[from_id][to_id]= {"from": convert_to_rowcol(from_id), "to": convert_to_rowcol(to_id)}
                                else:
                                    env_graph[from_id] = {to_id: {"from": convert_to_rowcol(from_id), "to": convert_to_rowcol(to_id)}}
    
    return env_graph

def convert_path_to_actions(path, current_direction, change_directions):
    """
    convert an valid path to a list of possible actions to do to get there
    """
    previous_direction = current_direction
    path = path[::-1]
    actions = []
    for i in range (len(path)-1):
        next_direction = which_direction(path[i],path[i+1])
        next_action = action_from_direction(next_direction, previous_direction, change_directions)
        actions.append(next_action)
        previous_direction = next_direction
    actions = ''.join(actions)
    return (actions,path)


def find_path(from_id, to_id, locations, inventory, env_map, env_graph,water_explore_phrase, stop_before=""):
    """
    using dijkstra search to find valid path, if not possible then mark it to be unreachable
    """
    (path, distance) = dijkstra_search(env_graph, from_id, to_id,water_explore_phrase, env_map,[],{},{})
    if (stop_before!=""):
        temp_path = copy.deepcopy(path)
        path = path[1:]
    if (check_valid_path(path, inventory, env_map) == False):
        path=[]
        distance=None
    if (path==[]) and (distance==None):
        if to_id not in locations["unreachable"]:
            locations['unreachable'].append(to_id)
        return ("", path, distance, locations)
        # else:
        #     raise TypeError('ERROR: explore unreachable tiles again')
    else:
        if (stop_before==""):            
            (actions, path) = convert_path_to_actions(path, current_direction, change_directions)
        else:
            (actions, path) = convert_path_to_actions(temp_path, current_direction, change_directions)
            actions = actions[:-1]
            if (stop_before=='Tree'):
                actions +='c'
            if (stop_before=='Door'):
                actions +='u'
        return (actions, path, distance, locations)

def strategy(env_graph, env_map, current_point, locations, inventory, change_directions, exploration_quota, water_explore_phrase):
    """
    the main function contains different strategies to prioritize which action should take (explore land or water, collect, cut, unlock , go home) 
    """
    from_id = convert_to_tileid(current_point)

    # trying to go home after having the treasure as early as possible
    if (inventory["treasure"]>0):
        home_loc = [int(ENV_MAP_SIZE/2),int(ENV_MAP_SIZE/2)]
        to_id = convert_to_tileid(home_loc)
        
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        if DEBUG:
            print ('trying find home with treasure dijkstra from'+ str(from_id) +' to ' + str(to_id))
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    # trying to collect treasure if knowing where it is
    if len(locations["treasure"])!=0:
        treasure_location = locations["treasure"][0]
        to_id = treasure_location
        
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        if DEBUG:
            print ('trying find treasure dijkstra from'+ str(from_id) +' to ' + str(to_id))
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    #time to collect stones
    if (len(locations["stone"])!=0):
        for to_id in locations["stone"]:
            
            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
            if DEBUG:
                print ('trying find stone dijkstra from'+ str(from_id) +' to ' + str(to_id))
                print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)


    #  trying to collect axe if knowing where it is and currently don't have it
    if (len(locations["axe"])!=0) and (inventory["axe"]==0):
        axe_location = locations["axe"][0]
        to_id = axe_location
        
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        if DEBUG:
            print ('trying find axe dijkstra from'+ str(from_id) +' to ' + str(to_id))
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    # trying to cut tree after having an axe to hava at least one raft
    if (len(locations["tree"])!=0) and (inventory["axe"]>0):
        for to_id in locations["tree"]:
            
            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase, "Tree")
            if DEBUG:
                print ('trying find tree to cut dijkstra from'+ str(from_id) +' to ' + str(to_id))
                print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)


    #  trying to collect key if knowing where it is and currently don't have it
    if (len(locations["key"])!=0) and (inventory["key"]==0):
        axe_location = locations["key"][0]
        to_id = axe_location
        
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        if DEBUG:
            print ('trying find key dijkstra from'+ str(from_id) +' to ' + str(to_id))
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    # trying to unlock door after having a key to unlock more pathways
    if (len(locations["door"])!=0) and (inventory["key"]>0):
        for to_id in locations["door"]:
            
            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase, "Door")
            if DEBUG:
                print ('trying find unlock door with key dijkstra from'+ str(from_id) +' to ' + str(to_id))
                print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)

    # explore land tiles
    if (water_explore_phrase == False):
        explore_land_tiles = []
        for tile_id in locations["yet_walk"]:
            if tile_id not in locations["unreachable"]:
                explore_land_tiles.append(tile_id)
        if len(explore_land_tiles)!=0:
            for to_id in explore_land_tiles:
                
                (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
                if DEBUG:
                    print ('trying find explore land dijkstra from'+ str(from_id) +' to ' + str(to_id))
                    print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
                if (actions == ""):
                    continue
                else:
                    return (actions, path)


    # after no more land tiles to explore, 
    # time to explore water tiles
    explore_water_tiles = []
    for tile_id in locations["yet_water"]:
        if tile_id not in locations["unreachable"]:
            explore_water_tiles.append(tile_id)
    if (inventory["raft"]>0) or (inventory["stone"]>0):
        water_explore_phrase = True
        for to_id in explore_water_tiles:

            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
            if DEBUG:
                print ("Water Phrase: "+str(water_explore_phrase))
                print ('trying find explore water dijkstra from'+ str(from_id) +' to ' + str(to_id))
                print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)

    # after reaching the end without having any next action, explore unreachable tiles (maybe they are reachable after all explorations)
    if (exploration_quota>0):
        exploration_quota -=1
        locations["unreachable"]=[]
        water_explore_phrase = False 

    # no more action can be done - agent is stuck :(  !!!
    raise TypeError('No more action can be done from strategy')     

# function to take get action from AI or user
def get_action(view):

    ## REPLACE THIS WITH AI CODE TO CHOOSE ACTION ##
    
    # make sure all global variables are available to use
    global current_direction, change_directions, num_of_rotations, current_point
    global env_graph, direction_symbols, env_map, locations, inventory
    global actions_queue, path_queue, exploration_quota, in_the_water, water_explore_phrase

    # adjust view to match the global environment map
    adjusted_view = adjust_view(view, current_direction, num_of_rotations, direction_symbols)
    
    # store 5x5 map to global map
    env_map = record_view (adjusted_view, env_map, current_point)
    
    # store special tile locations
    (locations, actions_queue, path_queue) = analyse_view(env_map, locations, actions_queue, path_queue)
    
    # update path graph based on mini-map
    env_graph = generate_graph_paths(adjusted_view, current_point, env_graph)
    
    # results if stepping on any special tiles
    (inventory, locations,in_the_water) = step_on_result(current_point, inventory, locations,in_the_water)

    # no more action from the previous strategy, need new actions
    if len(actions_queue)==0:
        (actions, path) = strategy(env_graph, env_map, current_point, locations, inventory, change_directions, exploration_quota, water_explore_phrase)
        actions_queue+=actions
        path_queue = path

    inp = actions_queue[0]
    actions_queue = actions_queue[1:]

    # printing debugging variable
    if DEBUG:
        print ("Adjusted view - Current direction " + current_direction)
        print ("Record map - current point {0}".format(current_point))
        print_grid(adjusted_view)
        print ("Whole map")
        print_grid(env_map)
        print ("Inventory:")
        print (inventory)
        print ("Locations:")
        print(locations)
        print ("The action queue is")
        print(actions_queue)
        print ("The path queue is")
        print(path_queue)
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(env_graph)
   
    # input loop to take input from user (only returns if this is valid)
    while 1:
        
        #delay = input("Press Enter")
        #inp = input("Enter Action(s): ")

        print ("NEXT INPUT IS " +str(inp))
        inp.strip()
        final_string = ''
        for char in inp:
            if char in ['f','l','r','c','u','b','F','L','R','C','U','B']:
                final_string += char
                if final_string:
                    if final_string[0] in change_directions:
                        current_direction = change_directions[final_string[0]][current_direction]
                    if final_string[0] in change_current_point:
                        new_point = change_current_point[final_string[0]][current_direction]
                        current_point[0] += new_point[0]
                        current_point[1] += new_point[1]

                    (inventory, locations) = action_result(final_string[0], current_point, current_direction, change_current_point, inventory, locations)

                    return final_string[0]

# helper function to print the grid
def print_grid(view):
    width_len = len(view[0])
    print('+', end='')
    for _ in range(width_len):
        print('-', end='')
    print('+')
    for ln in view:
        print("|", end='')
        for char in ln:
            print(str(char), end='')
        print("|")
    print('+', end='')
    for _ in range(width_len):
        print('-', end='')
    print('+')

if __name__ == "__main__":

    # checks for correct amount of arguments 
    if len(sys.argv) != 3:
        print("Usage Python3 "+sys.argv[0]+" -p port \n")
        sys.exit(1)

    port = int(sys.argv[2])

    #port = 12345

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
    while 1:
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
            action = get_action(view) # gets new actions
            sock.send(action.encode('utf-8'))

    sock.close()
