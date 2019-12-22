from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from shutil import copyfile
from statistics import mean
from sys import argv

import json
import math
import os 

import plotly
from plotly.graph_objs import Scatter, Layout, Figure
from plotly.subplots import make_subplots

N_MEAN = 7
N_DAYS = 21
INCHES = 72

NAME_MAP = {
    'w': 'weight',
    'm': 'minutes',
    's': 'amount',
    'h': 'heart' 
}

FILENAME = None

COLOR = True

LINE = '\033[4m'
END = '\033[0m'
UP = '\033[1A'

def update_colors():
    global BOLD, LIGHT, RED, BLUE, GREEN, YELLOW, CYAN

    BOLD = '\033[1m' if COLOR else ''
    LIGHT = '\033[2m' if COLOR else ''
    RED = '\033[1;91m' if COLOR else ''
    BLUE = '\033[1;94m' if COLOR else ''
    GREEN = '\033[1;92m' if COLOR else ''
    YELLOW = '\033[1;93m' if COLOR else ''
    CYAN = '\033[1;96m' if COLOR else ''


top_info = ''
last_error = False
json_data = None
old_json = []
state_change = False
current_date = datetime.now()

def add_list_item(key, value):
    date = current_date_str()
    if date not in json_data[key]:
        json_data[key][date] = []
    json_data[key][date].append(value)
    save_json()

    
def get_amount():
    global top_info 
    global last_error

    amount = input('Amount: $')
    if not amount:
        return 
    dot_pos = amount.find('.')
    if dot_pos == -1:
        dollar = amount
        cents = '00'
    else:
        dollar = amount[0:dot_pos]
        cents = amount[dot_pos+1:]

    if dollar.isdigit() and cents.isdigit() and len(cents) == 2:
        dollar = int(dollar)
        cents = int(cents)
        amount = dollar + cents/100
    else:
        top_info = f'Invalid amount: ${amount}'
        last_error = True
        view_all()
        return

    return amount 

def set_heart():
    global top_info
    global last_error

    systolic = input('Systolic: ')
    if not systolic:
        view_all()
        return
    if systolic.isdigit():
        systolic = int(systolic)
    else:
        top_info = f'Invalid systolic: ${systolic}'
        last_error = True
        view_all()
        return

    diastolic = input('Diastolic: ')
    if not diastolic:
        return
    if diastolic.isdigit():
        diastolic = int(diastolic)
    else:
        top_info = f'Invalid diastolic: ${diastolic}'
        last_error = True

    pulse = input('Pulse: ')
    if not pulse:
        return
    if pulse.isdigit():
        pulse = int(pulse)
    else:
        top_info = f'Invalid pulse: ${pulse}'
        last_error = True

    date = current_date_str()
    json_data['heart'][date] = {'systolic': systolic, 'diastolic': diastolic, 'pulse': pulse}
    save_json()
    top_info = f'Heart: {systolic}/{diastolic} {pulse}'
    view_all()


def add_spending():
    amount = get_amount()
    if not amount:
        view_all()
        return 
    add_list_item('amount', amount)    
    global top_info
    top_info = f'Amount: ${amount:0.02f}'
    view_all()


def set_minutes():
    global top_info
    global json_data
    global last_error
    minutes = input('Minutes: ')
    if not minutes:
        view_all()
        return
    if minutes.isdigit():
        minutes = int(minutes)
    else:
        top_info = f'Invalid minutes: {minutes}'
        last_error = True
        view_all()
        return

    date = current_date_str()
    json_data['minutes'][date] = minutes
    save_json() 
    top_info = f'Minutes: {minutes}'
    view_all()

def set_weight():
    global top_info
    global json_data
    global last_error
    
    weight = input('Weight: ')
    if not weight:
        view_all()
        return
    
    dot_pos = weight.find('.')
    if dot_pos == -1:
        value = weight
        fraction = '0'
    else:
        value = weight[0:dot_pos]
        fraction = weight[dot_pos+1:]
    
    if value.isdigit() and fraction.isdigit() and len(fraction) == 1:
        weight = float(value) + float(fraction)/10.0
    else:
        top_info = f'Invalid weight: {weight}'
        last_error = True
        view_all()
        return

    date = current_date_str()
    json_data['weight'][date] = weight
    save_json() 
    top_info = f'Weight: {weight}'
    view_all()


