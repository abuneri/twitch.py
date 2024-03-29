# twitch.py
**Python 3.7** wrapper around the Twitch's Helix and IRC API. General
design inspired by the [discord.py](https://github.com/Rapptz/discord.py/) library.


[Documentation](https://twitchpi.readthedocs.io/en/latest/)
    - As you can see, there isn't much here yet :) I'm waiting until the library gets more complete/more mature as right now some major redesigns could potentially happen

## Key Features

- Modern user-friendly asynchronous API using [aiohttp](https://aiohttp.readthedocs.io/en/stable/) and [websockets](https://websockets.readthedocs.io/en/stable/)
- Proper HTTP rate limit handling
- 100% coverage of the supported **new** Twitch API (**v5 not supported**)*
- 100% coverage of the supported Chatbot/IRC gateway*
- PEP 8 Compliant
- Rich built-in commands plugin featuring:
    - Custom type registry
    - Optional fuzzy matching on commands

\* The underlying HTTP and Websocket implementations support 100%, but it may not be exposed in the client or models yet (soon:tm:)

## Limitations
- Currently only Python 3.7 is supported and tested

## Simple Examples
A glimpse into the library to get you started!
#### Base Client: Joining a channel and echoing the chat to your console
```python
import twitch

client = twitch.Client()


@client.event(twitch.Event.CONNECTED)
async def on_connected(user):
    print(f'Bot username: {user.login}')
    print(f'Bot id: {user.id}')
    await client.join_channel('channel_name')


@client.event(twitch.Event.MESSAGE)
async def message_listener(message):
    print(f'[#{message.channel.name}] {message.author.login}: {message.content}')

client.run('login_name', 'access_token', 'client_id')
```
-----------

#### Commands Plugin: Ping-Pong
The commands plugin makes it possible to get a ping-pong bot running in **under 10 lines of actual code!!**
```python
from twitch.plugins.commands import Bot

bot = Bot(command_prefix='>', channels=['channel_name'])


@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run('login_name', 'access_token', 'client_id')
```
-----------

#### Commands Plugin: Register Custom Types
The commands plugin provides a method of registering custom types.
This is allows you to define a format for your command parameters and then
directly map them to custom types you've defined.
```python
from twitch.plugins.commands import Bot

class Foo:
    def __init__(self, p1, p2):
        self.p = (p1, p2)

    def stuff(self):
        # do stuff with self.p
        pass

bot = Bot(command_prefix='@', channels=['channel_name'])

@bot.register(Foo)
def reg_foo(s: str):
    s_parts = s.split(';')
    if len(s_parts) == 2:
        s1 = s_parts[0]
        s2 = s_parts[1]
        return Foo(s1, s2)
    return None

@bot.command()
async def foo(ctx, foo_param: Foo):
    if not foo_param:
        return

    the_stuff = foo_param.stuff()
    # ... do things with the_stuff ...

bot.run('login_name', 'access_token', 'client_id')
```

-----------
#### Commands Plugin: Fuzzy Matching command
The commands plugin provides built-in fuzzy matching. This is opt-in,
no fuzzy matching happens by default.

You can pass in a `commands.FuzzyMatch` object to your command definition. In this
example, we are using the simple ratio algorithm with a threshold of 85.

This means if a user types `?meadcount`, if it matches `headcount` by >= 85,
the command will still get invoked.
```python
from twitch.plugins.commands import Bot, FuzzyMatch, FuzzyRatio

bot = Bot(command_prefix='?', channels=['channel_name'])

fuzzy = FuzzyMatch(ratio=FuzzyRatio.SIMPLE, threshold=85)


@bot.command(fuzzy_match=fuzzy)
async def headcount(ctx, val: int):
    await ctx.send(f'matched, double the user\'s value is {val * 2}')

bot.run('login_name', 'access_token', 'client_id')
```
-----------

``login_name``:
- The account name of your bot

``access_token``:
- Token received via one of the [authentication](#authentication) methods. The token can be prefixed with ``oauth:``, but **it doesn't have to be**, the library handles both cases.

``client_id``:
- Client ID of your OAuth 2 application created in the [developer console](https://dev.twitch.tv/console/apps)

## Authentication
https://twitchapps.com/tokengen/

You have two ways to get the access token required
1. Use an [existing service](https://twitchapps.com/tokengen/) to retrieve an access token for your application
   1. Make sure you are using the correct [scopes](https://dev.twitch.tv/docs/authentication/scopes/) for both the Rest API and the Websocket API
2. Roll your own with [Twitch's OAuth 2.0 authorization flow](https://dev.twitch.tv/docs/authentication#getting-tokens)
