# This is a visibility function that had a major flaw and didn't work,
# so I had to get rid of it, but I spent too much time on it to want to delete it.




"""
#this returns a list of x_spiraling_values that represent
#the x values in a circle spiraling out (up first)
#a is 0 for y, 1 for x
def find_x_or_y_values(a):
    x_or_y_spiraling_values = []
    x_or_y = 0
    max = 0
    min = 0
    repeat_times = a
    repeated_already = 0
    going_up = False
    going_down = False
    for i in range(361):
        if going_up == True:
            if x_or_y < max:
                x_or_y += 1
                x_or_y_spiraling_values.append(x_or_y)
                continue
            else:
                going_up = False
        if going_down == True:
            if x_or_y > min:
                x_or_y -= 1
                x_or_y_spiraling_values.append(x_or_y)
                continue
            else:

                going_down = False
        if repeat_times == repeated_already:
            repeat_times += 1
            repeated_already = 0
            if x_or_y == min:
                going_up = True
                max += 1
            else:
                going_down = True
                min -= 1
        if repeat_times != repeated_already:
            x_or_y_spiraling_values.append(x_or_y)
            repeated_already += 1
    return x_or_y_spiraling_values

#this is the code used to create the x_and_y_values_spiral list. I copied and
#pasted fromm the terminal vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
x_values = find_x_or_y_values(1)
y_values = find_x_or_y_values(0)

x_and_y_values_for_spiral = []

for i in range(len(x_values)):
    new_coordinate = [x_values[i], y_values[i]]
    x_and_y_values_for_spiral.append(new_coordinate)
print(x_and_y_values_for_spiral)
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""

@bot.command()
async def test(ctx):
    author = ctx.message.author
    character = None
    with open('room_1_squares.json', 'r') as f:
        squares = json.load(f)
    with open('character_locations.json', 'r') as f:
        character_locations = json.load(f)
    for role in author.roles:
        if role.name in character_locations:
            character = role.name
            break
    #this command iterates through every square in the room and creates a
    #dictionary (square_identity_coords) where the keys are rooms and the values
    #the identity coords vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    character_x, character_y = 0,0
    character_x, character_y = character_locations[character]
    square_identity_coords = {}
    for square_name, square_info in squares.items():
        x, y = 0,0
        x,y = square_info["coordinates"]
        x1, y1 = x-character_x, y-character_y
        square_identity_coords[square_name] = [x1, y1]
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    square_identity_coords_list = list(square_identity_coords.values())
    square_identity_names_list = []
    with open('x_and_y_values_spiral.json', 'r') as f:
        spiral = json.load(f)
    ordered_identity_list = []
    for coords in spiral:
        if coords in square_identity_coords_list:
            ordered_identity_list.append(coords)
    #put them in order
    square_identity_coords_list = ordered_identity_list
    del ordered_identity_list
    #put square_identity_names_list in order
    for coord in square_identity_coords_list:
        for value in square_identity_coords.values():
            if coord == value:
                for name in square_identity_coords:
                    if square_identity_coords[name] == value:
                        square_identity_names_list.append(name)
    #square_identity_names_list is a list of names of the squares in spiralling
    #order. Important dictionaries/lists:
    #squares
    #square_identity_names_list
    #square_identity_coords (dictionary of squares w/ identity coords)
    for square in square_identity_names_list:
        x,y = square_identity_coords[square]
        #calculate square_slope (666 = up, -666 = down, 333 = right, -333 = left)
        if x != 0 and y != 0:
            square_slope = y / x
        else:
            if x == 0:
                if y < 0:
                    square_slope = -666
                else:
                    square_slope = 666
            else:
                if x < 0:
                    square_slope = -333
                else:
                    square_slope = 333
        #calculate square_distance
        square_distance = int(math.sqrt(x**2 + y**2))
        print(square, " ", square_distance)
    print(square_distance)
