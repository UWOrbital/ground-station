package enums

type CommandStatus int

const (
	commandPending CommandStatus = iota
	commandScheduled
	commandOngoing
	commandCancelled
	commandFailed
	commandCompleted
	commandEnumError
)

var commandStatusStrs = [...]string{
	"PENDING",
	"SCHEDULED",
	"ONGOING",
	"CANCELLED",
	"FAILED",
	"COMPLETED",
	"ENUM_ERROR",
}

var CommandStatuses = struct {
	Pending   CommandStatus
	Scheduled CommandStatus
	Ongoing   CommandStatus
	Cancelled CommandStatus
	Failed    CommandStatus
	Completed CommandStatus
	EnumError CommandStatus
}{
	Pending:   commandPending,
	Scheduled: commandScheduled,
	Ongoing:   commandOngoing,
	Cancelled: commandCancelled,
	Failed:    commandFailed,
	Completed: commandCompleted,
	EnumError: commandEnumError,
}

var commandStatusMap = make(map[string]CommandStatus)

func init() {
	for i, str := range commandStatusStrs {
		commandStatusMap[str] = CommandStatus(i)
	}
}

func (cs CommandStatus) String() string {
	if cs < 0 || int(cs) >= len(commandStatusStrs) {
		cs = commandEnumError
	}
	return commandStatusStrs[cs]
}

func ParseCommandStatus(str string) CommandStatus {
	cs, ok := commandStatusMap[str]
	if !ok {
		return commandEnumError
	}
	return cs
}
