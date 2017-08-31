#!/usr/bin/env python

# ============================== Global Variable Definition and Importing ==============================

# Uses the curses python lib to allow for fancy terminal drawing
import curses
# Uses what is time?
import time
# Might make this thread idk
import threading
# Imports option parser so that I can use command line flags. Thanks Harrison!
import click
import os

# Imports curses wrapper so that exceptions will cause curses to exit instead of hanging, very useful in debug
from curses import wrapper
# Imports textpad, I used this during testing
from curses import textpad

# Sets up command line parser
@click.command()
# Grabs flags from command line args
@click.option("--p1latency",
             type=int,
             default=10,
             help="Defines the baseline latency for player 1 in ms. Default 10" )
@click.option("--p2latency",
             type=int,
             default=10,
             help="Defines the baseline latency for player 2 in ms. Default 2" )
@click.option("--p1variance",
             type=int,
             default=10,
             help="Defines the latency variance range for player 1. Default 10" )
@click.option("--p2variance",
             type=int,
             default=10,
             help="Defines the latency variance range for player 2. Default 10" )
@click.option("--p1packet",
             type=int,
             default=2,
             help="Defines the packet loss chance player 1. Default 2" )
@click.option("--p2packet",
             type=int,
             default=2,
             help="Defines  the packet loss chance player 2. Default 2" )
@click.option("--tickrate",
             type=int,
             default=60,
             help="Defines the server tick rate. Default 60" )
@click.option("--maxkills",
             type=int,
             default=10,
             help="Defines the max kills until 'game' end. Default 10" )

# =====================================================================================================
# ========================================== Function Calls ===========================================
# =====================================================================================================

# ========================================== Initialization ===========================================

# Main function, fires off all other setup functions, starts the simulation
def main(**kwargs):
    # Grabs the command line args
    global p1latency, p2latency, p1variance, p2variance, p1packet, p2packet, tickrate, maxkills
    p1latency = kwargs["p1latency"]
    p2latency = kwargs["p2latency"]
    p1variance = kwargs["p1variance"]
    p2variance = kwargs["p2variance"]
    p1packet = kwargs["p1packet"]
    p2packet = kwargs["p2packet"]
    tickrate = kwargs["tickrate"]
    maxkills = kwargs["maxkills"]

    wrapper(start_program)

def start_program(stdscr):
    # Allow things to appear at all
    window_init(stdscr)

    # Draw the words for labeling
    server_init(stdscr)

    # Create stats
    stats_init(stdscr)

    # Fire off the server loop cycle
    player_init(stdscr)

    # Closes on keypress
    stdscr.getch()

# ========================================== Init Functions ===========================================

# Sets up the window divisions for the "game"
def window_init(stdscr):
    # Defines the variables as global
    global winsplitdist, winheight, winwidth

    stdscr.clear()

    # Grabs terminal dimensions
    winheight = curses.LINES
    winwidth  = curses.COLS

    # Draws a border around the whole window
    stdscr.border(0)

    # Splits the window into 3 equal parts
    winsplitdist = winwidth / 3
    stdscr.vline(0, winsplitdist, "|", winheight)
    stdscr.vline(0, (winsplitdist * 2), "|", winheight)

    # Leaves space for stat tracking
    stdscr.hline((winheight - 10), 0,"-", winwidth)

    # Refreshes the draw window
    stdscr.refresh()

# Paints on labels
def server_init(stdscr):
    # Writes header labels
    stdscr.addstr(3, ((winsplitdist / 2)), "Client 1")
    stdscr.addstr(3, (winsplitdist + (winsplitdist / 2)), "Server")
    stdscr.addstr(3, ((winsplitdist * 2) + (winsplitdist / 2)), "Client 2")

    # Writes stat labels
    stdscr.addstr((winheight - 9), (winsplitdist + (winsplitdist / 2)), "- Current Tick")

    stdscr.addstr((winheight - 8), ((winsplitdist / 2)), "- K/D")
    stdscr.addstr((winheight - 8), (winsplitdist + (winsplitdist / 2)), "- Tick Rate")
    stdscr.addstr((winheight - 8), ((winsplitdist * 2) + (winsplitdist / 2)), "- K/D")

    stdscr.addstr((winheight - 7), ((winsplitdist / 2)), "- Ping")
    stdscr.addstr((winheight - 7), (winsplitdist + (winsplitdist / 2)), "- C1 Packets Lost")
    stdscr.addstr((winheight - 7), ((winsplitdist * 2) + (winsplitdist / 2)), "- Ping")

    stdscr.addstr((winheight - 6), ((winsplitdist / 2)), "- Kills Missed")
    stdscr.addstr((winheight - 6), (winsplitdist + (winsplitdist / 2)), "- C2 Packets Lost")
    stdscr.addstr((winheight - 6), ((winsplitdist * 2) + (winsplitdist / 2)), "- Kills Missed")