def get_weighted_mean(list):
    global N_MEAN
    
    weight_sum = 0
    weights = [1, 3, 6, 10, 15, 21, 28]
    sum = 0
    for idx in range(len(list)):
        weight_sum += weights[idx]
        sum += list[idx] * weights[idx]
    return sum / weight_sum 


def view_all():
    global top_info
    global current_date
    global N_MEAN

    print('\033[2J\033[0;0f')
    print(f'{END}Date         Weight          Minutes     Spending')
    
    weight_list = []
    minutes_list = []
    amount_list = []

    today = datetime.now()
     
    for delta in range(N_DAYS, 0, -1):
        raw_day = today - timedelta(days=delta-1)
        day = get_date_str(raw_day)
        nice_day = get_nice_date_str(raw_day)

        # weight
        if day in json_data['weight']:
            weight = float(json_data['weight'][day])
            weight_list.append(weight)
            while len(weight_list) > N_MEAN:
                weight_list.pop(0)
            mean_value = get_weighted_mean(weight_list)     
            weight = f'{weight:0.1f}'
            mean_value = f'{LIGHT}{mean_value:0.1f}{END}'
        else:
            weight = '     '
            mean_value = '     '
        
        # amount
        amount_sum = 0
        if day in json_data['amount']:
            for amount in json_data['amount'][day]:
                amount_sum += amount
        amount_list.append(amount_sum)
        while len(amount_list) > N_MEAN:
            amount_list.pop(0)
        amount_mean = get_amount_str(get_weighted_mean(amount_list))
        amount_sum = get_amount_str(amount_sum)

        # minutes
        if day in json_data['minutes']:
            minutes = float(json_data['minutes'][day])
            minutes = int(f'{minutes:0.0f}')
        else:
            minutes = 0
        minutes_list.append(minutes)
        while len(minutes_list) > N_MEAN:
            minutes_list.pop(0)
        mean_minutes = get_weighted_mean(minutes_list)
        mean_minutes = f'{mean_minutes:0.0f}'.rjust(3)
        minutes = f'{minutes:0.0f}'.rjust(3) if minutes > 0 else '   '

        # heart
        if day in json_data['heart']:
            item = json_data['heart'][day]
            systolic = item['systolic']
            diastolic = item['diastolic']
            pulse = item['pulse']
            heart = f'{systolic}/{diastolic} {pulse}'
        else:
            heart = ''

        # row 
        format = f'' if \
            get_date_str(current_date) == get_date_str(raw_day) \
            else f'{LIGHT}'
        print(f'{format}{nice_day}{END}   '
            f'{BOLD}{weight}  '
            f'{mean_value}{END}   '
            f'{YELLOW}{minutes}  '
            f'{LIGHT}{mean_minutes}{END}   '
            f'{GREEN}{amount_sum}  '
            f'{LIGHT}{amount_mean}{END}   '
            f'{RED}{heart}{END}')


def get_date():
    global last_error
    global top_info
    global current_date

    today = datetime.now()
    month = input('Month: ')
    if not month:
        month = int(current_date.strftime('%-m'))
        print(f'{UP}Month: {month}')
    elif not(month.isdigit()) or int(month) < 1 or int(month) > 12:
        top_info = f'Invalid month: {month}'
        last_error = True
        view_all()
        return
    else:
        month = int(month)
    
    day = input('Day: ')
    if not day:
        day = int(current_date.strftime('%-d'))
        print(f'{UP}Day: {day}')
    elif not(day.isdigit()) or int(day) < 1 or int(day) > 31:
        top_info = f'Invalid day: {day}'
        last_error = True
        view_all()
        return
    else:
        day = int(day)

    year = input('Year: ')
    if not year:
        year = int(current_date.strftime('%y'))
        print(f'{UP}Year: {year}')
    elif not(year.isdigit()) or int(year) < 19 or int(year) > 99:
        top_info = f'Invalid year: {year}'
        last_error = True
        view_all()
        return
    else:    
        year = int(year)

        
    try:
        result = datetime(year+2000, month, day)
        return result

    except ValueError:
        top_info = f'Invalid date: {month}/{day}/{year}'
        last_error = True
        view_all()
        return


