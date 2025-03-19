CREATE TABLE IF NOT EXISTS npcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    background TEXT,
    appearance TEXT,
    personality TEXT,
    goals TEXT,
    assets TEXT,
    memory TEXT
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_id INTEGER,
    player_input TEXT,
    npc_response TEXT,
    FOREIGN KEY (npc_id) REFERENCES npcs(id)
);

CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_description TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
); 