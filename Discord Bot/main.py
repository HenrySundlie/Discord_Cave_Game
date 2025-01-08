"""
• All actions take 30 seconds? maybe less

• active_things is a dictionary of all of the beings that are currently active.
   This means that they are moving and stuff

• So far, move is the only command that needs to use time. it takes 30 seconds.

• Should all actions take the same amount of time? Should pickup take any time?
  Maybe only in battle?
  Drop: takes no time
  Pickup: Normally doesn't take time. Add check for when in battle

• Next things to do: battle
"""

import json
import discord
from discord.ext import commands
from discord import File
from PIL import Image, ImageDraw, ImageFont
import io
from io import BytesIO
import math
from fractions import Fraction
from collections import OrderedDict
import random

#kadsjhfkasdjhf aksdjhfalsjdfhalkjfh aljdsfh 

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
intents.dm_messages = True

#adds an amount to the time. specify minutes, seconds, or hours. json file
#   stores time in hours
def time_elapse(amount, units):
    if units == "seconds":
        amount = amount / 60 / 60
    elif units == "minutes":
        amount = amount / 60
    with open('time.json', 'r') as f:
        time = json.load(f)
    time["time"] += amount
    with open('time.json', 'w') as f:
        json.dump(time, f)

#puts the object at the end of the turns list
def turns(object):
    with open('turns.json', 'r') as f:
        turns = json.load(f)
    turns.remove(object)
    turns.append(object)
    with open('turns.json', 'w') as f:
        json.dump(turns, f)

#returns True if character is first in turns list, False otherwise
def turnCheck(character):
    with open('turns.json', 'r') as f:
        turns = json.load(f)
    if turns[0] == character:
        return True
    else:
        return False


async def move_character(direction: str, author):
    character = None
    for role in author.roles:
        with open('players.json', 'r') as f:
            players = json.load(f)
        if role.name in players:
            character = role.name
            break
        with open('room_1_squares.json', 'r') as f:
            squares = json.load(f)
    if character:
        x, y = players[character]["coordinates"]
        old_square = find_matching_square((x,y), squares)
        if direction in squares[old_square]["walls"]:
            return "You can't move through a wall!"
        else:
            if direction == "north":
                y += 1
            elif direction == "south":
                y -= 1
            elif direction == "west":
                x -= 1
            elif direction == "east":
                x += 1
            else:
                return "Invalid direction, please enter 'north', 'south', 'west', or 'east'."
            new_square = find_matching_square((x,y), squares)
            if new_square:
                players[character]["coordinates"] = [x, y]
                players[character]["just_moved"] = "yes"
                string = (f'{character} has been moved.')
                with open('players.json', 'w') as f:
                    json.dump(players, f)
                if character not in squares[new_square]["characters_explored"]:
                    squares[new_square]["characters_explored"].append(character)
                with open('room_1_squares.json', 'w') as f:
                    json.dump(squares, f)
                return string
            else:
                return 'Cannot move outside of the grid.'
    else:
        return 'You are not authorized.'

def find_matching_square(coord, squares):
    for square_name, square_info in squares.items():
        if square_info["coordinates"] == list(coord):
            return square_name
    return None

async def check_character(json_file, author):
    for role in author.roles:
        if role.name in json_file:
            return role.name
    return None

#async def battle(attacker, defender):

@bot.command(aliases=['help!'])
async def bot_description(ctx):
    commands_and_descriptions = {'move': 'roll your movement dice, and then type in n, e, s, or w to move in that direction.',
                                 'pickup [item]': 'get an item in your square and put it in your inventory',
                                 'drop [item]': 'drop an item onto your square',
                                 'stats': 'see your stats',
                                 'map': "send a map of all the squares that you've explored privately to yourself. You have to find a map first though!",
                                 'view': 'get a quick list of items that you can see',
                                 'details [command]': 'get more info on a specific command.',
                                 'visible squares': 'get a list of the visibility of every square.'}
    message = ""
    for command, description in commands_and_descriptions.items():
        message += f"type !{command} to {description}\n"
    message += "Miscellaneous info: One square is about 3 by 3 feet, the only command that you have to take turns with (as of now) is the move command. Everything else can be executed at any time."
    await ctx.send(message)