def set_date():
    global current_date
    global top_info
    
    new_date = get_date()
    if not new_date:
        view_all()
        return    

    current_date = new_date
    top_info = f'Date: {get_nice_date_str(current_date)}'
    view_all()


def get_date_str(date):
    return date.strftime('%m/%d/%y')


def get_nice_date_str(date):
    return date.strftime('%a %b %d')


def current_date_str():
    global current_date
    return get_date_str(current_date)


def get_amount_str(amount):
    negative = False
    if amount < 0:
        negative = True
        amount *= -1

    return RED + f'-${amount:0,.02f}'.rjust(8) + END if negative \
        else f'${amount:0,.02f}'.rjust(8) 
    

def load_json():
    global json_data
    global COLOR
    global N_DAYS
    global N_MEAN

    try:
        with open(FILENAME, 'r') as fp:
            json_data = json.load(fp)
        
        if 'color' not in json_data:
            json_data['color'] = COLOR
        COLOR = True if json_data['color'] else False
        
        if 'n_days' not in json_data:
            json_data['n_days'] = N_DAYS
        N_DAYS = int(json_data['n_days'])

        if 'n_mean' not in json_data:
            json_data['n_mean'] = N_MEAN
        N_MEAN = int(json_data['n_mean'])
    
        save_json()

    except FileNotFoundError:
        print('Error: no such file {FILENAME}')
        exit(-1)


def save_json():
    global json_data
    global state_change

    with open(FILENAME, 'w') as fp:
        json.dump(json_data, fp)
    state_change = True


def parse_date(date):
    n = date.find('/')
    month = int(date[0:n])
    date = date[n+1:]
    n = date.find('/')
    day = int(date[0:n])
    year = 2000 + int(date[n+1:])
    return datetime(year, month, day)


def get_command():
    global last_error
    global top_info
    global current_date
    global N_DAYS
    
    format = RED if last_error else YELLOW
    date_str = get_nice_date_str(current_date)
    N = len(date_str) + 5
    str = f'\n{BOLD}{date_str}{END}  $ ' \
          f'\n{format}{top_info}{END}\033[{N_DAYS+4};{N}f{BOLD}{END}' 
    top_info = ''
    last_error = False
    return input(str)


def toggle_color():
    global COLOR
    
    COLOR = not COLOR
    json_data['color'] = COLOR
    save_json()
    update_colors()
    view_all()    


def undo_last():
    global top_info
    global last_error
    global old_json
    global json_data
    
    if old_json:
        json_data = old_json[-1]['json']
        operation = old_json[-1]['name']
        old_json.pop()
        top_info = f'Undo {operation}'
        view_all()
    else:
        top_info = 'Error: No operation'
        last_error = True
        view_all()


def view_commands():
    global top_info

    top_info = f'{END}' \
               f'{LINE}m{END}inutes  ' \
               f'{LINE}s{END}pending  ' \
               f'{LINE}w{END}eight  ' \
               f'{LINE}h{END}eart  ' \
               f'{LINE}d{END}ate  ' \
               f'{LINE}c{END}olor  ' \
               f'{LINE}u{END}ndo  ' \
               f'{LINE}q{END}uit' 
    view_all()


def main():
    global top_info
    global state_change
    global json_data
    global old_json
    global last_error

    load_json()
    update_colors()

    command_map = {
        'c': toggle_color,
        's': add_spending,
        'm': set_minutes,
        'w': set_weight,
        'h': set_heart,
        'd': set_date,
        'u': undo_last
    }

    view_all()

    done = False
    while not done:
        raw_command = get_command()
        command = raw_command.lower()
        
        print('\033[K', end='')

        if command == 'q':
            done = True
        
        elif not command:
            view_commands()
        
        elif command in command_map:
            last_json = deepcopy(json_data)
            print(f'{BOLD}', end='')
            command_map[command]()
            if state_change:
                old_json.append({'json': last_json, 'name': top_info})
            state_change = False        
        

        else:
            top_info = f'No such command: {raw_command}'
            last_error = True
            view_all()
   
 
