import discord
from random import shuffle
from asyncio import sleep

# TODO: add config/persistent file
token = "your token here"
startchannel = None

mafiachannel = None
copchannel = None
generalchannel = None


class Mafia:
    def __init__(self):
        self.players = []
        self.playerRoles = {}
        self.gamestate = "initialized"
        self.nominations = {}
        self.responded = 0

    async def increment_gamestate(self):
        if self.gamestate == "initialized":
            await startchannel.send('@Notifications:\n'
                                    'Starting game.\n '
                                    'Everyone wishing to participate, '
                                    'please react with a :thumbsup: to this message.')
            self.gamestate = "waiting for players"
        elif self.gamestate == "waiting for players":
            await startchannel.send('Closing sign-ups.')
            await sleep(5)
            await startchannel.send('Sign-ups closed. Sending out roles via DMs.')

            self.gamestate = "setting up"
            counter = 0
            # get signupMessage
            signupMessage = None
            async for message in startchannel.history(limit=50):
                if message.author == client.user:
                    counter += 1
                if counter == 3:
                    signupMessage = message
                break

            # get all users who reacted to the signup message
            for reaction in signupMessage.reactions:
                if reaction.emoji == '👍':
                    self.players = await reaction.users().flatten()

            # DM and set roles for mafia, cops, villagers
            userRoles = self.assignroles()
            for role in userRoles.keys():
                users = userRoles[role]
                for user in users:
                    if not user.dm_channel:
                        await user.create_dm()

                    user.dm_channel.send(role)
                    if role == "Mafia":
                        await mafiachannel.set_permissions(user, read_messages=True,
                                                           send_messages=False)
                    elif role == "Cop":
                        await copchannel.set_permissions(user, read_messages=True,
                                                         send_messages=False)
                    else:
                        await mafiachannel.set_permissions(user, read_messages=False,
                                                           send_messages=False)
                        await copchannel.set_permissions(user, read_messages=False,
                                                         send_messages=False)

                    await generalchannel.set_permissions(user, read_messages=True,
                                                         send_messages=False)

            # @ all the mafia and tell them that they're mafia
            for user in userRoles["Mafia"]:
                await mafiachannel.send('@' + user.display_name)
            await mafiachannel.send('You are mafia')

            # @ all the cops and tell them that they're cops
            for user in userRoles["Cop"]:
                await copchannel.send('@' + user.display_name)
            await copchannel.send('You are cops')
            self.gamestate = "set up"
        elif self.gamestate == "set up":
            await self.play()

    async def play(self):
        gameDone = False
        while not gameDone:
            # DAY
            # give chat perms
            for user in maf.players:
                await generalchannel.set_permissions(user, read_messages=True,
                                                     send_messages=True)
            await sleep(300)
            # take chat perms
            for user in maf.players:
                await generalchannel.set_permissions(user, read_messages=True,
                                                     send_messages=False)
            self.gamestate = "day nominations"
            # ask for nominations
            for user in maf.players:
                await generalchannel.set_permissions(user, read_messages=True,
                                                     send_messages=True)
                await generalchannel.send('@' + user.display_name + ', who do you nominate? '
                                                                    '(nominate with !nom @{person})')

                for i in range(15):
                    old_responded = self.responded
                    await sleep(1)
                    if self.responded > old_responded:
                        break
                    if i >= 14:
                        await generalchannel.send('Assuming that no nomination is an abstention, @' +
                                                  user.display_name + '.')
                await generalchannel.set_permissions(user, read_messages=True, send_messages=False)

            self.responded = 0
            # vote
            self.gamestate = "day voting"
            for user in maf.players:
                await generalchannel.set_permissions(user, read_messages=True,
                                                     send_messages=True)
                await generalchannel.send('@' + user.display_name + ', who do you vote for? '
                                                                    '(nominate with !v @{person})')

                for i in range(15):
                    old_responded = self.responded
                    await sleep(1)
                    if self.responded > old_responded:
                        break
                    if i >= 14:
                        await generalchannel.send('Assuming that no vote is an abstention, @' +
                                                  user.display_name + '.')
                await generalchannel.set_permissions(user, read_messages=True, send_messages=False)
            # get voting results
            dead_user = max(self.nominations, key=lambda key: self.nominations[key])
            self.death(dead_user)



    def __getroles(self):
        numMaf = round(len(self.players)/4)
        numCop = 1
        numVil = len(self.players)-(numMaf + numCop)

        roles = ["Mafia" for _ in range(numMaf)] + ["Cop" for _ in range(numCop)] + ["Villager" for _ in range(numVil)]
        return roles

    def assignroles(self):
        roles = self.__getroles()
        shuffle(roles)

        for player in self.players:
            try:
                self.playerRoles[roles[0]].append(player)
            except KeyError:
                self.playerRoles[roles[0]] = []
                self.playerRoles[roles[0]].append(player)
            roles.pop(0)

        return self.playerRoles

    def death(self, player):
        gameDone = False
        msg = ""  # placeholder
        dead = None
        for player in self.players:
            if player == player:
                dead = player
        self.players.remove(dead)
        deadRole = None
        for role in self.playerRoles:
            for player in role:
                if player == dead:
                    deadRole = role
        self.playerRoles[deadRole].remove(dead)

        # TODO: add flavor text

        # wincons
        if len(self.playerRoles['Mafia']) >= (len(self.playerRoles['Villager']) + len(self.playerRoles['Cop'])):
            # Mafia wins
            # TODO: add flavor messages
            gameDone = True
        elif len(self.playerRoles['Mafia']) <= 0:
            # Villagers win
            # TODO: add flavor messages
            gameDone = True

        return dead, msg, gameDone

    def day(self):
        # announce death by mafia
        # discussion (5 mins)
        sleep(300)
        # nominations
        # voting
        # announce death by vote

    def night(self):
        # wake mafia up
        # discussion (2 mins)
        sleep(120)
        # voting
        # wake cop up
        # nominate to see who is who


