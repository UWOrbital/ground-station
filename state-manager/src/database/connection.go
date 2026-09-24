package database

import (
	"context"
	"fmt"
	"os"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"state-manager/src/database/gen"
)

var pool *pgxpool.Pool

var queries *gen.Queries

func getenv(key string) string {
	val := os.Getenv(key)
	if val == "" {
		panic(fmt.Sprintf("environment variable %v is missing/empty", key))
	}
	return val
}

func connString() string {
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s",
		getenv("DB_USER"),
		getenv("DB_PASSWORD"),
		getenv("DB_HOST"),
		getenv("DB_PORT"),
		getenv("DB_NAME"),
	)
}

// InitDB sets up the connection pool. Call once at startup.
func InitDB(ctx context.Context) error {
	p, err := pgxpool.New(ctx, connString())
	if err != nil {
		return fmt.Errorf("failed to create db pool: %w", err)
	}
	pool = p
	queries = gen.New(p)
	return nil
}

// Queries returns the sqlc-generated query set bound to the pool.
// InitDB must have been called first.
func Queries() *gen.Queries {
	if queries == nil {
		panic("database: InitDB must be called before using the database")
	}
	return queries
}

// Close shuts down the pool. Call at shutdown.
func Close() {
	if pool != nil {
		pool.Close()
	}
	pool, queries = nil, nil
}

// WithTx runs fn inside a transaction, committing on success
// and rolling back if fn returns an error.
func WithTx[R any](ctx context.Context, fn func(tx pgx.Tx) (R, error)) (R, error) {
	var zero R

	tx, err := pool.Begin(ctx)
	if err != nil {
		return zero, fmt.Errorf("failed to begin transaction: %w", err)
	}

	result, err := fn(tx)
	if err != nil {
		if rbErr := tx.Rollback(ctx); rbErr != nil {
			return zero, fmt.Errorf("rollback failed: %v (original error: %w)", rbErr, err)
		}
		return zero, err
	}

	if err := tx.Commit(ctx); err != nil {
		return zero, fmt.Errorf("commit failed: %w", err)
	}

	return result, nil
}

func WithConn[R any](ctx context.Context, fn func(conn *pgxpool.Conn) (R, error)) (R, error) {
	var zero R
	conn, err := pool.Acquire(ctx)
	if err != nil {
		return zero, fmt.Errorf("failed to acquire connection: %w", err)
	}
	defer conn.Release()

	return fn(conn)
}
