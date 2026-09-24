package enums

type SessionStatus int

const (
	sessionPending SessionStatus = iota
	sessionScheduled
	sessionOngoing
	sessionCompleted
	sessionEnumError
)

var sessionStatusStrs = [...]string{
	"PENDING",    // Initial state of a session. Optional or can start at SCHEDULED status
	"SCHEDULED",  // Session has been scheduled. GS has not received any data yet but the start time is known
	"ONGOING",    // Session has been started. GS is receiving data
	"COMPLETED",  // Session is complete. GS has received all the data for the session. Final state of session
	"ENUM_ERROR", // Enum reading error value
}

var SessionStatuses = struct {
	Pending   SessionStatus
	Scheduled SessionStatus
	Ongoing   SessionStatus
	Completed SessionStatus
	EnumError SessionStatus
}{
	Pending:   sessionPending,
	Scheduled: sessionScheduled,
	Ongoing:   sessionOngoing,
	Completed: sessionCompleted,
	EnumError: sessionEnumError,
}

var sessionStatusMap = make(map[string]SessionStatus)

func init() {
	for i, str := range sessionStatusStrs {
		sessionStatusMap[str] = SessionStatus(i)
	}
}

func (ss SessionStatus) String() string {
	if ss < 0 || int(ss) >= len(sessionStatusStrs) {
		ss = sessionEnumError
	}
	return sessionStatusStrs[ss]
}

func ParseSessionStatus(str string) SessionStatus {
	ss, ok := sessionStatusMap[str]
	if !ok {
		return sessionEnumError
	}
	return ss
}