detailed_descriptions = {('move', 'n', 'w', 'e', 's'): 'Rolls your movement dice and adds your movement bonus. You may move that many times. This will not work if:\n1. It\'s not your turn: the bot will ask you if you want to skip your friend\'s turn.\n2. If someone else is currently in the process of moving: two people can\'t move at once.',
                            ('pickup', 'get', 'take'): 'Type !pickup [item], and if the item is in your square, it retrieves item and puts it in your inventory.',
                            ('send_map', 'map'): 'DMs you a picture of your map. You have to have a map to use this command, and only squares that you\'ve been on show up.',
                            ('stats', 'show_stats'): 'Sends you your current stats and inventory.',
                            ('view', 'v', 'look', 'see'): 'Sends you a list of items that you can see, and what squares they are on. Large items can always be seen, as long as the square is at least partially visible (PV). The smaller items give you a 50/50 chance of being seen if the square is only PV.',
                            ('visible_squares', 'visible'): 'Sends you the visibility of every square in your room'
                            }

@bot.command()
async def details(ctx, arg1: str):

    # Check if the command is "!describe" followed by command
    if (ctx.message.content.startswith('!details') or
        ctx.message.content.startswith('!d')
    ) and len(ctx.message.content.split()) == 2:
        command = arg1
        for key, value in detailed_descriptions.items():
            if command.lower() in key:
                await ctx.send(value)
    else:
        await ctx.send("Invalid command. Use !describe followed by the command")

#dict for when a character is moving (used in bot event)
isMovingDict = {}
#dict for when a character wants to skip a turn (or not) used in a bot event
isSkippingTurn = {}

@bot.command(aliases=['m', 'go'])
async def move(ctx):
    with open('players.json', 'r') as f:
        players = json.load(f)
    author = ctx.message.author
    character = None
    character = await check_character(players, author)
    #check to see if someone else is moving
    if isMovingDict:
        await ctx.send("Someone else is in the middle of a move, " + character + ".")
        return
    #check to see if it's their turn
    elif turnCheck(character) == False:
        await ctx.send("It's not your turn! Do you wish to skip your friends turn? ('y' or 'n')")
        isSkippingTurn[ctx.author.id] = "isSkippingTurn"
    else:
        #put them at the end of the turns file
        turns(character)
        #30 seconds elapse
        time_elapse(30, "seconds")
        #sets the user's state in isMovingDict to moving
        isMovingDict[ctx.author.id] = "isMoving"
        SpeedBase = players[character]["Stats"]["SpeedBase"]
        SpeedBonus = players[character]["Stats"]["SpeedBonus"]
        roll = random.randint(1, SpeedBase) + SpeedBonus
        players[character]["current_movement_roll"] = roll
        with open('players.json', 'w') as f:
            json.dump(players, f)
        await ctx.send("You (" + character + ") rolled a " + str(roll) + ". Type the letter of the direction you want to move.")

