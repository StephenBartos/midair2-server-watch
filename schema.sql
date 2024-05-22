-- Initial table definitions; not setting up any migrations for now,
-- since this should be relatively simple.

CREATE TABLE IF NOT EXISTS guild (
    id INTEGER PRIMARY KEY NOT NULL,
    is_blocked INTEGER DEFAULT FALSE
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS server_list (
    guild_id BIGINT PRIMARY KEY NOT NULL REFERENCES guild(id) ON UPDATE CASCADE ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,
    message_id BIGINT,
    title TEXT
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_server_list_message_id ON server_list (message_id);

CREATE TABLE IF NOT EXISTS notice_feed (
    guild_id BIGINT PRIMARY KEY NOT NULL REFERENCES guild(id) ON UPDATE CASCADE ON DELETE CASCADE,
    channel_id BIGINT NOT NULL,
    role_id BIGINT,
    last_message_id BIGINT,
    last_message_at TIMESTAMP
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS idx_notice_feed_role_id ON notice_feed (role_id);
CREATE INDEX IF NOT EXISTS idx_notice_feed_last_message_id ON notice_feed (last_message_id);
CREATE INDEX IF NOT EXISTS idx_notice_feed_last_mention_at ON notice_feed (last_message_at);
