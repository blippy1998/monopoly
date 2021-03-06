import random
import math

unownables = [0, 2, 4, 7, 10, 17, 20, 22, 30, 33, 36, 38]
prop_values = {1:60, 3:60, 5:200, 6:100, 8:100, 9:120, 11:140, 12:140, 13:150,
	14:160, 15:200, 16:180, 18:180, 19:200,	21:220, 23:220, 24:240, 25:200,
	26:260, 27:260, 28:150, 29:280, 31:300, 32:300, 34:320, 35:200, 37:350,
	39:400}
monopolies = {"brown":(1, 3), "rail":(5, 15, 25, 35), "lblue":(6, 8, 9),
	"pink":(11, 13, 14), "util":(12, 28), "orange":(16, 18, 19),
	"red":(21, 23, 24), "yellow":(25, 27, 29), "green":(31, 32, 34),
	"dblue":(37, 39)}
rents = {
			1:(2, 10, 30, 90, 160, 250),
			3:(4, 20, 60, 180, 320, 450),
			6:(6, 30, 90, 270, 400, 550),
			8:(6, 30, 90, 270, 400, 550),
			9:(8, 40, 100, 300, 450, 600),
			11:(10, 50, 150, 450, 625, 750),
			13:(10, 50, 150, 450, 625, 750),
			14:(12, 60, 180, 500, 700, 900),
			16:(14, 70, 200, 550, 750, 950),
			18:(14, 70, 200, 550, 750, 950),
			19:(16, 80, 220, 600, 800, 1000),
			21:(18, 90, 250, 700, 875, 1050),
			23:(18, 90, 250, 700, 875, 1050),
			24:(20, 100, 300, 750, 925, 1100),
			26:(22, 110, 330, 800, 975, 1150),
			27:(22, 110, 330, 800, 975, 1150),
			29:(24, 120, 360, 850, 1025, 1200),
			31:(26, 130, 390, 900, 1100, 1275),
			32:(26, 130, 390, 900, 1100, 1275),
			34:(28, 150, 450, 1000, 1200, 1400),
			37:(35, 175, 500, 1100, 1300, 1500),
			39:(50, 200, 600, 1400, 1700, 2000)
		}
houses = 32
hotels = 12

def to_buy(pd, odlist):
	"""
	pd is the player data

	odlist is a list of lists that holds each opponent's player data

	this function will return whether to buy a property or houses on a set of
	properties given the position of the board
	"""

	assert(pd.pos not in unownables)

	# if it's owned already
	if properties[pd.pos].owned:
		return False

	# print(properties[pd.pos].value)
	if(pd.cash >= properties[pd.pos].value):
		return True

	return False

class Property:

	def __init__(self, pos):
		assert(pos not in unownables)
		self.pos = pos
		self.value = prop_values[pos]
		self.owned = False
		self.mortgaged = False
		self.houses = 0 # 5 houses means a hotel

