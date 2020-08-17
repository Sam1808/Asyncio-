import asyncio
import curses
import glob
import random
import time
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle, show_obstacles

EVENT_LOOP = []
OBSTACLES = []

async def sleep(tics=1):
    for tic in range(0, tics):
        await asyncio.sleep(0)

async def blink(canvas, offset_tics, row, column, symbol):
    while True:

        for tic in range(0, offset_tics):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)

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
        for obstacle in OBSTACLES:
            if obstacle.has_collision(row,column):
                return False

        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas,
                            row,
                            column,
                            frames,
                            max_ship_row_position,
                            max_ship_column_position):
    row_speed = column_speed = 0
    while True:

        rows_direction, columns_direction, space_pressed = read_controls(canvas)

        row = row + rows_direction
        column = column + columns_direction

        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        if row > max_ship_row_position-1:
            row = row - 1
        elif row < 2:
            row = row + 1
        else:
            row += row_speed

        if column > max_ship_column_position: # TODO: save the right|left border
            column = column - 1
        elif column < 1:
            column = column + 1
        else:
            column += column_speed

        if space_pressed:
            coroutine = fire(canvas, row, column+2) # cannon barrel per center
            EVENT_LOOP.append(coroutine)

        for frame in frames:
            draw_frame(canvas, row, column, frame)
            await sleep(2)
            draw_frame(canvas, row, column, frame, negative=True)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    while row < rows_number-frame_rows-1:

        barrier = Obstacle(row, column, frame_rows,frame_columns)
        OBSTACLES.append(barrier)

        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)


        row += speed

        OBSTACLES.remove(barrier)

async def fill_orbit_with_garbage(canvas,trash_basket,max_column):
    while True:
        for garbage in trash_basket:
            _, frame_columns = get_frame_size(garbage)

            coroutine=fly_garbage(canvas, column=random.randint(2, max_column - frame_columns), garbage_frame=garbage)
            EVENT_LOOP.append(coroutine)
            await sleep(len(trash_basket))

def draw(canvas, ship_frames, trash_basket):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    rows, columns = canvas.getmaxyx()
    max_row = rows -1
    max_column = columns-1
    stars_symbols = '+:.*'

    for star in range(0,100):
        row = random.randint(2, max_row-1) # let`s save place for border
        column = random.randint(2, max_column-1)
        offset_tics = random.randint(0, 20)
        coroutine = blink(canvas, offset_tics, row, column, random.choice(stars_symbols))
        EVENT_LOOP.append(coroutine)

    center_row = int(max_row/2)
    center_column = int(max_column/2)


    frame_rows, frame_columns = get_frame_size(ship_frames[0])
    max_ship_row_position = max_row - frame_rows
    max_ship_column_position = max_column - frame_columns

    coroutine = animate_spaceship(canvas,
                                  center_row,
                                  center_column,
                                  ship_frames,
                                  max_ship_row_position,
                                  max_ship_column_position)
    
    EVENT_LOOP.append(coroutine)

    coroutine= fill_orbit_with_garbage(canvas,trash_basket,max_column)
    EVENT_LOOP.append(coroutine)

    #coroutine = show_obstacles(canvas, OBSTACLES) to show obstacles
    #EVENT_LOOP.append(coroutine)

    while True:
        for coroutine in EVENT_LOOP.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                EVENT_LOOP.remove(coroutine)

        canvas.refresh()
        time.sleep(0.1)

if __name__=='__main__':

    ship_frames = []
    with open("animation/rocket_frame_1.txt", 'r') as file:
        frame_1 = file.read()
    ship_frames.append(frame_1)
    with open("animation/rocket_frame_2.txt", 'r') as file:
        frame_2 = file.read()
    ship_frames.append(frame_2)

    existed_files = set(glob.glob('animation/garbage/*', recursive=False))

    trash_basket = []
    for file_path in existed_files:
        with open(file_path, 'r') as file:
            garbage = file.read()
        trash_basket.append(garbage)


    curses.update_lines_cols()
    curses.wrapper(draw, ship_frames, trash_basket)