def add_one_value(name, value): 
    try:
        value = float(value)

    except ValueError:
        print(f'Invalid {name}: {value}')
        exit(-1)

    global json_data
    date = current_date_str()
    if name == 'amount':
        if date not in json_data[name]:
            json_data[name][date] = []
        json_data[name][date].append(value)
    else:
        json_data[name][date] = value
    save_json()
    view_all()
    print(f'\n{name}: {value}')


def add_one(option, value):
    global NAME_MAP

    if option not in NAME_MAP:
        print(f'No such option: {option}')
        exit(-1)

    load_json()
    update_colors()
    add_one_value(NAME_MAP[option], value)


def plot_weight():
    global json_data
    load_json()
    
    print('Start Date')
    start = get_date()
    start_str = get_date_str(start)
    print('\nEnd Date')
    end = get_date() 
    end_str = get_date_str(end)

    mean_wt = []
    x = []
    y1 = []

    while get_date_str(start) != get_date_str(end + timedelta(days=1)):
        date = get_date_str(start)
        if date in json_data['weight']:
            value = float(json_data['weight'][date])
            mean_wt.append(value)
        while len(mean_wt) > N_MEAN:
            mean_wt.pop(0)
        wt = get_weighted_mean(mean_wt)
        x.append(get_date_str(start))
        y1.append(wt)
        start += timedelta(days=1)
   
    title = f'Weight ({start_str} - {end_str})'
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(Scatter(x=x, y=y1, name='Weight', line={'color': 'blue'}), secondary_y=False)
    fig.update_layout(
        title=title, 
        font={'size':20}, 
        yaxis={
            'range': [170,210]
        },
        xaxis={
            'tickangle': 30
        }
    )
    fig.show()


def plot_one(option):
    global json_data
    global NAME_MAP

    if option not in ['s', 'm']:
        print(f'No such option: {option}')
        exit(-1)

    name = NAME_MAP[option]

    load_json()
    print('Start Date')
    start = get_date()
    start_str = get_date_str(start)
    print('\nEnd Date')
    end = get_date() 
    end_str = get_date_str(end)

    mean_list = []
    x = []
    y = []

    while get_date_str(start) != get_date_str(end + timedelta(days=1)):
        date = get_date_str(start)
        if date in json_data[name]:
            if name == 'amount':
                sum = 0
                for item in json_data[name][date]:
                    sum += float(item)
                value = sum
            else:
                value = float(json_data[name][date])
            mean_list.append(value)
        elif name in ['minutes' or 'amount']:
            mean_list.append(0)
        while len(mean_list) > N_MEAN:
            mean_list.pop(0)
        mean_value = get_weighted_mean(mean_list)
        x.append(get_date_str(start))
        y.append(mean_value)
        start += timedelta(days=1)
   
    title_map = {
        'amount': 'Spending',
        'weight': 'Weight',
        'minutes': 'Minutes'
    }
    title = f'{title_map[name]} ({start_str} - {end_str})'
    plotly.offline.plot({
        'data': [Scatter(x=x, y=y)],
        'layout': Layout(title=title, font={'size':18})
    })
    

if __name__ == '__main__':
    FILENAME = 'tracker.dat'
    
    if len(argv) == 1:
        main()

    elif len(argv) == 2 and argv[1] == 'v':  
        load_json()
        update_colors()
        view_all()
 
    elif len(argv) == 3:
        if argv[1] == 'p':
            if argv[2] == 'w':
                plot_weight()
            else:
                plot_one(argv[2])
        else:
            add_one(argv[1], argv[2])
    
    else:
        print('python', argv[0], 'w|m|s', 'value')
        print('python', argv[0], 'v')
        print('python', argv[0], 'p', 'w|m|s')
    

