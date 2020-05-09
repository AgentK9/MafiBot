import discord
from random import shuffle
from time import sleep

# TODO: add config/persistent file
token = "your token here"
gamestate = None
startchannel = None

mafiachannel = None
copchannel = None
generalchannel = None

nominations = {}

maf = None


class Mafia:
    def __init__(self, playe: list):
        self.players = playe
        self.playerRoles = {}

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

    def death(self, playerID):
        gameDone = False
        msg = ""  # placeholder
        dead = None
        for player in self.players:
            if player.id == playerID:
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


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global gamestate, startchannel, mafiachannel, copchannel, generalchannel
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
        if not gamestate:
            startchannel = message.channel
            await startchannel.send('@Notifications:\n'
                                       'Starting game.\n '
                                       'Everyone wishing to participate, '
                                       'please react with a :thumbsup: to this message.')
            gamestate = "waitingForPlayers"
            print(gamestate)
        elif gamestate == "waitingForPlayers":
            await startchannel.send('Closing sign-ups.')
            sleep(5)
            await startchannel.send('Sign-ups closed. Sending out roles via DMs.')
            counter = 0
            gamestate = "setting up"
            print(gamestate)

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
                    maf = Mafia(await reaction.users().flatten())

            # DM and set roles for mafia, cops, villagers
            userRoles = maf.assignroles()
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

            gamestate = "playing"
            print(gamestate)
            gameDone = False
            while not gameDone:
                gamestate = "playing-night"
                gamestate = "playing-night-mafia"
                # mafia
                #  - discussion
                #  - voting
                # cops
                #  - voting
                gamestate = "playing-day"
                gamestate = "playing-day-discussion"
                gamestate = "playing-day-discussion-give chat perms"
                for user in maf.players:
                    await generalchannel.set_permissions(user, read_messages=True,
                                                         send_messages=True)
                sleep(300)
                gamestate = "playing-day-discussion-take chat perms"
                for user in maf.players:
                    await generalchannel.set_permissions(user, read_messages=True,
                                                         send_messages=False)
                gamestate = "playing-day-discussion-nominations"
                for user in maf.players:
                    await generalchannel.set_permissions(user, read_messages=True,
                                                         send_messages=True)
                    await generalchannel.send('@' + user.display_name + ', who do you nominate? '
                                                                        '(nominate with !nom @{person})')
                gamestate = "playing-day-discussion-voting"

    # nominations
    if message.channel == generalchannel and message.content.startswith('!nom') and \
            gamestate == "playing-day-discussion-nominations":
        if len(message.mentions) != 1:
            await generalchannel.send('You can only nominate one person. Please try again.')
        else:
            nominations[str(message.mentions[0].name)] = 0
    # voting
    if message.content.startswith('!v'):
        if message.channel == generalchannel and gamestate == "playing-day-discussion-voting":
            if len(message.mentions) != 1:
                await message.channel.send('You can only vote for one person. Please try again.')
            else:
                nominations[str(message.mentions[0].name)] += 1
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