client = discord.Client()
maf = Mafia()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global gamestate, startchannel, mafiachannel, copchannel, generalchannel, maf
    if message.author == client.user:
        return

    if message.content.startswith('!start'):
        # make sure we have all the channels
        if not mafiachannel or not copchannel or not generalchannel:
            await message.channel.send('Not all channels set!')
            if not mafiachannel:
                await message.channel.send('Please set the mafia channel with the command !setmafia')
            if not copchannel:
                await message.channel.send('Please set the cop channel with the command !setcop')
            if not generalchannel:
                await message.channel.send('Please set the general channel with the command !setgeneral')
        # start the game
        if maf.gamestate == "initialized":
            startchannel = message.channel
            maf.increment_gamestate()
        elif gamestate == "waiting for players":
            maf.increment_gamestate()

    # nominations
    if message.channel == generalchannel and message.content.startswith('!nom') and \
            gamestate == "day nominations":
        if len(message.mentions) != 1:
            await generalchannel.send('You can only nominate one person. Please try again.')
        else:
            maf.nominations[str(message.mentions[0].name)] = 0
            maf.responded += 1
    # voting
    if message.content.startswith('!v'):
        if message.channel == generalchannel and gamestate == "day voting":
            if len(message.mentions) != 1:
                await message.channel.send('You can only vote for one person. Please try again.')
            else:
                try:
                    maf.nominations[str(message.mentions[0].name)] += 1
                except KeyError:
                    await message.channel.send('You cannot vote for someone who was not nominated. Please try again.')
        elif message.channel == mafiachannel and gamestate == "playing-night-mafia-voting":
            if len(message.mentions) != 1:
                await message.channel.send('You can only vote for one person. Please try again.')
            else:
                maf.death(message.mentions[0])
        elif message.channel == copchannel and gamestate == "playing-night-cop-voting":
            if len(message.mentions) != 1:
                await message.channel.send('You can only vote for one person. Please try again.')
            else:
                checkRole = None
                for role in maf.playerRoles:
                    for player in role:
                        if player == message.mentions[0]:
                            checkRole = role
                await message.channel.send(message.mentions[0].name + ' is a ' + checkRole)

    if message.content.startswith('!setmafia'):
        if message.channel == copchannel or message.channel == generalchannel:
            await message.channel.send("You can't set one channel to perform more than one function. "
                                       "Please select a different channel.")
            pass
        mafiachannel = message.channel
        if mafiachannel:
            await message.channel.send('overwriting mafia channel')
        else:
            await message.channel.send('mafia channel set')
    if message.content.startswith('!setcop'):
        if message.channel == mafiachannel or message.channel == generalchannel:
            await message.channel.send("You can't set one channel to perform more than one function. "
                                       "Please select a different channel.")
            pass
        copchannel = message.channel
        if copchannel:
            await message.channel.send('overwriting cop channel')
        else:
            await message.channel.send('cop channel set')
    if message.content.startswith('!setgeneral'):
        if message.channel == mafiachannel or message.channel == copchannel:
            await message.channel.send("You can't set one channel to perform more than one function. "
                                       "Please select a different channel.")
            pass
        generalchannel = message.channel
        if generalchannel:
            await message.channel.send('overwriting general channel')
        else:
            await message.channel.send('general channel set')

client.run(token)