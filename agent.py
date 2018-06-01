
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
env_map_size = 25
current_point = [int(env_map_size/2),int(env_map_size/2)]
env_map = [['?' for _ in range(env_map_size)] for _ in range(env_map_size)]

def rotate_clockwise_view(view, no_times, current_symbol):
    for _ in range(no_times):
        view = list(zip(*view[::-1]))
    for i in range(len(view)):
        view[i] = list (view[i])
    view[2][2]=current_symbol
    return view

def adjust_view(view, current_direction, num_of_rotations, direction_symbols):
    return rotate_clockwise_view(view, num_of_rotations[current_direction], direction_symbols[current_direction])

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

def initialize_view():
    pass

def analyse_view(view, current_direction, num_new_tiles, env_graph):
    pass

    #         [fr, to, delay, cap] = line.split()
    #         delay = int(delay)
    #         cap = int(cap)
    #         if fr in graph:
    #             env_graph[fr][to] = {'delay': delay, 'cap': cap, 'used': 0}
    #         else:
    #             env_graph[fr] = {to: {'delay': delay, 'cap': cap, 'used': 0}}

    #         if to in graph:
    #             env_graph[to][fr] = {'delay': delay, 'cap': cap, 'used': 0}
    #         else:
    #             env_graph[to] = {fr: {'delay': delay, 'cap': cap, 'used': 0}}
    # return env_graph

# function to take get action from AI or user
def get_action(view):

    ## REPLACE THIS WITH AI CODE TO CHOOSE ACTION ##
    global current_direction
    global change_directions
    global num_of_rotations
    global num_new_tiles
    # global walkable_graph
    global current_point 
    global env_map
    global direction_symbols
    adjusted_view = adjust_view(view, current_direction, num_of_rotations, direction_symbols)

    print ("Adjusted view - Current direction " + current_direction)
    print_grid(adjusted_view)
    print ("Record map - current point {0}".format(current_point))
    env_map = record_view (adjusted_view, env_map, current_point)
    print_grid(env_map) 
    # input loop to take input from user (only returns if this is valid)
    while 1:
        
        inp = input("Enter Action(s): ")
        #inp = 'r'

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