#the bot event for when a character is moving, or when he wants to skip a turn
@bot.event
async def on_message(message):
    #ignore commands?
    await bot.process_commands(message)
    #ignore bot's messages
    if message.author.bot:
        return
    channel = message.channel
    global isMovingDict
    global isSkippingTurn
    #if he's moving
    if isMovingDict.get(message.author.id) == "isMoving":
        author = message.author
        message = (str(message.content)).lower()
        with open('players.json', 'r') as f:
            players = json.load(f)
        character = await check_character(players, author)
        roll = players[character]["current_movement_roll"]
        if roll > 0:
            if message in ("n", "north", "e", "east", "s", "south", "w", "west", "done", "d", "stop"):
                messagesend = ""
                if message in ("n", "north"):
                    direction = "north"
                    messagesend = await move_character(direction, author)
                    await channel.send(messagesend)
                elif message in ("e", "east"):
                    direction = "east"
                    messagesend = await move_character(direction, author)
                    await channel.send(messagesend)
                elif message in ("s", "south"):
                    direction = "south"
                    messagesend = await move_character(direction, author)
                    await channel.send(messagesend)
                elif message in ("w", "west"):
                    direction = "west"
                    messagesend = await move_character(direction, author)
                    await channel.send(messagesend)
                elif message in ("done", "d", "stop"):
                    roll = 0
                    players[character]["current_movement_roll"] = roll
                    with open('players.json', 'w') as f:
                        json.dump(players, f)
                    isMovingDict = {}
                if not (messagesend == "You can't move through a wall!" or
                messagesend == "Invalid direction, please enter 'north', 'south', 'west', or 'east'." or
                messagesend == 'Cannot move outside of the grid.' or
                messagesend == 'You are not authorized.' or
                messagesend == ""):
                    with open('players.json', 'r') as f:
                        players = json.load(f)
                    roll -= 1
                    players[character]["current_movement_roll"] = roll
                    with open('players.json', 'w') as f:
                        json.dump(players, f)
                if roll > 0:
                    await channel.send("You have " + str(roll) + " moves left.")
                else:
                    await channel.send("You are done moving")
                    isMovingDict = {}
        else:
            await channel.send("You have a roll of 0, and are done moving.")
            isMovingDict = {}
    #if he's skipping a turn (sends him back up to previous one if he is)
    elif isSkippingTurn.get(message.author.id) == "isSkippingTurn":
        author = message.author
        message = (str(message.content)).lower()
        #does he want to skip his friend?
        if message in ("n", "no"):
            await channel.send("Your move is canceled")
            isSkippingTurn = {}
        elif message in ("yes", "y"):
            with open('players.json', 'r') as f:
                players = json.load(f)
            character = await check_character(players, author)
            #30 seconds elapse
            time_elapse(30, "seconds")
            #put them at the end of the turns file
            turns(character)
            #sets the user's state in isMovingDict to moving
            isMovingDict[author.id] = "isMoving"
            SpeedBase = players[character]["Stats"]["SpeedBase"]
            SpeedBonus = players[character]["Stats"]["SpeedBonus"]
            roll = random.randint(1, SpeedBase) + SpeedBonus
            players[character]["current_movement_roll"] = roll
            with open('players.json', 'w') as f:
                json.dump(players, f)
            await channel.send("You rolled a " + str(roll) + ". Type the letter of the direction you want to move.")
            isSkippingTurn = {}

@bot.command(aliases=['pickup', 'get'])
async def take_item(ctx, item: str):
    author = ctx.message.author
    character = None
    with open('players.json', 'r') as f:
        players = json.load(f)
    for role in author.roles:
        if role.name in players:
            character = role.name
            break
    with open('room_1_squares.json', 'r') as f:
        squares = json.load(f)
    if character:
        x, y = players[character]["coordinates"]
        coord = (x,y)
        square = find_matching_square(coord, squares)
        items = squares[square]["items"]
        if item in items:
            full_item = items[item]
            del items[item]
            squares[square]["items"] = items
            with open('room_1_squares.json', 'w') as f:
                json.dump(squares, f)
            if item not in players[character]["inventory"]:
                players[character]["inventory"][item] = full_item
                with open('players.json', 'w') as f:
                    json.dump(players, f)
            else:
                if "quantity" in players[character]["inventory"][item]:
                    players[character]["inventory"][item]["quantity"] += 1
                else:
                    players[character]["inventory"][item]["quantity"] = 1
                with open('players.json', 'w') as f:
                    json.dump(players, f)
            await ctx.send(f'You picked up {item}.')
        else:
            await ctx.send(f'{item} is not in this square.')
    else:
        await ctx.send(f'You are not authorized.')


@bot.command(aliases=['d'])
async def drop(ctx, item: str):
    with open("players.json", "r") as f:
        players = json.load(f)
    author = ctx.message.author
    character = None
    character = await check_character(players, author)
    with open('room_1_squares.json', 'r') as f:
        squares = json.load(f)
    x, y = players[character]["coordinates"]
    coord = (x, y)
    square = find_matching_square(coord, squares)
    if item in players[character]["inventory"]:
        full_item = players[character]["inventory"][item]
        if full_item["quantity"] > 1:
            players[character]["inventory"][item]["quantity"] -= 1
        else:
            del players[character]["inventory"][item]
        if item in squares[square]["items"]:
            squares[square]["items"][item]["quantity"] += 1
        else:
            squares[square]["items"][item] = full_item
            squares[square]["items"][item]["quantity"] = 1

        with open('room_1_squares.json', 'w') as f:
            json.dump(squares, f)
        with open('players.json', 'w') as f:
            json.dump(players, f)

        await ctx.send("You dropped a " + str(item))
    else:
        await ctx.send("You don't have a " + str(item))


