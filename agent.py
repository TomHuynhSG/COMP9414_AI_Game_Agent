#!/usr/bin/python3
# Name: Nguyen Minh Thong Huynh
# ID: 5170141

import sys
import socket
import pprint
import copy

# declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

current_direction = 'N'
# direction instructions
change_directions = {
    'r':{'N':'E','E':'S','S':'W','W':'N'},
    'rr':{'N':'S','E':'W','S':'N','W':'E'},
    'l':{'N':'W','E':'N','S':'E','W':'S'},
}
change_current_point = {
    'f':{'N':[-1,0],'E':[0,1],'W':[0,-1],'S':[1,0]}
}
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
num_new_tiles = 0
exploration_quota = 4
env_graph = {}
ENV_MAP_SIZE = 90
current_point = [int(ENV_MAP_SIZE/2),int(ENV_MAP_SIZE/2)]
env_map = [['?' for _ in range(ENV_MAP_SIZE)] for _ in range(ENV_MAP_SIZE)]
inventory = {
    "treasure": 0,
    "stone": 0,
    "axe": 0,
    "key": 0,
    "raft": 0 
}
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
in_the_water = False
water_explore_phrase = False
actions_queue=""
path_queue=[]


def dijkstra_path_search(graph, source, destination, water_explore_phrase, env_map, visited=[], distances={}, predecessors={}):

    if source not in graph:
        return ([],None)

    if destination not in graph:
        return ([],None)
   
    if source == destination: 

        path=[]
        pred=destination
        while pred != None:
            path.append(pred)
            pred=predecessors.get(pred,None)
        
        return (path, distances[destination])
        
    else :     

        if not visited: 
            distances[source]=0

        for neighbor in graph[source] :
            if neighbor not in visited:
                [x, y] = convert_to_rowcol(neighbor)
                tile_type = env_map[x][y]
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
                new_distance = distances[source] + distance_neighbor
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = source

        visited.append(source)

        unvisited={}
        for k in graph:
            if k not in visited:
                unvisited[k] = distances.get(k, float('inf'))
        if all(dist==float('inf') for dist in unvisited.values()):
            return ([], None)
        new_source = min(unvisited, key=unvisited.get)
        (final_path, final_distances) = dijkstra_path_search(graph, new_source, destination, water_explore_phrase, env_map, visited, distances, predecessors)
    return (final_path, final_distances)


def step_on_result(current_point, inventory, locations, in_the_water):
    current_tileid = convert_to_tileid(current_point)
    
    # collect stuffs
    if current_tileid in locations["water"]:
        in_the_water=True
    else:
        in_the_water=False

    if current_tileid in locations["key"]:
        inventory["key"] +=1
        locations["key"].remove(current_tileid)
        print ("Picked up key at "+str(current_tileid))
    if current_tileid in locations["stone"]:
        inventory["stone"] +=1
        locations["stone"].remove(current_tileid)
        print ("Picked up stone at "+str(current_tileid))
    if current_tileid in locations["axe"]:
        inventory["axe"] +=1
        locations["axe"].remove(current_tileid)
        print ("Picked up axe at "+str(current_tileid))
    if current_tileid in locations["treasure"]:
        inventory["treasure"] +=1
        locations["treasure"].remove(current_tileid)
        print ("Picked up treasure at "+str(current_tileid))
    #remove needed explore tiles
    if current_tileid in locations["yet_walk"]:
        locations["yet_walk"].remove(current_tileid)
        print ("Explored at "+str(current_tileid))
    if current_tileid in locations["yet_water"]:
        locations["yet_water"].remove(current_tileid)
        print ("Explored at "+str(current_tileid))

    return (inventory, locations,in_the_water)

def action_result(action, current_point, current_direction, change_current_point, inventory, locations):
    facing_point_distance = change_current_point['f'][current_direction]
    facing_tileid = convert_to_tileid([current_point[0] + facing_point_distance[0], current_point[1] + facing_point_distance[1]])
    
    if (action=='c'):
        inventory["raft"] = 1
        locations["tree"].remove(facing_tileid)
    
    if (action=='u'):
        locations["door"].remove(facing_tileid)

    return (inventory, locations)

def rotate_clockwise_view(view, no_times, current_symbol):
    for _ in range(no_times):
        view = list(zip(*view[::-1]))
    for i in range(len(view)):
        view[i] = list (view[i])
    view[2][2]=current_symbol
    return view

def adjust_view(view, current_direction, num_of_rotations, direction_symbols):
    return rotate_clockwise_view(view, num_of_rotations[current_direction], direction_symbols[current_direction])

def convert_to_rowcol(tile_id):
    return [int (tile_id/ENV_MAP_SIZE), int (tile_id % ENV_MAP_SIZE)]

def convert_to_tileid(rowcol):
    [i,j]=rowcol
    return ENV_MAP_SIZE*i+j

def which_direction(from_location_id,to_location_id):  
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
    if (next_direction == cur_direction):
        return 'f'
    if (change_directions['r'][cur_direction] == next_direction):
        return 'rf'
    if (change_directions['l'][cur_direction] == next_direction):
        return 'lf'
    if (change_directions['rr'][cur_direction] == next_direction):
        return 'rrf'

def record_view(adjusted_view, env_map, current_point):
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
    num_raft = inventory["raft"]
    num_stone = inventory["stone"]
    for tile_id in path:
        [tile_row, tile_col]= convert_to_rowcol(tile_id)
        if env_map[tile_row][tile_col] in "-T":
            return False
        if env_map[tile_row][tile_col] in "~":
            if (num_stone>0) or (num_raft>0):
                if (num_stone)>0:
                    num_stone -=1
                else:
                    num_stone = 0
            else:
                return False
    return True

