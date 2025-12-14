CREATE TABLE IF NOT EXISTS modifications (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS hashing_methods (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS images (
  id SERIAL PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  user_id INTEGER REFERENCES users(id),
  UNIQUE(path,user_id)
);

CREATE TABLE IF NOT EXISTS modified_images (
  id SERIAL PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  image_id INTEGER NOT NULL REFERENCES images(id),
  modification_id INTEGER NOT NULL REFERENCES modifications(id)
);

CREATE TABLE IF NOT EXISTS hashes (
  id SERIAL PRIMARY KEY,
  hash TEXT NOT NULL,
  modified_image_id INTEGER NOT NULL REFERENCES modified_images(id),
  hashing_method_id INTEGER NOT NULL REFERENCES hashing_methods(id)
);

CREATE TABLE IF NOT EXISTS matches (
  id SERIAL PRIMARY KEY,
  hamming_distance DOUBLE PRECISION NOT NULL,
  hash_id1 INTEGER NOT NULL REFERENCES hashes(id),
  hash_id2 INTEGER NOT NULL REFERENCES hashes(id)
);

-- Ensures no duplicate hashes for unique images. This is given that path is UNIQUE because it holds a hash to a specific image.
ALTER TABLE hashes
ADD CONSTRAINT unique_image_hash UNIQUE (modified_image_id, hashing_method_id, hash);

INSERT INTO users (name) VALUES ('undefined');
