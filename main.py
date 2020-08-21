import asyncio
import curses
import glob
import random
import time
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle, show_obstacles
from explosion import explode

     

EVENT_LOOP = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []
YEAR = 1957
GARBAGE_AMOUNT = None
CANNOT_BARREL = None
PHRASES = {

    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}

async def show_year(canvas, max_row, max_column):
    global YEAR
    global GARBAGE_AMOUNT
    global CANNOT_BARREL

    subwindow = canvas.derwin(max_row-3, int(max_column/1.5))
    

    while True:
        
        GARBAGE_AMOUNT = get_garbage_delay_tics(YEAR)

        if YEAR >= 2020:
            CANNOT_BARREL = True

        message = f'Current year: {YEAR}'
        subwindow.addstr(0,0, message)

        if YEAR in PHRASES.keys():
            space_event = f'{YEAR}: {PHRASES.get(YEAR)}'
            subwindow.addstr(1,0, space_event)

        subwindow.refresh()
        YEAR += 1 
        await sleep(15)

def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2

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
        for obstacle in OBSTACLES.copy():
            if obstacle.has_collision(row,column):
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                
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
                            max_ship_column_position,
                            game_over_logo):
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

        if space_pressed and CANNOT_BARREL:
            coroutine = fire(canvas, row, column+2) # cannon barrel per center
            EVENT_LOOP.append(coroutine)

        for frame in frames:
            draw_frame(canvas, row, column, frame)
            #await sleep(2) 
            await asyncio.sleep(0) # TODO: speed of ship
            draw_frame(canvas, row, column, frame, negative=True)
        
        for obstacle in OBSTACLES.copy():
            if obstacle.has_collision(row,column):
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                EVENT_LOOP.append(show_gameover(canvas,game_over_logo))
                return False
        
async def show_gameover(canvas, game_over_logo):
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(game_over_logo)
    row_position = rows_number/2 - frame_rows/2
    columns_position = columns_number/2 - frame_columns/2
    while True:
        draw_frame(canvas,row_position,columns_position,game_over_logo)
        await asyncio.sleep(0)

async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    while row < rows_number-frame_rows-3: # -3 to save the year info



        barrier = Obstacle(row, column, frame_rows,frame_columns)
        OBSTACLES.append(barrier)

        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)


        row += speed
        
        OBSTACLES.remove(barrier)

        if barrier in OBSTACLES_IN_LAST_COLLISIONS.copy():
            OBSTACLES_IN_LAST_COLLISIONS.clear()
            await explode(canvas, row, column)
            return False
        

async def fill_orbit_with_garbage(canvas,trash_basket,max_column):
    while True:
        
        if GARBAGE_AMOUNT:
            
            for garbage in trash_basket:
                _, frame_columns = get_frame_size(garbage)

                coroutine=fly_garbage(canvas, column=random.randint(2, max_column - frame_columns), garbage_frame=garbage)
                EVENT_LOOP.append(coroutine)
            
                await sleep(GARBAGE_AMOUNT)
        await sleep(1)





def draw(canvas, ship_frames, trash_basket, game_over_logo):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    rows, columns = canvas.getmaxyx()
    max_row = rows -1
    max_column = columns-1
    stars_symbols = '+:.*'

    for star in range(0,100):
        row = random.randint(2, max_row-3) # let`s save place for border and year
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
                                  max_ship_column_position,
                                  game_over_logo)
    
    EVENT_LOOP.append(coroutine)

    coroutine = show_year(canvas, max_row, max_column)
    EVENT_LOOP.append(coroutine)

    coroutine= fill_orbit_with_garbage(canvas,trash_basket,max_column)
    EVENT_LOOP.append(coroutine)


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

    with open("animation/game_over.txt", 'r') as file:
        game_over_logo = file.read()

    curses.update_lines_cols()
    curses.wrapper(draw, ship_frames, trash_basket, game_over_logo)