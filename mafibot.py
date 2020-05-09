import discord
from random import shuffle
from time import sleep

token = "your token here"


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
    gamestate = None
    startchannel = None

    mafiachannel = None
    copchannel = None
    generalchannel = None

    maf = None
    if message.author == client.user:
        return

    if message.content.startswith('!start') and message.channel.category_id != "Mafia":
        if not gamestate:
            startchannel = message.channel
            await startchannel.send('@Notifications:\n'
                                       'Starting game.\n '
                                       'Everyone wishing to participate, '
                                       'please react with a :thumbsup: to this message.')
            gamestate = "waitingForPlayers"
        elif gamestate == "waitingForPlayers":
            await startchannel.send('Closing sign-ups.')
            sleep(5)
            await startchannel.send('Sign-ups closed. Sending out roles via DMs.')
            counter = 0

            signupMessage = None
            async for message in startchannel.history(limit=50):
                if message.author == client.user:
                    counter += 1
                if counter == 3:
                    signupMessage = message
                break

            # get all users who reacted
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
                                                                 send_messages=True)
                    elif role == "Cop":
                        await copchannel.set_permissions(user, read_messages=True,
                                                               send_messages=True)
                    else:
                        await mafiachannel.set_permissions(user, read_messages=False,
                                                           send_messages=False)
                        await copchannel.set_permissions(user, read_messages=False,
                                                         send_messages=False)

                    await generalchannel.set_permissions(user, send_messages=True)

            # @ all the mafia and tell them that they're mafia
            for user in userRoles["Mafia"]:
                await mafiachannel.send('@' + user.display_name)
            await mafiachannel.send('You are mafia')

            # @ all the cops and tell them that they're cops
            for user in userRoles["Cop"]:
                await copchannel.send('@' + user.display_name)
            await copchannel.send('You are cops')








client.run(token)