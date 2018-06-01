
# ^^ note the python directive on the first line
# COMP 9414 agent initiation file 
# requires the host is running before the agent
# designed for python 3.6
# typical initiation would be (file in working directory, port = 31415)
#        python3 agent.py -p 31415
# created by Leo Hoare
# with slight modifications by Alan Blair

import sys
import socket
import pprint


# declaring visible grid to agent
view = [['' for _ in range(5)] for _ in range(5)]

current_direction = 'N'
# direction instructions
change_directions = {
    'r':{'N':'E','E':'S','S':'W','W':'N'},
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
env_graph = {}
ENV_MAP_SIZE = 6
current_point = [int(ENV_MAP_SIZE/2),int(ENV_MAP_SIZE/2)]
env_map = [['?' for _ in range(ENV_MAP_SIZE)] for _ in range(ENV_MAP_SIZE)]
locations = {
    "tree": set(),
    "door": set(),
    "water": set(),
    "wall": set(),
    "axe": set(),
    "key": set(),
    "stone": set(),
    "walk": set(),
    "river": set(),
    "non-walk": set()
}

def dijkstra(graph,src,dest,visited=[],distances={},predecessors={}):
    """ calculates a shortest path tree routed in src
    """    
    # a few sanity checks
    if src not in graph:
        raise TypeError('The root of the shortest path tree cannot be found')
    if dest not in graph:
        raise TypeError('The target of the shortest path cannot be found')    
    # ending condition
    if src == dest:
        # We build the shortest path and display it
        path=[]
        pred=dest
        while pred != None:
            path.append(pred)
            pred=predecessors.get(pred,None)
        print('shortest path: '+str(path)+" cost="+str(distances[dest])) 
    else :     
        # if it is the initial  run, initializes the cost
        if not visited: 
            distances[src]=0
        # visit the neighbors
        for neighbor in graph[src] :
            if neighbor not in visited:
                
                distance_neighbor = 1

                new_distance = distances[src] + distance_neighbor
                if new_distance < distances.get(neighbor,float('inf')):
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = src
        # mark as visited
        visited.append(src)
        # now that all neighbors have been visited: recurse                         
        # select the non visited node with lowest distance 'x'
        # run Dijskstra with src='x'
        unvisited={}
        for k in graph:
            if k not in visited:
                unvisited[k] = distances.get(k,float('inf'))        
        x=min(unvisited, key=unvisited.get)
        dijkstra(graph,x,dest,visited,distances,predecessors)

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
    

def record_view(adjusted_view, env_map, current_point):
    x = current_point[0]
    y = current_point[1]
    for i in range (-2,3):
        for j in range (-2,3):
            if env_map[x + i][j + y] in '<>^V':
                env_map[x + i][j + y] =  adjusted_view[i+2][j+2]

            if env_map[x + i][j + y] == '?':
                env_map[x + i][j + y] =  adjusted_view[i+2][j+2] 

            if env_map[x + i][j + y] in '-o~Ta$k':
                env_map[x + i][j + y] =  adjusted_view[i+2][j+2] 

            if adjusted_view[i+2][j+2] in '<>^V':
                env_map[x + i][j + y] =  adjusted_view[i+2][j+2]

    return env_map

def analyse_view(env_map, locations):
    for i in range(ENV_MAP_SIZE):
        for j in range(ENV_MAP_SIZE):
            if env_map[i][j] == 'T':
                locations["tree"].add(convert_to_tileid([i,j]))
            if env_map[i][j] == 'k':
                locations["key"].add(convert_to_tileid([i,j]))
            if env_map[i][j] == 'a':
                locations["axe"].add(convert_to_tileid([i,j]))
            if env_map[i][j] == '-':
                locations["door"].add(convert_to_tileid([i,j]))
            if env_map[i][j] == 'o':
                locations["stone"].add(convert_to_tileid([i,j]))
    return locations

def generate_graph_paths(adjusted_view, current_point, env_graph):
    x = current_point[0]
    y = current_point[1]
    for i in range(5):
        for j in range(5):
            if adjusted_view[i][j] not in '*?~-':
                from_i = i + x - 2
                from_j = j + y - 2
                from_id = convert_to_tileid([from_i,from_j])
                for l in range (i-1,i+2):
                    for k in range(j-1,j+2):
                        if (l >= 0) and (k >= 0) and (l<5) and (k <5) and ((l !=i) or (k != j)) and abs((l-i)+(k-j))==1:
                            if adjusted_view[l][k] not in '*?~-':
                                to_i = l + x - 2
                                to_j = k + y - 2
                                to_id = convert_to_tileid([to_i, to_j])
                                if from_id in env_graph:
                                    env_graph[from_id][to_id]= {"symbol": adjusted_view[l][k], "from": convert_to_rowcol(from_id), "to": convert_to_rowcol(to_id)}
                                else:
                                    env_graph[from_id] = {to_id: {"symbol": adjusted_view[l][k], "from": convert_to_rowcol(from_id), "to": convert_to_rowcol(to_id)}}
    
    return env_graph


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

    adjusted_view = adjust_view(view, current_direction, num_of_rotations, direction_symbols)

    print ("Adjusted view - Current direction " + current_direction)
    print_grid(adjusted_view)
    print ("Record map - current point {0}".format(current_point))
    env_map = record_view (adjusted_view, env_map, current_point)
    print_grid(env_map)
    locations = analyse_view(env_map, locations)
    env_graph = generate_graph_paths(adjusted_view, current_point, env_graph)
    pp = pprint.PrettyPrinter(indent=4)
    print(locations)
    pp.pprint(env_graph)
    # print(env_graph)
    # input loop to take input from user (only returns if this is valid)
    while 1:
        
        inp = input("Enter Action(s): ")
        #inp = 'f'

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
    # if len(sys.argv) != 3:
    #     print("Usage Python3 "+sys.argv[0]+" -p port \n")
    #     sys.exit(1)

    # port = int(sys.argv[2])

    port = 12345

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
