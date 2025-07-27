-- ------------------------------------------------------
-- Crear la base de datos (ejecutar solo si no existe)
-- ------------------------------------------------------
-- CREATE DATABASE imdb;

-- Asegúrate de conectarte a la base de datos `imdb` antes de continuar

-- ------------------------------------------------------
-- Tabla: movies
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    year INTEGER,
    rating FLOAT,
    duration INTEGER,
    metascore FLOAT
);

-- ------------------------------------------------------
-- Tabla: actors
-- ------------------------------------------------------
CREATE TABLE IF NOT EXISTS actors (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    name VARCHAR
);

-- ------------------------------------------------------
-- Índices recomendados
-- ------------------------------------------------------

-- Índice en el año de la película (usado en búsquedas por década o filtrado)
CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);

-- Índice en movie_id para acelerar joins entre actores y películas
CREATE INDEX IF NOT EXISTS idx_actors_movie_id ON actors(movie_id);

-- Índice en el nombre del actor para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_actors_name ON actors(name);


-- ------------------------------------------------------
-- Vista: movie_actor_view
-- ------------------------------------------------------

-- Esta vista une información de películas y actores
-- Útil para consultas directas sin necesidad de hacer JOINs manuales
CREATE OR REPLACE VIEW movie_actor_view AS
SELECT
    m.id AS movie_id,
    m.title,
    m.year,
    m.rating,
    m.duration,
    m.metascore,
    a.name AS actor_name
FROM movies m
JOIN actors a ON m.id = a.movie_id;
