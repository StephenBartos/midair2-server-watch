# Self Hosting
It is highly reccomended to invite the bot to your server using [this link](https://discord.com/oauth2/authorize?client_id=1237575746315354192),
however, if you want to host your own instance of the bot then you will need to configure the following:

### Requirements:
- python >= 3.10
- [sqlite3](https://sqlite.org/cli.html)
### Setup/create the venv
- `python3 -m venv .venv`
- `source .venv/bin/activate` (Note: This needs to be done every time)
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
### Sync the commands with your server
After the bot is both invited to your server and running, sync it by typing this anyhwere in your server:
> @bot_name sync

The bot should reply with the number of commands synced
