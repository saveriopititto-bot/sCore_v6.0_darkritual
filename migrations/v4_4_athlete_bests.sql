-- Migration v4.4: Athlete Best Efforts (PRs)
CREATE TABLE IF NOT EXISTS athlete_bests (
    athlete_id BIGINT REFERENCES athletes(id),
    distance_type TEXT, -- '5k', '10k', 'Half-Marathon', etc.
    best_time INTEGER,  -- tempo in secondi
    activity_id BIGINT, -- riferimento alla corsa specifica
    achieved_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (athlete_id, distance_type)
);
