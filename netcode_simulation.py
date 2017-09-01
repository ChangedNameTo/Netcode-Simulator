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
# Imports the ability for random numbers
from random import randint

# Sets up command line parser
@click.command()
# Grabs flags from command line args
@click.option("--c1latency",
             type=int,
             default=10,
             help="Defines the baseline latency for player 1 in ms. Default 10" )
@click.option("--c2latency",
             type=int,
             default=10,
             help="Defines the baseline latency for player 2 in ms. Default 2" )
@click.option("--c1variance",
             type=int,
             default=10,
             help="Defines the latency variance range for player 1. Default 10" )
@click.option("--c2variance",
             type=int,
             default=10,
             help="Defines the latency variance range for player 2. Default 10" )
@click.option("--c1packet",
             type=int,
             default=2,
             help="Defines the packet loss chance player 1. Default 2" )
@click.option("--c2packet",
             type=int,
             default=2,
             help="Defines  the packet loss chance player 2. Default 2" )
@click.option("--tickrate",
             type=int,
             default=60,
             help="Defines the server tick rate. Default 60. Use numbers that evenly divide 60." )
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
    global c1latency, c2latency, c1variance, c2variance, c1packet, c2packet, tickrate, maxkills
    c1latency = kwargs["c1latency"]
    c2latency = kwargs["c2latency"]
    c1variance = kwargs["c1variance"]
    c2variance = kwargs["c2variance"]
    c1packet = kwargs["c1packet"]
    c2packet = kwargs["c2packet"]
    tickrate = 60 / kwargs["tickrate"]
    maxkills = kwargs["maxkills"]

    wrapper(start_program)

def start_program(stdscr):
    # Allow things to appear at all
    window_init(stdscr)

    draw_screen(stdscr)

    # Starts the game
    run_game(stdscr)

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

    # Splits the window into 3 equal parts
    winsplitdist = winwidth / 3

# Paints on labels
def server_init(stdscr):
    global c1packetstack, c2packetstack

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

    # Creates the stacks for packets because I am dumb and didn't make this OO from the start
    # Packet structure is a tuple containing the newly updated position of the local player and whether
    # or not they shot
    c1packetstack = []
    c2packetstack = []

# Create statistics and statistics labels
def stats_init(stdscr):
    # Declare as global for all static stacks
    global c1kills, c1deaths, c1ping, c1killmiss
    global c2kills, c2deaths, c2ping, c2killmiss
    global tickrate, c1packetloss, c2packetloss
    global servertick, looptick
    global nextservertick, nextc1packet, nextc2packet

    # Define them
    c1kills        = 0
    c2kills        = 0

    c1deaths       = 0
    c2deaths       = 0

    c1ping         = 0
    c2ping         = 0

    c1killmiss     = 0
    c2killmiss     = 0

    c1packetloss   = 0
    c2packetloss   = 0

    servertick     = 0
    looptick       = 0

    nextservertick = 0
    nextc1packet   = 0
    nextc2packet   = 0

# Tells the players where to be at the start
def player_init(stdscr):
    global p1slocation, p2slocation
    global p1c1location, p2c1location
    global p1c2location, p2c2location

    # Client1 locations
    p1c1location = (winsplitdist / 3)
    p2c1location = (winsplitdist / 3)
    # Server locations
    p1slocation = (winsplitdist / 2) + winsplitdist
    p2slocation = (winsplitdist / 2) + winsplitdist
    # Client2 locations
    p1c2location = (winsplitdist / 3) + (winsplitdist * 2)
    p2c2location = (winsplitdist / 3) + (winsplitdist * 2)

# Redraws lines after the first tick
def redraw_lines(stdscr):
    stdscr.border(0)
    stdscr.vline(0, winsplitdist, "|", winheight)
    stdscr.vline(0, (winsplitdist * 2), "|", winheight)
    stdscr.hline((winheight - 10), 0,"-", winwidth)

# I realized later that I should have done this in a OOP style too late, so this is an ugly loop
# Infact, everything will be ugly. Whoops.
# ======================================== Client Functions ===========================================
def player_move(stdscr):
    global p1c1location, p2c2location

    # Loops while looking for valid moves
    valid = False
    while(not valid):
        # Introduces more variance so that these two actually shoot at each other eventually
        num = randint(1,3)
        movelen = randint(-1, 1)
        combo = num * movelen
        if(p1c1location + combo > 0 and p1c1location + combo < winwidth):
            p1c1location = p1c1location + combo
            valid = True

    # Moves p2c2 now
    valid = False
    while(not valid):
        # Introduces more variance so that these two actually shoot at each other eventually
        num = randint(1,3)
        movelen = randint(-1, 1)
        combo = num * movelen
        if(p2c2location + combo > 0 and p2c2location + combo < winwidth):
            p2c2location = p2c2location + combo
            valid = True

