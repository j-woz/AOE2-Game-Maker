
import csv, sys

csvfile = None
online  = None

def do_argparse():
    import argparse
    parser = argparse.ArgumentParser(description='Propose a game.')
    parser.add_argument('csvfile')
    parser.add_argument('online')
    args = parser.parse_args()
    global csvfile, online
    csvfile, online = args.csvfile, args.online


do_argparse()


class Player:

    def __init__(self, name, column):
        self.name = name
        self.column = column
        self.rank = 1
        self.wins = 0
        self.losses = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def description(self):
        games = self.wins + self.losses
        pct = 0 if games == 0 else int(100.0 * self.wins / games)
        pct_str = "(%i%%)" % pct
        return "%s: [%i] %i/%i %6s" % \
            (self.name, self.rank, self.wins, games, pct_str)

    def win(self):
        self.wins += 1
        self.rank += 1

    def lose(self):
        self.losses += 1
        self.rank -= 1
        if self.rank < 0: self.rank = 0

    def get_rank(player):
        """ for sorting """
        return player.rank


# Map from CSV column number to Player
# Indexed from 1
columns = {}

def read_header(header):
    column = 0
    for name in header[1:]: # skip column 0 (dates)
        column += 1
        if len(name) == 0: continue
        player = Player(name, column)
        columns[column] = player
    return columns

def read_rows(reader, columns):
    row = 2
    for data in reader:
        column = 0
        if data[0] == "End data": break # special value in CSV
        for token in data[1:]: # skip column 0 (dates)
            column += 1
            if len(token) == 0: continue
            player = columns[column]
            if   token == "W":  player.win()
            elif token == "L":  player.lose()
            else:
                raise ValueError("Bad data: " +
                                 "row=%i column=%i data='%s'" %
                                 (row, column, token))
    row += 1


dialect = csv.unix_dialect()
dialect.strict = True
with open(csvfile, newline='') as fp:
    reader = csv.reader(fp, dialect=dialect)
    columns = read_header(next(reader))
    read_rows(reader, columns)

# print(columns)

# for column in columns:
#     print("%2i: %s" % (column, columns[column].description()))


def fail(msg):
    print("FAIL: " + msg)
    exit(1)

# Sort all Players into a list    
players = sorted(columns.values(), key=Player.get_rank, reverse=True)

print("All players:")
for p in players:
    print(p.description())

# Split up given online player names:
active = online.split(",")
N = len(active)

# Check that all players are in the spreadsheet
for name in active:
    found = False
    for p in players: 
        if name == p.name:
            found = True
            continue
    if not found:
        fail("Unknown player: " + name)

# Ensure the number of unique players is the same as the number of given
#        player names
unique = {} # temp, will delete
for name in active:
    unique[name] = 0
if len(unique) != len(active):
    fail("Player names were not unique!")
del unique

verbose = False

def out(level, message):
    """ output message with indentation level """
    if not verbose:
        return
    for i in range(0,level):
        sys.stdout.write("  ")
    print(message)

def sl(L):
    """ string-list """
    return " " + " ".join(map(str, L))

# Start handling combos...
# A combo is an list of team numbers, one for each player
# For example: [1,2,1,2] puts players 0 & 2 on team 1,
#                                     1 & 3 on team 2.

# Sorted list of (score, combo).  Index 0 is the best (lowest) diff.
best = []
best_max = 10
# Initialize the list of best with Nones:
for i in range(0, best_max):
    best.append(None)

def best_add(combo):
    """ Sorted insert into list of best combos """
    diff = score(combo)
    # for i in range(0, 10):
    #     show_best(i)
    # Start with top of list
    for i in range(0, 10):
        # Found blank entry: insert
        if best[i] == None:
            best[i] = (diff, combo)
            break
        # Are we better?
        if diff < best[i][0]:
            # If so, shift everyone else down
            for j in range(9,i,-1):
                best[j] = best[j-1]
            best[i] = (diff, combo)
            break
    # print("")
    # for i in range(0, 10):
    #     show_best(i)
    # print("")
    # print("--")
    # print("")

def show_best(i):
    if best[i] != None:
        print("%2i    %s -> %i" % \
              (i, named_teams(best[i][1]), best[i][0]))

    
def score(combo):
    scores = [0,0]
    # print("score: " + sl(combo))
    for i in range(0, len(combo)):
        scores[combo[i]-1] += columns[i+1].rank
    diff = abs(scores[0]-scores[1])
    # print(" -> %s -> %s -> %i" % (str(scores), named_teams(combo), diff))
    return diff


def named_teams(combo):
    names = [[], []]
    for i in range(0, len(combo)):
        names[combo[i]-1].append(columns[i+1].name)
    return "%s vs. %s" % (",".join(names[0]), ",".join(names[1]))


# Player 0 is always on team 1:        
teams = [ 1 ]
# Initial combo:
for i in range(1,int(N/2)):
    teams.append(1)
for i in range(int(N/2),N):
    teams.append(2)

total = 0    
combos = []
combos.append(teams)
total += 1

def samples(teams, start):
    """ Generate all unique combos, add to global list combos """
    global total
    out(start, "samples[%i]" % start)
    out(start, sl(teams))
    if start == N-1:
        out(start, "done!")
        return
    samples(teams, start+1)
    if teams[start] == 1:
        swap = True
        t = start+1
        while True:
            if t == N:
                swap = False
                break
            if teams[t] == 2:
                break
            t += 1
        if swap:
            teams_new = teams.copy()
            out(start+1, "swap: %i %i" % (start,t))
            teams_new[start] = 2
            teams_new[t] = 1
            out(start+1, sl(teams_new) + " new! " + str(total))
            total += 1
            combos.append(teams_new)
            best_add(teams_new)
            samples(teams_new, start+1)
  
samples(teams, 1)

i = 0
for combo in combos:
    # print(sl(combo) + " : %2i" % i)
    i += 1
print("combos: %i" % len(combos))

for i in range(0, 10):
    show_best(i)

best_diff = best[0][0]
print("best diff: %i" % best_diff)