def analyse_view(env_map, locations):
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
    return locations

def generate_graph_paths(adjusted_view, current_point, env_graph):
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
                            # if (adjusted_view[l][k] not in "^><V-"):
                            tile_type = adjusted_view[l][k]
                            # else:
                            #     to_symbol = " "
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
    (path, distance) = dijkstra_path_search(env_graph, from_id, to_id,water_explore_phrase, env_map,[],{},{})
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
    from_id = convert_to_tileid(current_point)


    if (inventory["treasure"]>0):
        home_loc = [int(ENV_MAP_SIZE/2),int(ENV_MAP_SIZE/2)]
        to_id = convert_to_tileid(home_loc)
        print ('trying find home with treasure dijkstra from'+ str(from_id) +' to ' + str(to_id))
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    #time to get the treasure
    if len(locations["treasure"])!=0:
        treasure_location = locations["treasure"][0]
        to_id = treasure_location
        print ('trying find treasure dijkstra from'+ str(from_id) +' to ' + str(to_id))
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    #time to get the axe
    if (len(locations["axe"])!=0) and (inventory["axe"]==0):
        axe_location = locations["axe"][0]
        to_id = axe_location
        print ('trying find axe dijkstra from'+ str(from_id) +' to ' + str(to_id))
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    #time to cut the tree with axe
    if (len(locations["tree"])!=0) and (inventory["axe"]>0):
        for to_id in locations["tree"]:
            print ('trying find tree to cut dijkstra from'+ str(from_id) +' to ' + str(to_id))
            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase, "Tree")
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)

    #time to collect stones
    # if (len(locations["stone"])!=0):
    #     for to_id in locations["stone"]:
    #         print ('trying find stone dijkstra from'+ str(from_id) +' to ' + str(to_id))
    #         (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase, "Tree")
    #         print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
    #         if (actions == ""):
    #             continue
    #         else:
    #             return (actions, path)

    #time to get the key
    if (len(locations["key"])!=0) and (inventory["key"]==0):
        axe_location = locations["key"][0]
        to_id = axe_location
        print ('trying find key dijkstra from'+ str(from_id) +' to ' + str(to_id))
        (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
        print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
        if (actions != ""):
            return (actions, path)

    #time to unlock the door with key
    if (len(locations["door"])!=0) and (inventory["key"]>0):
        for to_id in locations["door"]:
            print ('trying find unlock door with key dijkstra from'+ str(from_id) +' to ' + str(to_id))
            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase, "Door")
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)


    if (water_explore_phrase == False):
        explore_land_tiles = []
        for tile_id in locations["yet_walk"]:
            if tile_id not in locations["unreachable"]:
                explore_land_tiles.append(tile_id)
        if len(explore_land_tiles)!=0:
            for to_id in explore_land_tiles:
                print ('trying find explore land dijkstra from'+ str(from_id) +' to ' + str(to_id))
                (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
                print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
                if (actions == ""):
                    continue
                else:
                    return (actions, path)


    #Time to explore water
     
    explore_water_tiles = []
    for tile_id in locations["yet_water"]:
        if tile_id not in locations["unreachable"]:
            explore_water_tiles.append(tile_id)
    if (inventory["raft"]>0) or (inventory["stone"]>0):
        water_explore_phrase = True
        for to_id in explore_water_tiles:
            print ("Water Phrase: "+str(water_explore_phrase))
            print ('trying find explore water dijkstra from'+ str(from_id) +' to ' + str(to_id))
            (actions, path, distance, locations)= find_path(from_id, to_id, locations, inventory, env_map, env_graph, water_explore_phrase)
            print('path from'+ str(from_id) +' to ' + str(to_id) + ': '+str(path)+" cost="+str(distance))
            if (actions == ""):
                continue
            else:
                return (actions, path)

    if (exploration_quota>0):
        exploration_quota -=1
        locations["unreachable"]=[]
        water_explore_phrase = False 
    else:
        raise TypeError('No more free tiles to explore')
    #no more exploration can be done!!!
    


    raise TypeError('Need more strategies - no more actions')     


# function to take get action from AI or user
def get_action(view):

    ## REPLACE THIS WITH AI CODE TO CHOOSE ACTION ##
    global current_direction
    global change_directions
    global num_of_rotations
    global num_new_tiles
    global current_point
    global env_graph
    global env_map
    global direction_symbols
    global locations
    global inventory
    global actions_queue
    global path_queue
    global exploration_quota
    global in_the_water
    global water_explore_phrase
    adjusted_view = adjust_view(view, current_direction, num_of_rotations, direction_symbols)

    print ("Adjusted view - Current direction " + current_direction)
    print_grid(adjusted_view)
    print ("Record map - current point {0}".format(current_point))
    env_map = record_view (adjusted_view, env_map, current_point)
    print_grid(env_map)
    locations = analyse_view(env_map, locations)
    env_graph = generate_graph_paths(adjusted_view, current_point, env_graph)
    (inventory, locations,in_the_water) = step_on_result(current_point, inventory, locations,in_the_water)
    print (inventory)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(env_graph)
    print(locations)
    

    if len(actions_queue)==0:
        (actions, path) = strategy(env_graph, env_map, current_point, locations, inventory, change_directions, exploration_quota, water_explore_phrase)
        actions_queue+=actions
        path_queue = path
    print ("The action queue is")
    print(actions_queue)
    print ("The path queue is")
    print(path_queue)
    a = []
    for tile_id in path_queue:
        a.append(convert_to_rowcol(tile_id))
    print (a)
    inp = actions_queue[0]
    actions_queue = actions_queue[1:]
    
    # print(env_graph)
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