class Data:

	def __init__(self, number):
		self.number = number
		self.pos = 0 # position
		self.cash = 1500
		self.props = [] # properties
		self.rcprops = [] # rent-collecting (i.e. unmortgaged) properties
		self.mprops = [] # mortgaged properties
		self.asset_value = 0
		self.net = 1500 # net worth
		self.jail = 0 # turns left in jail; 0 if not in jail
		self.bankrupt = False
		self.jail_free = 0 # number of GOJF cards
		self.monopolies = set() # which monopolies the player owns

	def sub_cash(self, amount, odlist):
		if self.cash >= amount:
			self.cash -= amount
			self.net -= amount
		else:
			enough = False
			for p in self.rcprops:
				while not enough:
					possible = self.sell_house(p)
					if self.cash > amount:
						enough = True
					if not possible:
						break

			mortgage = to_trade_or_mortgage(self, odlist)
			if not mortgage:
				trade(self, odlist)
			if self.cash < amount:
				mortgage_props = props_to_mortgage(self, amount)
				for p in mortgage_props:
					self.mortgage(p)
		if(self.cash < 0):
			self.bankrupt = True

	def add_cash(self, amount):
		self.cash += amount
		self.net += amount

	def mortgage(self, prop):
		assert(prop.owned)
		assert(prop in self.props)
		assert(not prop.mortgaged)

		prop.mortgaged = True
		self.mprops.append(prop)
		self.rcprops.remove(prop)
		self.cash += prop.value // 2
		self.net += prop.value // 2

		# self.check_monopolies()

	def unmortgage(self, prop):
		assert(prop.owned)
		assert(prop in self.props)
		assert(prop.mortgaged)
		assert(self.cash >= int(prop.value * 1.1))

		prop.mortgaged = False
		self.mprops.remove(prop)
		self.rcprops.append(prop)
		self.cash -= int(prop.value // 2 * 1.1)
		self.net -= int(prop.value // 2 * 1.1)

		# self.check_monopolies()

	def rent_collect(self, pd, dice):
		global monopolies
		global players
		global rents

		prop = properties[pd.pos]

		assert(prop.pos == pd.pos)
		assert(prop in self.props)

		if prop not in self.rcprops:
			return None

		odlist = []
		for p in players:
			if p != pd:
				odlist.append(p)

		if pd.pos % 5 != 0 and pd.pos != 12 and pd.pos != 28:
			rent = rents[prop.pos][prop.houses]
		elif pd.pos == 12 or pd.pos == 28:
			if "util" in self.monopolies:
				rent = 10 * sum(dice)
			else:
				rent = 4 * sum(dice)
		else:
			assert(pd.pos % 5 == 0)
			railroads = 0
			for p in self.props:
				if p.pos % 5 == 0:
					railroads += 1
			assert(railroads >= 1)
			assert(railroads <= 4)
			rent = 25 * (2 ** railroads)

		if prop.houses == 0:
			for m in self.monopolies:
				if pd.pos in monopolies[m]:
					rent *= 2
					break

		print("Player " + str(pd.number) + " paying $" + str(rent) +
			" to Player " + str(self.number))
		pd.sub_cash(rent, odlist)
		if pd.bankrupt:
			pd.lose(True, lose_to=self)
			return None
		self.add_cash(rent)

	def lose(self, to_player, **kwargs):
		global players
		# print("to_player: " + str(to_player))
		self.bankrupt = True
		if not to_player:
			assert(len(kwargs) == 0)
		else:
			assert(len(kwargs.keys()) == 1)
			lose_to = kwargs["lose_to"]
		if not to_player:
			for p in self.props:
				p.mortgaged = False
				p.owned = False
		else:
			lose_to.cash += self.cash
			lose_to.props += self.props
			lose_to.mprops += self.mprops
			lose_to.rcprops += self.rcprops
			lose_to.check_monopolies()
			for p in self.props:
				lose_to.net += p.value
			self.props = []
			self.mprops = []
			self.rcprops = []
			self.check_monopolies()
		players.remove(self)
		pprint(self)

	def check_monopolies(self):
		global monopolies

		self.monopolies = set()

		positions = []
		for p in self.props:
			positions.append(p.pos)

		for m in monopolies.keys():
			mono = True
			for p in monopolies[m]:
				if p not in positions:
					mono = False
					break
			if mono:
				self.monopolies.add(m)

	def buy_house(self, prop):
		global monopolies
		global houses
		global hotels

		assert(prop not in unownables)
		assert(prop in self.rcprops)
		assert(prop.houses >= 0)
		assert(prop.houses <= 5)

		if prop.houses == 5:
			return False
		if prop.houses == 4 and hotels == 0:
			return False
		if prop.houses < 4 and houses == 0:
			return False

		in_monopoly = False
		for m in self.monopolies:
			if m == "rail" or m == "util":
				continue
			if prop.pos in monopolies[m]:
				in_monopoly = True
				for p in self.props:
					if p.pos in monopolies[m] and p.mortgaged:
						in_monopoly = False
						break
				break

		if not in_monopoly:
			return False

		cost = 50 * (prop.pos // 10 + 1)

		if self.cash >= cost:
			prop.houses += 1
			if prop.houses == 5:
				houses += 4
				hotels -= 1
			else:
				houses -= 1
			self.cash -= cost
			# print("buying house")
			return True

		return False

	def sell_house(self, prop):
		global houses
		global hotels

		assert(prop not in unownables)
		assert(prop in self.rcprops)
		assert(prop.houses >= 0)
		assert(prop.houses <= 5)

		if prop.houses == 0:
			return False

		if prop.houses == 5:
			if houses < 4:
				return False
			houses -= 4
			hotels += 1
		else:
			houses += 1

		sale_price = 25 * (prop.pos // 10 + 1) # half value
		prop.houses -= 1
		self.cash += sale_price
		self.net -= sale_price

def move(pd, odlist, num_doubles):
	"""
	pd is the player data: a list that holds the player's position, cash, and
	assets

	this function will roll the dice, move the player, and evaluate the new
	position
	"""

	global players

	assert(pd in players)
	assert(num_doubles < 3)

	if not pd.jail:
		dice = roll_dice()
		doubles = dice[0] == dice[1]
		num_doubles += int(doubles)
		if num_doubles == 3:
			go_jail(pd)
			return None

		old_pos = pd.pos
		pd.pos = (pd.pos + sum(dice)) % 40
		if pd.pos < old_pos:
			pd.add_cash(200) # TODO: GO should be 200, not 20
		eval_pos(pd, odlist, dice)
		if pd.jail or pd.bankrupt:
			return None
		if doubles:
			move(pd, odlist, num_doubles)
	else:
		jail(pd, odlist)

	for p in pd.mprops:
		if pd.cash >= int(p.value * 1.1):
			pd.unmortgage(p)
		else:
			break

	for p in pd.rcprops:
		while True:
			possible = pd.buy_house(p)
			if not possible:
				break

	pprint(pd)

def props_to_mortgage(pd, amount):
	ptm = [] # "props to mortgage"
	total = 0
	for p in pd.rcprops:
		ptm.append(p)
		total += p.value
		if total > amount:
			break
	if total < amount:
		pd.bankrupt = True
	return ptm

def eval_pos(pd, odlist, dice):
	"""
	pd is the player data

	this function will update the board based on the position the player has
	moved to (e.g. chance or community chest, etc.)
	"""

	if pd.pos not in unownables:
		# print("ownable")
		prop = properties[pd.pos]
		if prop.owned:
			for od in odlist:
				if prop in od.props:
					od.rent_collect(pd, dice)
					break
		else:
			to_buy_prop = to_buy(pd, odlist)
			if to_buy_prop:
				# print("buying")
				buy(pd)
			else:
				auction(prop)

	elif pd.pos == 2 or pd.pos == 17 or pd.pos == 33:
		draw_comm_chest(pd, odlist)
	elif pd.pos == 4:
		income_tax(pd, odlist)
	elif pd.pos == 7 or pd.pos == 22 or pd.pos == 36:
		draw_chance(pd, odlist)
	elif pd.pos == 30:
		go_jail(pd)
	elif pd.pos == 38:
		luxury_tax(pd, odlist)
	# adding cash from go is handled in move()
	# jail is handled in move()
	# nothing happens in free parking

def auction(prop):
	global players

	# TODO
	pass

def simulate(pd, odlist):
	# TODO
	pass

def roll_dice():
	a = random.randint(1, 6)
	b = random.randint(1, 6)

	# print(a == b)

	return (a, b)

def income_tax(pd, odlist):
	global players
	global v2007
	if v2007:
		if pd.net >= 2000:
			pd.sub_cash(200, odlist)
		else:
			pd.sub_cash(pd.net // 10, odlist)
	else:
		pd.sub_cash(200, odlist)
	if pd.bankrupt:
		pd.lose(False)

def luxury_tax(pd, odlist):
	global players
	global v2007
	if v2007:
		pd.sub_cash(75, odlist)
	else:
		pd.sub_cash(100, odlist)
	if pd.bankrupt:
		pd.lose(False)

def go_jail(pd):
	pd.pos = 10
	pd.jail = 3

def draw_chance(pd, odlist):
	pass

def draw_comm_chest(pd, odlist):
	pass

def jail(pd, odlist):
	use_card = False
	if pd.jail_free:
		use_card = to_use_jail_free(pd, odlist)
	if use_card:
		pd.jail = 0
		move(pd, odlist, 0)
	else:
		dice = roll_dice()
		if dice[0] == dice[1]:
			pd.jail = 0
			pd.pos += sum(dice)
			eval_pos(pd, odlist, dice)
		elif pd.jail == 1:
			pd.sub_cash(50, odlist)
			pd.jail = 0
			pd.pos += sum(dice)
			eval_pos(pd, odlist, dice)
		else:
			pd.jail -= 1

def buy(pd):
	global monopolies
	global players

	prop = properties[pd.pos]

	assert(not prop.owned)
	assert(prop not in pd.props)
	assert(pd.cash >= prop_values[pd.pos])

	prop.owned = True
	pd.props.append(prop)
	pd.rcprops.append(prop)
	pd.cash -= prop.value
	pd.check_monopolies()

def to_trade_or_mortgage(pd, odlist):
	# TODO
	return True

def trade(pd, odlist):
	# TODO
	traded = False
	trade_props = props_to_trade(pd)
	if trade_props:
		trade_with = to_trade_with(pd, odlist)
		if trade_with:
			traded = offer_trade(trade_props, trade_with)
	return traded

def pprint(pd):
	print("Player " + str(pd.number))
	print("position:\t" + str(pd.pos))
	print("cash:\t\t" + str(pd.cash))
	keys = []
	for prop in pd.props:
		keys.append(prop.pos)
	keys.sort()
	print("properties:\t" + str(keys))
	rckeys = []
	for prop in pd.rcprops:
		rckeys.append(prop.pos)
	rckeys.sort()
	print("for rent:\t" + str(rckeys))
	mkeys = []
	for prop in pd.mprops:
		mkeys.append(prop.pos)
	mkeys.sort()
	print("mortgaged:\t" + str(mkeys))
	print("monopolies:\t" + str(pd.monopolies))
	print("net worth:\t" + str(pd.net))
	print("jail no.:\t" + str(pd.jail))
	print("bankrupt:\t" + str(pd.bankrupt))
	print("GOJF cards:\t" + str(pd.jail_free))
	print("")
	print("")

def play():
	global players
	global properties
	turn = 0
	turns = 0

	while turns < 1000 and len(players) > 1:
		length = len(players)
		odlist = []
		for p in players:
			if p != players[turn]:
				odlist.append(p)
		move(players[turn], odlist, 0)
		if(len(players) == length):
			turn = (turn + 1) % len(players)
		else:
			turn %= len(players)
		turns += 1
	# print(players)

if __name__ == "__main__":
	v2007 = True
	players = []
	properties = {}
	num_players = 2

	for i in range(num_players):
		player = Data(i + 1)
		players.append(player)

	for pos in prop_values.keys():
		prop = Property(pos)
		properties[pos] = prop

	play()