# When c1 sends a packet, uses random variance to decide when the next client packet is sent
def c1_update_ping():
    global c1variance
    global c1ping
    global nextc1packet
    global looptick

    num = randint(0, c1variance)
    c1ping = c1latency + (num * randint(-1, 1))
    nextc1packet = looptick + c1ping

def c2_update_ping():
    global c2variance
    global c2ping
    global nextc1packet
    global looptick

    num = randint(0, c2variance)
    c2ping = c2latency + (num * randint(-1, 1))
    nextc2packet = looptick + c2ping

# Appends the commands to the back of the packet stacks that the server pulls off of
def c1_send_packet(stdscr):
    c1packetstack = tuple([p1c1location, p1_shoot_logic()])

def c2_send_packet(stdscr):
    c2packetstack = tuple([p2c2location, p2_shoot_logic()])

# Checks if the center of player is in front of anywhere on the p1 "hitbox", draws a line if it is
def p1_shoot_logic():
    # If valid returns true and calls the shot draw
    if((p1c1location + 3) <= (p2c1location + 5) and (p1c1location + 3) >= (p2c1location)):
        return True
    else:
        return False

def p2_shoot_logic():
    # If valid returns true and calls the shot draw
    return True
    if((p2c2location + 3) <= (p1c2location + 5) and (p2c2location + 3) >= (p1c2location)):
        return True
    else:
        return False

# Shots can be drawn in 3 seperate areas that are all distinct from each other. The section param checks which place to draw
def p1_shoot_draw(stdscr, section):
    stdscr.addstr(2, 1, "p1 shoot")
    stdscr.refresh()
    if(section == 1):
        stdscr.vline(11, p1c1location + 3, "v", 7)
    elif(section == 2):
        stdscr.vline(11, p1slocation + 3, "v", 7)
    else:
        stdscr.vline(11, p1c2location + 3, "v", 7)
    stdscr.refresh()

def p2_shoot_draw(stdscr, section):
    stdscr.addstr(3, 1, "p2 shoot")
    stdscr.refresh()
    if(section == 1):
        stdscr.vline(winheight - 23, p2c1location + 3, "^", 7)
    elif(section == 2):
        stdscr.vline(winheight - 23, p2slocation + 3, "^", 7)
    else:
        stdscr.vline(winheight - 23, p2c2location + 3, "^", 7)
    stdscr.refresh()


# Handles server packet management, distributing kills fairly, and handling game state conflicts
# ======================================== Server Functions ===========================================
# If the server has entered a server tick state, then it needs to process the packets that it has currently
# recieved, update the game state, then distribute packets back to each client so that they can sync state
def server_send_packets(stdscr):
    return 1

# ====================================== Running and Drawing ==========================================
# Initial screen draw on load
def draw_screen(stdscr):
    stdscr.clear()
    # Draw the words for labeling
    server_init(stdscr)
    # Create stats
    stats_init(stdscr)
    # Fire off the server loop cycle
    player_init(stdscr)
    # Redraws guide lines
    redraw_lines(stdscr)
    # Draws the server tick
    draw_tick(stdscr)

# Redraws things that need to be redrawn
def redraw_screen(stdscr):
    stdscr.clear()
    # Redraws guide lines
    redraw_lines(stdscr)
    # Redraws the labels
    server_init(stdscr)
    # Draws the server tick
    draw_tick(stdscr)

# This function is the actual running code. What this does is it has an arbitrary number that counts
# up called the "loop tick", because it's very difficult for me to simulate actual server ticks.
def run_game(stdscr):
    # Grabs all of the global vars needed
    global c1kills, c2kills
    global looptick, servertick
    global maxkills

    while(c1kills <= maxkills and c2kills <= maxkills):
        # Move each player
        player_move(stdscr)

        # Each client decides whether or not to shoot based on if there is a target to hit in front of them
        p1_shoot_draw(stdscr, 1)
        if(p1_shoot_logic()):
            stdscr.addstr(2, 1, "p1 shoot")
            p1_shoot_draw(stdscr, 1)
        if(p2_shoot_logic()):
            p2_shoot_draw(stdscr, 3)

        if(nextservertick == looptick):
            server_send_packets(stdscr)

        if(nextc1packet == looptick):
            c1_send_packet(stdscr)
            c1_update_ping()

        if(nextc2packet == looptick):
            c2_send_packet(stdscr)
            c2_update_ping()

        redraw_screen(stdscr)
        time.sleep(0.3)
        looptick = looptick + 1
        c1kills = c1kills + 1

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
    stdscr.addstr((winheight - 9), (winsplitdist + (winsplitdist / 2) - 5), str(servertick))

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

    stdscr.addstr(1, 1, str(looptick))

    # Refreshes the draw window
    stdscr.refresh()

# ====================================== Starts This Bad Boy ==========================================
# Calls the function, starts the program
if __name__ == "__main__":
    main()
