import datetime
import sys

def main():
    if len(sys.argv) == 2:
        weight = float(sys.argv[1])
        date = datetime.date.today()
        date = date.strftime('%m/%d/%y')
        with open('data.dat', 'a+') as fp:
            fp.write(f'{date} {weight:0.1f} 0 0.00\n')
    else:
        print('./add.sh <weight>')

if __name__ == '__main__':
    main()
