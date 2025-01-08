I didn't make any real effort to follow the right formatting when I made this project, so it's extremely bloated and unorganized. Most importantly though, everything works: I tested it recently to make sure.

It's a discord bot that I made a while ago, when I was learning python. It's a game where each user is a character in a cave, that can move around and pick up things. The cave is made of a set of squares where each has a character. The user sends commands to the discord chat to make his character take actions, including:

- Moving his character square by square
- Getting a map of the cave, but only the part that he had explored. The bot checks to see which squares have been explored, makes a unique pdf based on this info, and DMs the pdf to the user. full_map.png is an example of an image that the bot can generate.
- Viewing the cave: this command analyzes which squares can be seen by the user, based on the users location. Squares are either fully visible, partially visible, or not visible. map.png is a visual example of how this function works. This was definitely the most complex code in this program.
- Checking his inventory
- Picking up and dropping items into his square