# Create statistics and statistics labels
def stats_init(stdscr):
    # Declare as global
    global c1kills, c1deaths, c1ping, c1killmiss
    global c2kills, c2deaths, c2ping, c2killmiss
    global tickrate, c1packetloss, c2packetloss

    # Define them
    c1kills = 0
    c2kills = 0

    c1deaths = 0
    c2deaths = 0

    c1ping = 0
    c2ping = 0

    c1killmiss = 0
    c2killmiss = 0

    c1packetloss = 0
    c2packetloss = 0

# Tells the players where to be at the start
def player_init(stdscr):
    global p1slocation, p2slocation
    global p1c1location, p2c1location
    global p1c2location, p2c2location

    # Client1 locations
    p1c1location = (winsplitdist / 3)
    p2c1location = ((winsplitdist / 3) * 2)
    # Server locations
    p1slocation = (winsplitdist / 3) + winsplitdist
    p2slocation = ((winsplitdist / 3) * 2) + winsplitdist
    # Client2 locations
    p1c2location = (winsplitdist / 3) + (winsplitdist * 2)
    p2c2location = ((winsplitdist / 3) * 2) + (winsplitdist * 2)

    # Draws the initial server tick
    draw_tick(stdscr)

# ======================================== Client Functions ===========================================


# ====================================== Running and Drawing ==========================================
# Every server tick, the entire screen needs to refresh.
def draw_tick(stdscr):
    # Draws serverplayer1
    stdscr.vline(8, p1slocation, "|", 3)
    stdscr.vline(8, p1slocation + 4, "|", 3)
    stdscr.hline(8, p1slocation, "-", 5)
    stdscr.hline(11, p1slocation, "-", 5)
    # Draws serverplayer2
    stdscr.vline(winheight - 23, p2slocation, "|", 3)
    stdscr.vline(winheight - 23, p2slocation + 4, "|", 3)
    stdscr.hline(winheight - 23, p2slocation, "-", 5)
    stdscr.hline(winheight - 20, p2slocation, "-", 5)

    # Draws client1player1
    stdscr.vline(8, p1c1location, "|", 3)
    stdscr.vline(8, p1c1location + 4, "|", 3)
    stdscr.hline(8, p1c1location, "-", 5)
    stdscr.hline(11, p1c1location, "-", 5)
    # Draws client1player2
    stdscr.vline(winheight - 23, p2c1location, "|", 3)
    stdscr.vline(winheight - 23, p2c1location + 4, "|", 3)
    stdscr.hline(winheight - 23, p2c1location, "-", 5)
    stdscr.hline(winheight - 20, p2c1location, "-", 5)

    # Draws client2player1
    stdscr.vline(8, p1c2location, "|", 3)
    stdscr.vline(8, p1c2location + 4, "|", 3)
    stdscr.hline(8, p1c2location, "-", 5)
    stdscr.hline(11, p1c2location, "-", 5)
    # Draws client2player2
    stdscr.vline(winheight - 23, p2c2location, "|", 3)
    stdscr.vline(winheight - 23, p2c2location + 4, "|", 3)
    stdscr.hline(winheight - 23, p2c2location, "-", 5)
    stdscr.hline(winheight - 20, p2c2location, "-", 5)

    update_stats(stdscr)

    # Refreshes the draw window
    stdscr.refresh()

# Every tick, needs to update the bottom row stats
def update_stats(stdscr):
    # Updates the stats printed
    stdscr.addstr((winheight - 9), (winsplitdist + (winsplitdist / 2) - 5), str(0))

    stdscr.addstr((winheight - 8), ((winsplitdist / 2) - 9), str(c1kills))
    stdscr.addstr((winheight - 8), ((winsplitdist / 2) - 7), "/")
    stdscr.addstr((winheight - 8), ((winsplitdist / 2) - 5), str(c1deaths))
    stdscr.addstr((winheight - 8), (winsplitdist + (winsplitdist / 2) - 5), str(tickrate))
    stdscr.addstr((winheight - 8), ((winsplitdist * 2) + (winsplitdist / 2) - 9), str(c2kills))
    stdscr.addstr((winheight - 8), ((winsplitdist * 2) + (winsplitdist / 2) - 7), "/")
    stdscr.addstr((winheight - 8), ((winsplitdist * 2) + (winsplitdist / 2) - 5), str(c2deaths))

    stdscr.addstr((winheight - 7), ((winsplitdist / 2) - 5), str(c1ping))
    stdscr.addstr((winheight - 7), (winsplitdist + (winsplitdist / 2) - 5), str(c1packetloss))
    stdscr.addstr((winheight - 7), ((winsplitdist * 2) + (winsplitdist / 2) - 5), str(c2ping))

    stdscr.addstr((winheight - 6), ((winsplitdist / 2) - 5), str(c1killmiss))
    stdscr.addstr((winheight - 6), (winsplitdist + (winsplitdist / 2) - 5), str(c2packetloss))
    stdscr.addstr((winheight - 6), ((winsplitdist * 2) + (winsplitdist / 2) - 5), str(c2killmiss))

    # Refreshes the draw window
    stdscr.refresh()


# ====================================== Starts This Bad Boy ==========================================
# Calls the function, starts the program
if __name__ == "__main__":
    main()
