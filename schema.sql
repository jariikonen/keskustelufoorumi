CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    role TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role_id INTEGER REFERENCES roles,
    registered_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    topic TEXT UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics,
    refers_to INTEGER REFERENCES messages,
    thread_id INTEGER REFERENCES messages,
    writer_id INTEGER REFERENCES users,
    heading TEXT,
    content TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    last_update TIMESTAMP DEFAULT NULL
);

CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    group_name TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE group_memberships (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups,
    user_id INTEGER REFERENCES users,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (group_id, user_id)
);

CREATE TABLE topic_privileges (
    group_id INTEGER REFERENCES groups,
    topic_id INTEGER REFERENCES topics,
    know_priv BOOLEAN DEFAULT false,
    read_priv BOOLEAN DEFAULT false,
    write_priv BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (group_id, topic_id)
);

CREATE TABLE pending_message_deletions (
    message_id INTEGER REFERENCES messages UNIQUE PRIMARY KEY,
    deleter_role INTEGER REFERENCES roles,
    deleted_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pending_user_deletions (
    user_id INTEGER REFERENCES users UNIQUE PRIMARY KEY,
    deleted_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO roles (role) VALUES ('super');
INSERT INTO roles (role) VALUES ('admin');
INSERT INTO roles (role) VALUES ('user');
INSERT INTO roles (role) VALUES ('deleted');

INSERT INTO groups (group_name) VALUES ('SUPER');
INSERT INTO groups (group_name) VALUES ('ADMIN');
INSERT INTO groups (group_name) VALUES ('ALL');

/* Default accounts: admin, 12345; super, 12345 */
INSERT INTO users (username, password, role_id)
VALUES (
    'admin',
    'pbkdf2:sha256:260000$9L0FBcnLCPdRrl6o$3f8c615fd19ea17899990702c52eb885e6b0e88f3852f9a4625a09eb92ace644',
    2
);
INSERT INTO users (username, password, role_id)
VALUES (
    'super',
    'pbkdf2:sha256:260000$9L0FBcnLCPdRrl6o$3f8c615fd19ea17899990702c52eb885e6b0e88f3852f9a4625a09eb92ace644',
    1
);
