CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen' CHECK (role IN ('citizen','officer','admin')),
    reputation REAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    category TEXT NOT NULL,
    category_confidence REAL,
    description TEXT,
    image_path TEXT NOT NULL,
    geom geography(Point, 4326) NOT NULL,
    embedding vector(512),
    severity REAL NOT NULL DEFAULT 0.5,
    priority TEXT NOT NULL DEFAULT 'P3' CHECK (priority IN ('P1','P2','P3','P4')),
    priority_score REAL,
    trust_score REAL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','in_progress','resolved','needs_review')),
    department_id INT REFERENCES departments(id),
    parent_id INT REFERENCES complaints(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS complaints_geom_idx ON complaints USING GIST (geom);

CREATE TABLE IF NOT EXISTS support_votes (
    complaint_id INT REFERENCES complaints(id),
    user_id INT REFERENCES users(id),
    PRIMARY KEY (complaint_id, user_id)
);

CREATE TABLE IF NOT EXISTS complaint_events (
    id SERIAL PRIMARY KEY,
    complaint_id INT REFERENCES complaints(id),
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    detail JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO departments (name) VALUES
 ('Road Infrastructure'),('Sanitation'),('Public Utilities / Water'),
 ('Electricity / Street Lighting'),('Horticulture / Parks'),('Manual Review')
ON CONFLICT DO NOTHING;
