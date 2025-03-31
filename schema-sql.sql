DROP TABLE IF EXISTS bom_items;

CREATE TABLE bom_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    design_title TEXT NOT NULL,
    description TEXT,
    type TEXT,
    designator TEXT,
    qty INTEGER,
    manufacturer TEXT,
    part_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