@bot.command(aliases=['map'])
async def send_map(ctx):
    with open('room_1_squares.json', 'r') as f:
        squares = json.load(f)
    image = None
    author = ctx.message.author
    character = None
    with open('players.json', 'r') as f:
        players = json.load(f)
    for role in author.roles:
        if role.name in players:
            character = role.name
            break
    if "map" in players[character]["inventory"]:
        width = int(math.sqrt(len(squares)) * 35) + 35
        height = int(math.sqrt(len(squares)) * 35) + 35
        image = Image.new('RGB', (width, height), (160, 160, 160))
        draw = ImageDraw.Draw(image)
        for square in squares.values():
            if character in square["characters_explored"]:
                x, y = square["coordinates"]

                x1, y1 = ((x + 1) * 35), (height - ((y+1) * 35)) -35
                x2, y2 = ((x + 2) * 35 - 1), (height - (y * 35) - 1) -35
                draw.rectangle(((x1, y1), (x2, y2)), outline=(50, 50, 50), fill=(139, 139, 139), width=1)
                if "north" in square["walls"]:
                    draw.line((x1, y1, x2, y1), fill=(0, 0, 0), width=3)
                if "east" in square["walls"]:
                    draw.line((x2, y1, x2, y2), fill=(0, 0, 0), width=3)
                if "south" in square["walls"]:
                    draw.line((x1, y2, x2, y2), fill=(0, 0, 0), width=3)
                if "west" in square["walls"]:
                    draw.line((x1, y1, x1, y2), fill=(0, 0, 0), width=3)
        # Add numbers along the bottom and left edges
        for i in range(len(squares)):
            x, y = i % int(math.sqrt(len(squares))), i // int(math.sqrt(len(squares)))
            x0, y0 = (x + 1) * 35, height - ((y + 1) * 35)
            x1, y1 = x0 + 35, y0 + 35
            draw.text((x0 + 15, height - 20), str(x), fill=(0, 0, 0))
            draw.text((15, y0 - 20), str(y), fill=(0, 0, 0))
        # Save the image to a BytesIO object
        if image is not None:
            image_binary = io.BytesIO()
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            user = ctx.author
            await user.send(file=discord.File(fp=image_binary, filename='map.png'))
    else:
        await ctx.send("Sorry, you don't have a map yet")

@bot.command(aliases=['stats'])
async def show_stats(ctx):
    author = ctx.message.author
    character = None
    with open('players.json', 'r') as f:
        players = json.load(f)
    character = await check_character(players, author)
    inventory = players[character]["inventory"]
    if inventory:
        inventory_list = []
        for key, value in inventory.items():
            inventory_list.append(key)
    if character:
        message = ""
        await ctx.send(f'Inventory: {inventory_list}')
        for stat, value in players[character]["Stats"].items():
            message += f'{stat}: {value}\n'
        await ctx.send(message)
    else:
        await ctx.send('Something\'s wrong')

#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv view func stuff
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Given three collinear points p, q, r, the function checks if
# point q lies on line segment 'pr'
def onSegment(p, q, r):
    if ( (q.x <= max(p.x, r.x)) and (q.x >= min(p.x, r.x)) and
        (q.y <= max(p.y, r.y)) and (q.y >= min(p.y, r.y))):
        return True
    return False

def orientation(p, q, r):
    # to find the orientation of an ordered triplet (p,q,r)
    # function returns the following values:
    # 0 : Collinear points
    # 1 : Clockwise points
    # 2 : Counterclockwise

    # See https://www.geeksforgeeks.org/orientation-3-ordered-points/amp/
    # for details of below formula.

    val = (float(q.y - p.y) * (r.x - q.x)) - (float(q.x - p.x) * (r.y - q.y))
    if (val > 0):

        # Clockwise orientation
        return 1
    elif (val < 0):

        # Counterclockwise orientation
        return 2
    else:

        # Collinear orientation
        return 0

# The main function that returns true if
# the line segment 'p1q1' and 'p2q2' intersect.
def doIntersect(p1,q1,p2,q2):

    # Find the 4 orientations required for
    # the general and special cases
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if ((o1 != o2) and (o3 != o4)):
        return True

    # Special Cases

    # p1 , q1 and p2 are collinear and p2 lies on segment p1q1
    if ((o1 == 0) and onSegment(p1, p2, q1)):
        return True

    # p1 , q1 and q2 are collinear and q2 lies on segment p1q1
    if ((o2 == 0) and onSegment(p1, q2, q1)):
        return True

    # p2 , q2 and p1 are collinear and p1 lies on segment p2q2
    if ((o3 == 0) and onSegment(p2, p1, q2)):
        return True

    # p2 , q2 and q1 are collinear and q1 lies on segment p2q2
    if ((o4 == 0) and onSegment(p2, q1, q2)):
        return True

    # If none of the cases
    return False
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

