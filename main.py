import calendar
import datetime
import math
import json
import random
import plotly
import sys

class Loader:
    def __init__(self):
        self.weight = {}
        self.minutes = {}
        self.spending = {}
        self.count = 0
        self.last_date = None
        with open('data.dat', 'r') as fp:
            for line in fp.readlines():
                line = line.split()
                if not line:
                    continue
                date = line[0]
                self.weight[date] = float(line[1])
                self.minutes[date] = int(line[2])
                sum = 0;
                for amount in line[3].split('+'):
                    sum += float(amount)
                self.spending[date] = sum
                date = date.split('/')
                month = int(date[0])
                day = int(date[1])
                year = 2000 + int(date[2])
                self.last_date = datetime.datetime(year=year, month=month, day=day)
                self.count += 1

        with open('params.dat', 'r') as fp:
            self.info = json.load(fp)

class Graph:
    def build(title, x, yavg, range=None, ytrg=None):
        fig = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(plotly.graph_objs.Scatter(x=x, y=yavg, name='average', line={'color': 'blue'}), secondary_y=False)
        if ytrg:
            fig.add_trace(plotly.graph_objs.Scatter(x=x, y=ytrg, name='target', line={'color': 'orange'}), secondary_y=False)
        fig.update_layout(
            title=title, 
            font={'size':20}, 
            xaxis={
                'tickangle': 30,
                'tickmode': 'auto',
                'nticks': 30
            }
        )
        if range:
            fig.update_layout(yaxis={'range': range})
        fig.show()

class Format:
    def time(val):
        val = int(val)
        val = f'{val:4d}'
        return f'{val[0:2]}:{val[2:4]} AM'

    def minutes(val):
        hours = math.floor(val / 60)
        mins = val % 60
        return f'{hours:2.0f}:{mins:02.0f}'

    def money(val):
        return f'${val:0.2f}'.rjust(7)

    def weight(val):
        return f'{val:5.1f}'


class Cell:
    def __init__(self, row, col, width, color, str):
        self.row = row
        self.col = col
        self.width = width
        self.color = color
        self.str = str
        self.pad = ''.ljust(width - len(str))
    
    def print(self, active=False):
        Cursor.set(self.row, self.col)
        color = f'{self.color};7' if active else self.color
        print(f'\033[38;5;{color}m{self.str}\033[0m', end='')


class Cursor:
    COLS = 50
    ROWS = 0

    def set(row, col):
        print(f'\033[{row};{col}H', end='')

    def clear():
        print(f'\033[2J', end='')


class View:
    ROW_MAX = 7
    MEAN_OFFSET = 5
    
    def __init__(self):
        loader = Loader()
        self.date = loader.last_date
        self.weight = loader.weight
        self.minutes = loader.minutes
        self.spending = loader.spending
        self.info = loader.info
        View.ROW_MAX = min(loader.count, self.info['row-max'])
        Cursor.ROWS = View.ROW_MAX
        View.MEAN_OFFSET = self.info['mean-offset']

    def calc_mean(self, items, date):
        sum = 0
        wsum = 0
        count = 0
        w = [15, 10, 6, 3, 1]
        for offset in range(View.MEAN_OFFSET):
            date_str = (date - datetime.timedelta(days=offset)).strftime("%m/%d/%y")
            if date_str in items:
                sum += items[date_str] * w[count]
                wsum += w[count]
                count += 1
        return sum / wsum

    def calc_target(self, name, date):
        year = self.info['start-year']
        month = self.info['start-month']
        day = self.info['start-day']
        days = (date - datetime.date(year=year, month=month, day=day)).total_seconds() / (60*60*24)
        if name == 'weight':
            wt = self.info['weight-start'] + days * self.info['weight-slope']
            return max(self.info['weight-min'], min(self.info['weight-start'], wt))
        elif name == 'duration':
            mins = self.info['minutes-start'] + days * self.info['minutes-slope']
            return max(self.info['minutes-start'], min(self.info['minutes-max'], mins)) 

    def plot(self, name):
        if name == 'weight':
            self.plot_field(self.weight, name)
        elif name == 'duration':
            self.plot_field(self.minutes, name) 
        elif name == 'spending':
            self.plot_field(self.spending, name)
        else:
            print(f'No such name: {name}')

    def plot_field(self, items, name):
        x = []
        yavg = []
        ytrg = [] if name not in ['spending', 'start'] else None
        min_date = None
        max_date = None
        for date_str, item in items.items():
            x.append(date_str)
            year = 2000 + int(date_str[6:8])
            month = int(date_str[0:2])
            day = int(date_str[3:5])
            date = datetime.date(year=year, month=month, day=day)
            if not min_date or date < min_date:
                min_date = date
            if not max_date or date > max_date:
                max_date = date
            if name == 'start':
                yavg.append(items[date_str])
            else:
                yavg.append(self.calc_mean(items, date))
            if name not in ['spending', 'start']:
                ytrg.append(self.calc_target(name, date))
        min_date = min_date.strftime("%m/%d/%y")
        max_date = max_date.strftime("%m/%d/%y")
        title = f'{name} ({min_date} - {max_date})'
        if name == 'weight':
            range = [170, 215]
        else:
            range = [0, max(yavg) * 1.1]
        Graph.build(title, x, yavg, range, ytrg)

    def emit_all(self):
        self.cells = {}
        for row_idx in range(View.ROW_MAX):
            col = 1
            row = row_idx + 1
            self.cells[row] = []

            date = self.date - datetime.timedelta(days=View.ROW_MAX - (row_idx + 1))
            date_str = date.strftime("%m/%d/%y")
            
            self.cells[row].append(Cell(row, col, 8, '245', date_str))
            col += 11

            wt = Format.weight(self.weight[date_str])
            self.cells[row].append(Cell(row, col, 5, '15', wt)) 
            col += 6

            wt_mean = Format.weight(self.calc_mean(self.weight, date))
            self.cells[row].append(Cell(row, col, 5, '15;2', wt_mean)) 
            col += 6

            mins = Format.minutes(self.minutes[date_str])
            self.cells[row].append(Cell(row, col, 4, '11', mins)) 
            col += 5

            mins_mean = Format.minutes(self.calc_mean(self.minutes, date))
            self.cells[row].append(Cell(row, col, 4, '11;2', mins_mean)) 
            col += 7
                        
            spend = Format.money(self.spending[date_str])
            self.cells[row].append(Cell(row, col, 7, '10', spend))    
            col += 8
        
            spend_mean = Format.money(self.calc_mean(self.spending, date))
            self.cells[row].append(Cell(row, col, 7, '10;2', spend_mean))    
            col += 9           

    def print_all(self):
        self.emit_all()
        Cursor.clear()
        #header_str = 'date       weight       duration    start    sunrise   spending      '
        #header = Cell(1, 1, Cursor.COLS, '250;7', header_str)
        #header.print()
        for row, items in self.cells.items():
            if row == View.ROW_MAX:
                self.cells[row][0].color = '15' 
            for item in self.cells[row]:
                item.print()
            print()

def main():
    view = View()
    view.print_all()
    if len(sys.argv) == 2:
        name = sys.argv[1]
        view.plot(name)

if __name__ == '__main__':
    main()
    
