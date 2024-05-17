# What is this?
This is Discord bot with minimal permissions and dependencies that
can both create an embedded server list and send message updates
when a pub server is filling up.

It is based of of the [Official Midair 2 Server List](https://midair2.gg/servers), so any changes
to this [API](https://api.midair2.gg/v1/server/public) will affect the bot.

# Features
- Embedded Server List in a specified channel, that will be update periodically (locked servers are hidden)
- Send update messages when a server begins to fill up

# Getting Started
Use [this link](https://discord.com/oauth2/authorize?client_id=1237575746315354192) to invite the bot to your server.

There is only one command, `/configure`, which opens an interactive configuration menu to setup and manage either the Server List or the Server Notifier.

**Note**: Make sure to limit which roles can use the bot's slash commands through the Discord Server Setttings.

# Hosting Yourself
It is highly reccomended to invite the bot to your server using [this link](https://discord.com/oauth2/authorize?client_id=1237575746315354192),
however, if you want to host your own instance of the bot then you will need to configure the following:

### Requirements:
- python >= 3.10
- [sqlite3](https://sqlite.org/cli.html)
### Setup/create the venv
- `python3 -m venv .venv`
- `source .venv/bin/activate`
Note: This needs to be done every time
### Pip install the requirements
- `pip install -U -r requirements.txt`
### Setup the sqlite3 database
- `sqlite3 your-db-name.db < schema.sql`

There are no migrations, since the schema is very simple and I didn't feel like handling them
### Create a .env with:
Note: You can find your bot's token after creating a new application
in the [Discord Developer Portal](https://discord.com/developers/applications)
```conf
TOKEN=your-bot-token
MIDAIR_SERVERS_API_URL=https://api.midair2.gg/v1/server/public
DB_NAME=your-db-name
```

### Run the bot
- `python3 -m launcher.py`
