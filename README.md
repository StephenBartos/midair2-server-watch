# What is this?
This is Discord bot with minimal permissions and dependencies that
can both create an embedded server list and send message updates
when a pub server is filling up.

It is based off of the [Official Midair 2 Server List](https://midair2.gg/servers), so any changes
to this [API](https://api.midair2.gg/v1/server/public) will affect the bot.

# Features
- Embedded Server List in a specified channel, that will be update periodically (locked servers are hidden)
- Send update messages when a server begins to fill up

# Getting Started
Use [this link](https://discord.com/oauth2/authorize?client_id=1237575746315354192) to invite the bot to your server.

There is only one command, `/configure`, which opens an interactive configuration menu to setup and manage either the Server List or the Server Notifier.

### IMPORTANT: Make sure to limit which roles can use the bot's slash commands in your Discord server's setttings.

By default, @everyone may use the command

# Self Hosting
It is highly reccomended to invite the bot to your server using [this link](https://discord.com/oauth2/authorize?client_id=1237575746315354192),
but see [Self Hosting](docs/self-hosting.md) for instructions if you *really* want to host it yourself.
