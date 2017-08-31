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
# =====================================================================================================
# ========================================== Function Calls ===========================================
# =====================================================================================================

# ========================================== Initialization ===========================================
# Main function, fires off all other setup functions, starts the simulation
def main(**kwargs):
    wrapper(start_program)

def start_program(stdscr):
    window_init(stdscr)

    # Closes on keypress
    stdscr.getch()

# Sets up the window divisions for the "game"
def window_init(stdscr):
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

    # Refreshes the draw window
    stdscr.refresh()


# ====================================== Running and Drawing ==========================================
# Every server tick, the entire screen needs to refresh.
def draw_tick():
    print()

# ====================================== Starts This Bad Boy ==========================================
# Calls the function, starts the program
if __name__ == "__main__":
    main()
