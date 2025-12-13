CREATE TABLE IF NOT EXISTS modifications (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS hashing_methods (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS images (
  id SERIAL PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  modification_id INTEGER NOT NULL REFERENCES modifications(id)
);

CREATE TABLE IF NOT EXISTS hashes (
  id SERIAL PRIMARY KEY,
  hash TEXT NOT NULL,
  image_id INTEGER NOT NULL REFERENCES images(id),
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
ADD CONSTRAINT unique_image_hash UNIQUE (image_id, hashing_method_id, hash);

