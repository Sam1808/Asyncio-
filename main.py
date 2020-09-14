import asyncio
import curses
import glob
import random
import time
from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle, show_obstacles
from explosion import explode

game_coroutines = []
obstacles = []
obstacles_in_last_collisions = []
year = 1957

async def show_year(canvas, max_row, max_column): # To show year & events, triggers for garbage amount
    global year

    phrases = {
        1957: "First Sputnik",
        1961: "Gagarin flew!",
        1969: "Armstrong got on the moon!",
        1971: "First orbital space station Salute-1",
        1981: "Flight of the Shuttle Columbia",
        1998: 'ISS start building',
        2011: 'Messenger launch to Mercury',
        2020: "Take the plasma gun! Shoot the garbage!",
    }

    subwindow = canvas.derwin(max_row-3, int(max_column/1.5))
    
    while True:
        
        message = f'Current year: {year}'
        subwindow.addstr(0,0, message)

        if year in phrases.keys():
            space_event = f'{year}: {phrases.get(year)}'
            subwindow.addstr(1,0, space_event)

        subwindow.refresh()
        await sleep(15)
        year += 1

async def sleep(tics=1):
    for tic in range(0, tics):
        await asyncio.sleep(0)

async def blink(canvas, offset_tics, row, column, symbol):
    while True:

        await sleep(offset_tics)

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

    while 1 < row < max_row and 0 < column < max_column: # from first row to save border
        for obstacle in obstacles.copy():
            if obstacle.has_collision(row,column):
                obstacles_in_last_collisions.append(obstacle)
                
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

        if row > max_ship_row_position-1: # save the header|footer border
            row = row - 1
        elif row < 2:
            row = row + 1
        else:
            row += row_speed

        if column > max_ship_column_position-1: # save the right|left border
            column = column - 1
        elif column < 1:
            column = column + 1
        else:
            column += column_speed


        if space_pressed and year >= 2020: # enable cannon after 2020 year
            coroutine = fire(canvas, row, column+2)  # cannon per center
            game_coroutines.append(coroutine)

        for frame in frames:
            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0) # more smoother then await sleep(2) 
            draw_frame(canvas, row, column, frame, negative=True)
        
        frame_rows, frame_columns = get_frame_size(frames[0])
        
        for obstacle in obstacles.copy():
            if obstacle.has_collision(row,column,frame_rows,frame_columns):
                obstacles_in_last_collisions.append(obstacle)
                game_coroutines.append(show_gameover(canvas,game_over_logo))
                return False
        
async def show_gameover(canvas, game_over_logo):
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(game_over_logo)
    
    row_position = (rows_number - frame_rows)/2
    column_position = (columns_number - frame_columns)/2
    
    while True:
        draw_frame(canvas,row_position,column_position,game_over_logo)
        await asyncio.sleep(0)

async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    barrier = Obstacle(row, column, frame_rows, frame_columns)
    obstacles.append(barrier)

    while row < rows_number-frame_rows-3: # -3 to save the year info

        barrier.row = row

        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)

        row += speed

        if barrier in obstacles_in_last_collisions.copy():
            obstacles_in_last_collisions.clear()
            await explode(canvas, row, column)
            return False
    
    obstacles.remove(barrier)


async def fill_orbit_with_garbage(canvas,trash_basket,max_column):
    
    while True:
        garbage_amount = get_garbage_delay_tics(year)
        
        if garbage_amount:
            for garbage in trash_basket:
                _, frame_columns = get_frame_size(garbage)

                coroutine=fly_garbage(canvas, column=random.randint(2, max_column - frame_columns), garbage_frame=garbage)
                game_coroutines.append(coroutine)
            
                await sleep(garbage_amount)
        
        await asyncio.sleep(0)


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
        game_coroutines.append(coroutine)

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
    game_coroutines.append(coroutine)

    coroutine= fill_orbit_with_garbage(canvas,trash_basket,max_column)
    game_coroutines.append(coroutine)

    coroutine = show_year(canvas, max_row, max_column)
    game_coroutines.append(coroutine)

    while True:
        
        for coroutine in game_coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                game_coroutines.remove(coroutine) 
        
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
