package database

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"

	"state-manager/src/database/gen"
	"state-manager/src/enums"
)

// ErrInvalidRow is returned when a row fails a data-integrity check that would
// normally be enforced by the ORM/DB layer.
var ErrInvalidRow = errors.New("invalid row")

// GetNextSession returns the start time of the next upcoming session — the
// soonest PENDING session with a start_time still in the future. Returns nil
// if no such session exists.
func GetNextSession(ctx context.Context) (*time.Time, error) {
	startTime, err := Queries().GetNextSession(ctx, gen.SessionstatusPENDING)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get next session: %w", err)
	}
	return &startTime, nil
}

// GetNextSessionID returns the ID of the next upcoming pending session, or nil
// if no such session exists.
func GetNextSessionID(ctx context.Context) (*uuid.UUID, error) {
	id, err := Queries().GetNextSessionID(ctx, gen.SessionstatusPENDING)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get next session id: %w", err)
	}
	return &id, nil
}

// UpdateCurrentSessionStatus sets the status of the session starting at
// startTime.
func UpdateCurrentSessionStatus(
	ctx context.Context,
	status enums.SessionStatus,
	startTime time.Time,
) error {
	sessionStatus, err := sessionStatus(status)
	if err != nil {
		return err
	}
	if startTime.IsZero() {
		return fmt.Errorf("failed to update session status: %w: start time is unset", ErrInvalidRow)
	}

	err = Queries().UpdateCurrentSessionStatus(ctx, gen.UpdateCurrentSessionStatusParams{
		Status:    sessionStatus,
		StartTime: startTime,
	})
	if err != nil {
		return fmt.Errorf("failed to update session status: %w", err)
	}
	return nil
}

// GetMainCommandByID fetches a single row from main.commands. Returns nil if no
// command with that ID exists.
func GetMainCommandByID(ctx context.Context, commandID int32) (*gen.MainCommand, error) {
	command, err := Queries().GetMainCommandByID(ctx, commandID)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get main command %d: %w", commandID, err)
	}
	if err := validateMainCommand(command); err != nil {
		return nil, fmt.Errorf("main command %d: %w", commandID, err)
	}
	return &command, nil
}

// GetAllCommandsByStatus fetches all rows from transactional.commands matching a
// given status.
func GetAllCommandsByStatus(
	ctx context.Context,
	status enums.CommandStatus,
) ([]gen.TransactionalCommand, error) {
	commandStatus, err := commandStatus(status)
	if err != nil {
		return nil, err
	}

	commands, err := Queries().GetAllCommandsByStatus(ctx, commandStatus)
	if err != nil {
		return nil, fmt.Errorf("failed to get %v commands: %w", status, err)
	}
	return commands, nil
}

// GetAllCommandsNextSession fetches the commands with the given status that
// belong to the next upcoming pending session. Returns an empty slice if there
// is no such session.
func GetAllCommandsNextSession(
	ctx context.Context,
	status enums.CommandStatus,
) ([]gen.TransactionalCommand, error) {
	commandStatus, err := commandStatus(status)
	if err != nil {
		return nil, err
	}

	commands, err := Queries().GetAllCommandsNextSession(ctx, gen.GetAllCommandsNextSessionParams{
		Status:   gen.SessionstatusPENDING,
		Status_2: commandStatus,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get %v commands for next session: %w", status, err)
	}
	return commands, nil
}

// UpdateCommandStatus moves a command to a new status. Used in BuildQueue
// (-> SCHEDULED), QueueToPacket (-> ONGOING) and ClearQueue (-> COMPLETED).
func UpdateCommandStatus(ctx context.Context, commandID uuid.UUID, status enums.CommandStatus) error {
	commandStatus, err := commandStatus(status)
	if err != nil {
		return err
	}

	err = Queries().UpdateCommandStatus(ctx, gen.UpdateCommandStatusParams{
		Status: commandStatus,
		ID:     commandID,
	})
	if err != nil {
		return fmt.Errorf("failed to update status of command %v: %w", commandID, err)
	}
	return nil
}

// UpdateCommandResponse records the OBC response for a command.
func UpdateCommandResponse(ctx context.Context, commandID uuid.UUID, response string) error {
	err := Queries().UpdateCommandResponse(ctx, gen.UpdateCommandResponseParams{
		Response: &response,
		ID:       commandID,
	})
	if err != nil {
		return fmt.Errorf("failed to update response of command %v: %w", commandID, err)
	}
	return nil
}

// CreateTelemetry inserts one telemetry value into transactional.telemetry.
// timestamp is normalized to UTC before insertion.
func CreateTelemetry(ctx context.Context, telemetryType int32, value string, timestamp time.Time) error {
	err := Queries().CreateTelemetry(ctx, gen.CreateTelemetryParams{
		ID:        uuid.New(),
		Type:      telemetryType,
		Value:     &value,
		Timestamp: timestamp.UTC(),
	})
	if err != nil {
		return fmt.Errorf("failed to create telemetry of type %d: %w", telemetryType, err)
	}
	return nil
}

// ClearTelemetryByType deletes every telemetry row whose type_ matches
// telemetryType, and returns the number of rows deleted.
func ClearTelemetryByType(ctx context.Context, telemetryType int32) (int64, error) {
	deleted, err := Queries().ClearTelemetryByType(ctx, telemetryType)
	if err != nil {
		return 0, fmt.Errorf("failed to clear telemetry of type %d: %w", telemetryType, err)
	}
	return deleted, nil
}

// sessionStatus converts a SessionStatus into the value the sessionstatus
// Postgres enum expects.
func sessionStatus(status enums.SessionStatus) (gen.Sessionstatus, error) {
	if status == enums.SessionStatuses.EnumError {
		return "", fmt.Errorf("%w: unknown session status %d", ErrInvalidRow, status)
	}
	return gen.Sessionstatus(status.String()), nil
}

// commandStatus converts a CommandStatus into the value the commandstatus
// Postgres enum expects.
func commandStatus(status enums.CommandStatus) (gen.Commandstatus, error) {
	if status == enums.CommandStatuses.EnumError {
		return "", fmt.Errorf("%w: unknown command status %d", ErrInvalidRow, status)
	}
	return gen.Commandstatus(status.String()), nil
}

// validateMainCommand runs the data-integrity checks the ORM used to enforce on
// main.commands rows.
func validateMainCommand(command gen.MainCommand) error {
	switch {
	case command.DataSize < 0:
		return fmt.Errorf("%w: data_size must be >= 0", ErrInvalidRow)
	case command.TotalSize <= 0:
		return fmt.Errorf("%w: total_size must be > 0", ErrInvalidRow)
	case command.Priority < 0:
		return fmt.Errorf("%w: priority must be >= 0", ErrInvalidRow)
	}

	// params and format must either both be absent, or both list the same
	// number of comma-separated values.
	// TODO: check that the params have valid types
	switch {
	case command.Params == nil && command.Format == nil:
		return nil
	case command.Params == nil:
		return fmt.Errorf("%w: missing params", ErrInvalidRow)
	case command.Format == nil:
		return fmt.Errorf("%w: missing format", ErrInvalidRow)
	case strings.Count(*command.Params, ",") != strings.Count(*command.Format, ","):
		return fmt.Errorf("%w: params and format do not have the same number of values", ErrInvalidRow)
	}
	return nil
}
