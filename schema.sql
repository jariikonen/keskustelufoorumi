CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    registered_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    topic TEXT UNIQUE,
    description TEXT,
    restricted BOOL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics,
    parent_id INTEGER REFERENCES messages DEFAULT NULL,
    writer_id INTEGER REFERENCES users,
    heading TEXT,
    content TEXT,
    sent_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE topic_access_rights (
    user_id INTEGER REFERENCES users,
    topic_id INTEGER REFERENCES topics
);
