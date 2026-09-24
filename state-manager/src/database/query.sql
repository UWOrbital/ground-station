-- name: GetNextSession :one
-- Returns the start_time of the next upcoming session -- the soonest PENDING
-- session with a start_time still in the future.
SELECT start_time
FROM transactional.sessions
WHERE status = $1 AND start_time > now()
ORDER BY start_time ASC
LIMIT 1;

-- name: GetNextSessionID :one
-- Returns the ID of the next upcoming pending session.
SELECT id
FROM transactional.sessions
WHERE status = $1
  AND start_time > now()
ORDER BY start_time ASC
LIMIT 1;

-- name: UpdateCurrentSessionStatus :exec
UPDATE transactional.sessions
SET status = $1
WHERE id = (
    SELECT id
    FROM transactional.sessions s
    WHERE s.start_time = $2
    ORDER BY s.start_time ASC
    LIMIT 1
);

-- name: GetMainCommandByID :one
-- Fetches a single row from main.commands.
SELECT id, name, params, format, data_size, total_size, priority
FROM main.commands
WHERE id = $1;

-- name: GetAllCommandsByStatus :many
-- Fetches all rows from transactional.commands matching a given status.
SELECT *
FROM transactional.commands
WHERE status = $1;

-- name: GetAllCommandsNextSession :many
-- Fetches the commands with the given status that belong to the next upcoming
-- pending session. Yields no rows when there is no such session.
SELECT c.*
FROM transactional.commands c
WHERE c.session_id = (
    SELECT s.id
    FROM transactional.sessions s
    WHERE s.status = $1
      AND s.start_time > now()
    ORDER BY s.start_time ASC
    LIMIT 1
  )
  AND c.status = $2;

-- name: UpdateCommandStatus :exec
UPDATE transactional.commands
SET status = $1
WHERE id = $2;

-- name: UpdateCommandResponse :exec
UPDATE transactional.commands
SET response = $1
WHERE id = $2;

-- name: CreateTelemetry :exec
-- Insert one telemetry value into transactional.telemetry.
INSERT INTO transactional.telemetry (
    id,
    type_,
    value,
    timestamp
)
VALUES ($1, $2, $3, $4);

-- name: ClearTelemetryByType :execrows
-- Deletes every telemetry row whose type_ matches the given type.
DELETE FROM transactional.telemetry
WHERE type_ = $1;