def visible_squares(squares, walls, character_location):
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
        for tg_point in tg_list:
            for wall in walls:
                #target line = p1,q1 and wall = p2,q2
                p1 = Point(character_location[0], character_location[1])
                q1 = Point(tg_point[0], tg_point[1])
                p2 = Point(wall[0][0], wall[0][1])
                q2 = Point(wall[1][0], wall[1][1])

                if doIntersect(p1, q1, p2, q2):
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
    return square_visibility_dict

@bot.command(aliases=['look', 'see', 'v'])
async def view(ctx):
    author = ctx.message.author
    character = None
    with open('players.json', 'r') as f:
        players = json.load(f)
    character = await check_character(players, author)
    character_location = players[character]["coordinates"]
    character_location = [((character_location[0] * 4) + 2), ((character_location[1] * 4) + 2)]
    room = players[character]["Room"]
    #check which room
    if room == 1:
        with open('room_1_squares.json', 'r') as f:
            squares = json.load(f)
        with open('room_1_walls.json', 'r') as f:
            walls = json.load(f)
    if players[character]["just_moved"] == "no":
        for string in players[character]["current_view_list"]:
            await ctx.send(string)
    else:
        square_visibility_dict = visible_squares(squares, walls, character_location)
        outputs = {}
        for square in square_visibility_dict:
            items = squares[square]["items"]
            coordinates = tuple(squares[square]["coordinates"])
            #if square is totally visible
            if square_visibility_dict[square] == 1:
                if items:
                    for key in items.keys():
                        print(key + " are totally visible")
                        outputs[coordinates] = key
            #if its partially visible
            elif square_visibility_dict[square] == .5:
                for item, values in items.items():
                    print(item + " is half visible")
                    item_size = values["size"]
                    #if its large its visible
                    if item_size == "large":
                        outputs[coordinates] = item
                    #if its small its 50% chance visible
                    elif item_size == "small":
                        x = random.randint(1,2)
                        if x == 1:
                            outputs[coordinates] = item
        print(outputs)
        for key, value in outputs.items():
            string = str(key) + ": " + str(value)
            print(string)
            players[character]["current_view_list"].append(string)
            await ctx.send(string)
        players[character]["just_moved"] = "no"
        with open('players.json', 'w') as f:
            json.dump(players, f)

@bot.command()
async def visible(ctx, arg1: str):
    if (ctx.message.content.startswith('!visible') or
        ctx.message.content.startswith('!vis')
    ) and len(ctx.message.content.split()) == 2:
        author = ctx.message.author
        character = None
        with open('players.json', 'r') as f:
            players = json.load(f)
        character = await check_character(players, author)
        character_location = players[character]["coordinates"]
        character_location = [((character_location[0] * 4) + 2), ((character_location[1] * 4) + 2)]
        room = players[character]["Room"]
        #check which room
        if room == 1:
            with open('room_1_squares.json', 'r') as f:
                squares = json.load(f)
            with open('room_1_walls.json', 'r') as f:
                walls = json.load(f)
        square_visibility_dict = visible_squares(squares, walls, character_location)
        message = ""
        for key, value in square_visibility_dict.items():
            coords = squares[key]["coordinates"]
            if value == 1:
                message += f'{coords} is visible\n'
            elif value == .5:
                message += f'{coords} is partially visible\n'
            elif value == 0:
                message += f'{coords} is not visible\n'
        await ctx.send(message)
    else:
        await ctx.send("Command not understood")

@bot.command(aliases=['l', 'L', 'coordinates'])
async def location(ctx):
    with open("players.json", "r") as f:
        players = json.load(f)
    author = ctx.message.author
    character = None
    character = await check_character(players, author)
    location = players[character]["coordinates"]
    await ctx.send("Your (" + character + "'s) location is " + location)




"""
class maggot:

    attack = 3
    health = 4
    visibility = 10

    def __init__(self):


    def grunt(self):
        return 'A maggot is grunting'
"""

bot.run('OTk0MDI1MDk5MDAwODI3OTc4.G3xOD6.wlybF_3-ucjqNwlsPOfJN6hMbDGF2j5_wN9vfA')
