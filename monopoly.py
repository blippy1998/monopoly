import random
import math

unownables = [0, 2, 4, 7, 10, 17, 20, 22, 30, 33, 36, 38]
prop_values = {1:60, 3:60, 5:200, 6:100, 8:100, 9:120, 11:140, 12:140, 13:150,
	14:160, 15:200, 16:180, 18:180, 19:200,	21:220, 23:220, 24:240, 25:200,
	26:260, 27:260, 28:150, 29:280, 31:300, 32:300, 34:320, 35:200, 37:350,
	39:400}

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

class Data:

	def __init__(self):
		self.pos = 0 # position
		self.cash = 1500
		self.props = [] # properties
		self.asset_value = 0
		self.net = 1500 # net worth
		self.jail = 0 # turns left in jail; 0 if not in jail
		self.bankrupt = False
		self.jail_free = 0

	def sub_cash(self, amount, odlist):
		if self.cash >= amount:
			self.cash -= amount
			self.net -= amount
		else:
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
		assert(prop.mortgaged == False)

		prop.mortgaged = True
		self.cash += prop.value

	def unmortgage(self, prop):
		assert(prop.owned)
		assert(prop in self.props)
		assert(prop.mortgaged == True)
		assert(self.cash >= int(prop.value * 1.1))

		prop.mortgaged = False
		self.cash -= int(prop.value * 1.1)
		self.net -= int(prop.value * .1)

	def rent_collect(self, pd, dice):
		global players
		assert(properties[pd.pos] in self.props)

		odlist = []
		for p in players:
			if p != pd:
				odlist.append(p)

		if pd.pos != 4 and pd.pos % 5 != 0 and pd.pos != 12 and pd.pos != 28 \
			and pd.pos != 37 and pd.pos != 39:
			rent = int(properties[pd.pos].value * .1) - 4
		elif pd.pos == 4:
			rent = 4
		elif pd.pos % 5 == 0:
			rent = 25
		elif pd.pos == 12 or pd.pos == 28:
			rent = 4 * sum(dice)
		elif pd.pos == 37:
			rent = 35
		elif pd.pos == 39:
			rent = 50

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
			lose_to.props += self.props
			for p in self.props:
				lose_to.net += p.value
			self.props = []
		players.remove(self)
		pprint(self)

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
			pd.add_cash(2) # TODO: GO should be 200, not 2
		eval_pos(pd, odlist, dice)
		if pd.jail or pd.bankrupt:
			return None
		if doubles:
			move(pd, odlist, num_doubles)
	else:
		jail(pd, odlist)

def props_to_mortgage(pd, amount):
	ptm = [] # "props to mortgage"
	total = 0
	for p in pd.props:
		if p.mortgaged:
			continue
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
		to_buy_prop = to_buy(pd, odlist)
		if to_buy_prop:
			# print("buying")
			buy(pd, odlist)
		else:
			if properties[pd.pos].owned:
				for od in odlist:
					if properties[pd.pos] in od.props:
						od.rent_collect(pd, dice)
						break

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
			pd.sub_cash(int(pd.cash * .1), odlist)
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
		if dice[0] == dice[1] or pd.jail == 0:
			pd.jail = 0
			pd.pos += dice[0] + dice[1]
			eval_pos(pd, odlist, dice)
		else:
			pd.jail -= 1

def buy(pd, odlist):
	assert(not properties[pd.pos].owned)
	assert(properties[pd.pos] not in pd.props)
	assert(pd.cash >= prop_values[pd.pos])

	properties[pd.pos].owned = True
	pd.props.append(properties[pd.pos])
	pd.cash -= properties[pd.pos].value

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
	print("position:\t" + str(pd.pos))
	print("cash:\t\t" + str(pd.cash))
	keys = []
	for prop in pd.props:
		keys.append(prop.pos)
	keys.sort()
	print("properties:\t" + str(keys))
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

	while(len(players) > 1):
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
		print(turn)
		pprint(players[turn])
	# print(players)

if __name__ == "__main__":
	v2007 = True
	players = []
	properties = {}
	num_players = 4

	for i in range(num_players):
		player = Data()
		players.append(player)

	for pos in prop_values.keys():
		prop = Property(pos)
		properties[pos] = prop

	play()