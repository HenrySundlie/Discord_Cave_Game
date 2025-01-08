# This file includes segments of working code that I might need to use again


# opening and closing json files

with open('inventory.json', 'r') as f:
    inventory = json.load(f)
inventory['Sam'].append('compass')
with open('inventory.json', 'w') as f:
    json.dump(inventory, f)


with open('room_1_squares.json', 'r') as f:
    squares = json.load(f)
squares['square 1']['characters_explored'].append('Henry')
with open('room_1_squares.json', 'w') as f:
    json.dump(squares, f)


# describe square code

async def describe_square(ctx):
    author = ctx.message.author
    character = None
    with open('character_locations.json', 'r') as f:
        character_locations = json.load(f)
    with open('room_1_squares.json', 'r') as f:
        squares = json.load(f)
    for role in author.roles:
        if role.name in character_locations:
            character = role.name
            break
    if character:
        x, y = character_locations[character]
        square = squares[x][y]
        if square in square_descriptions:
            square_description = square_descriptions[square]
            with open('square_items.json', 'r') as f:
                square_items = json.load(f)
            if square in square_items:
                if square_items[square]:
                    square_items_list = ', '.join(square_items[square])
                    await ctx.send(f'{square_description}\nItems in this square: {square_items_list}')
                else:
                    await ctx.send(f'{square_description}')
            else:
                await ctx.send(f'{square_description}')
        else:
            await ctx.send(f'No description available for {square}.')
    else:
        await ctx.send(f'You are not authorized.')

@bot.command(aliases=['d'])
async def describe(ctx):
    await describe_square(ctx)

# first try for successful view code with line segments
@bot.command(aliases=['look', 'see'])
async def view(ctx):
    author = ctx.message.author
    character = None
    with open('player_stats.json', 'r') as f:
        player_stats = json.load(f)
    character = await check_character(player_stats, author)
    with open('character_locations.json', 'r') as f:
        character_locations = json.load(f)
    character_location = character_locations[character]
    character_location = [((character_location[0] * 4) + 2), ((character_location[1] * 4) + 2)]
    with open('character_rooms.json', 'r') as f:
        character_rooms = json.load(f)
    room = character_rooms[character]
    #check which room
    if room == "Room 1":
        with open('room_1_squares.json', 'r') as f:
            squares = json.load(f)
        with open('room_1_walls.json', 'r') as f:
            walls = json.load(f)
    #start iterating through squares
    square_visibility_dict = {}
    for square in squares:
        #(0,0) target coordinates
        tg1 = [1,1]
        tg2 = [1,3]
        tg3 = [3,3]
        tg4 = [3,1]
        #find square coords
        square_coords = squares[square]["coordinates"]
        #find the 4 test values for the selected square
        tg1 = [(tg1[0] + 4 * square_coords[0]), (tg1[1] + 4 * square_coords[1])]
        tg2 = [(tg2[0] + 4 * square_coords[0]), (tg2[1] + 4 * square_coords[1])]
        tg3 = [(tg3[0] + 4 * square_coords[0]), (tg3[1] + 4 * square_coords[1])]
        tg4 = [(tg4[0] + 4 * square_coords[0]), (tg4[1] + 4 * square_coords[1])]
        tg_list = [tg1, tg2, tg3, tg4]
        #the total of 0s will be the lines that intersected with walls
        tg_fail_list = []
        for tg in tg_list:
            tg_line_slope = ((tg[1] - character_location[1]) / (tg[0] - character_location[0]))
            #using the line's equation re-arranged:
            tg_line_y_intercept = tg[1] - tg_line_slope * tg[0]
            #iterate through walls
            for wall in walls:
                if (wall[1][0] - wall[0][0]) == 0:
                    wall_slope = float('inf')
                else:
                    wall_slope = ((wall[1][1] - wall[0][1]) / (wall[1][0] - wall[0][0]))
                if (wall[1][0] - wall[0][0]) == 0:
                    wall_y_intercept = float('inf')
                else:
                    wall_y_intercept = wall[0][1] - wall_slope * wall[0][0]
                #find the intersect points of the wall line and view line
                if wall_slope == float('inf'):
                    x_intersect = wall[0][0]
                else:
                    x_intersect = abs((wall_y_intercept - tg_line_y_intercept)/(wall_slope - tg_line_slope))
                if wall_slope == float('inf'):
                    y_intersect = tg_line_slope * wall[0][0] + tg_line_y_intercept
                else:
                    y_intersect = (wall_slope * x_intersect + wall_y_intercept)
                
                #find the xs and ys to find the range
                tg_line_y_values = [tg[1], character_location[1]]
                tg_line_x_values = [tg[0], character_location[0]]
                wall_y_values = [wall[0][1], wall[1][1]]
                wall_x_values = [wall[0][0], wall[1][0]]
                #intersect = True
                intersection = True
                #see if the ranges work out
                if not min(tg_line_y_values) <= y_intersect <= max(tg_line_y_values):
                    intersection = False
                if not min(tg_line_x_values) <= x_intersect <= max(tg_line_x_values):
                    intersection = False
                if not min(wall_y_values) <= y_intersect <= max(wall_y_values):
                    intersection = False
                if not min(wall_x_values) <= x_intersect <= max(wall_y_values):
                    intersection = False
                #if the line intersects with a wall, add a 0 to the fail_list
                #   and break the loop. else, keep iterating.
                if intersection == True:
                    tg_fail_list.append(0)
                    break
        number_success_targets = 4
        for zero in tg_fail_list:
            number_success_targets -= 1
        #add square visibility to dictionary
        if number_success_targets == 4:
            square_visibility_dict[square] = 1
        elif number_success_targets in (1, 2, 3):
            square_visibility_dict[square] = .5
        elif number_success_targets == 0:
            square_visibility_dict[square] = 0
    print(square_visibility_dict)
