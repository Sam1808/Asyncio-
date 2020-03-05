import asyncio
import curses
import random
import time
from curses_tools import draw_frame, read_controls, get_frame_size


SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

async def blink(canvas, row, column, symbol):
    while True:

        for tic in range(0, random.randint(0,20)): # for async stars blink
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for tic in range(0, 20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for tic in range(0, 3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for tic in range(0, 5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for tic in range(0, 3):
            await asyncio.sleep(0)

async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

async def animate_spaceship(canvas, # I do not understand why it`s blinking. I need help :?
                            row,
                            column,
                            frames,
                            max_ship_row_position,
                            max_ship_column_position):
    while True:
        for frame in frames:

            rows_direction, columns_direction, space_pressed = read_controls(canvas)

            row = row + rows_direction
            if row == max_ship_row_position:
                row = row - 1
            elif row == 1:
                row = row + 1

            column = column + columns_direction
            if column == max_ship_column_position:
                column = column - 1
            elif column == 1:
                column = column + 1

            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, frame, negative=True)
            await asyncio.sleep(0)


def draw(canvas, ship_frames):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    rows, columns = canvas.getmaxyx()
    max_row = rows -1
    max_column = columns-1
    stars_symbols = '+:.*'

    coroutines = []

    for star in range(0,100):
        row = random.randint(2, max_row-1) # let`s save place for border
        column = random.randint(2, max_column-1)
        coroutine = blink(canvas, row, column, random.choice(stars_symbols))
        coroutines.append(coroutine)

    center_row = int(max_row/2)
    center_column = int(max_column/2)

    coroutine = fire(canvas, center_row, center_column)
    coroutines.append(coroutine)

    frame_rows, frame_columns = get_frame_size(ship_frames[0])
    max_ship_row_position = max_row - frame_rows
    max_ship_column_position = max_column - frame_columns

    coroutine = animate_spaceship(canvas,
                                  center_row,
                                  center_column,
                                  ship_frames,
                                  max_ship_row_position,
                                  max_ship_column_position)
    coroutines.append(coroutine)

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)

        time.sleep(0.1)
        canvas.refresh()



if __name__=='__main__':

    ship_frames = []
    with open("animation/rocket_frame_1.txt", 'r') as file:
        frame_1 = file.read()
    ship_frames.append(frame_1)
    with open("animation/rocket_frame_2.txt", 'r') as file:
        frame_2 = file.read()
    ship_frames.append(frame_2)

    curses.update_lines_cols()
    curses.wrapper(draw, ship_frames)