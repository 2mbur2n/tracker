import sys

def main():
    if len(sys.argv) == 2:
        minutes = int(sys.argv[1])
        with open('data.dat', 'r') as fp:
            lines = fp.readlines()
        lines = [x[0:-1] if x[-1] == '\n' else x for x in lines]
        line = lines[-1]
        line = line.split()
        date = line[0]
        weight = line[1]
        duration = line[2]
        spending = line[3]
        lines[-1] = f'{date} {weight} {minutes} {spending}'
        with open('data.dat', 'w+') as fp:
            for line in lines:
                fp.write(f'{line}\n')

    else:
        print('./minutes.sh <value>')

if __name__ == '__main__':
    main()
