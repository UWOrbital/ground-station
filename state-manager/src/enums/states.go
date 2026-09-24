package enums

type MachineState int

const (
	// UPLINK STATES
	machineStateDisconnected MachineState = iota
	machineStateAttemptingConnection
	machineStateAwaitingAck
	machineStateUplinking
	machineStateDownlinking

	// DISCONNECT STATES
	machineStateAwaitingDisconnect
	machineStateSendDisconnectAck

	// EMERGENCY STATES
	machineStateEnteringEmergency
	machineStateAwaitingConnection
	machineStateSendConnectionAck
	machineStateEmergencyUplink
	machineStateServerSideError
)

var machineStateStrs = [...]string{
	// UPLINK STATES
	"DISCONNECTED",
	"ATTEMPTING_CONNECTION",
	"AWAITING_ACK",
	"UPLINKING",
	"DOWNLINKING",

	// DISCONNECT STATES
	"AWAITING_DISCONNECT",
	"SEND_DISCONNECT_ACK",

	// EMERGENCY STATES
	"ENTERING_EMERGENCY",
	"AWAITING_CONNECTION",
	"SEND_CONNECTION_ACK",
	"EMERGENCY_UPLINK",
	"SERVER_SIDE_ERROR",
}

var MachineStates = struct {
	// UPLINK STATES
	Disconnected         MachineState
	AttemptingConnection MachineState
	AwaitingAck          MachineState
	Uplinking            MachineState
	Downlinking          MachineState

	// DISCONNECT STATES
	AwaitingDisconnect MachineState
	SendDisconnectAck  MachineState

	// EMERGENCY STATES
	EnteringEmergency  MachineState
	AwaitingConnection MachineState
	SendConnectionAck  MachineState
	EmergencyUplink    MachineState
	ServerSideError    MachineState
}{
	Disconnected:         machineStateDisconnected,
	AttemptingConnection: machineStateAttemptingConnection,
	AwaitingAck:          machineStateAwaitingAck,
	Uplinking:            machineStateUplinking,
	Downlinking:          machineStateDownlinking,

	AwaitingDisconnect: machineStateAwaitingDisconnect,
	SendDisconnectAck:  machineStateSendDisconnectAck,

	EnteringEmergency:  machineStateEnteringEmergency,
	AwaitingConnection: machineStateAwaitingConnection,
	SendConnectionAck:  machineStateSendConnectionAck,
	EmergencyUplink:    machineStateEmergencyUplink,
	ServerSideError:    machineStateServerSideError,
}

var machineStateMap = make(map[string]MachineState)

func init() {
	for i, str := range machineStateStrs {
		machineStateMap[str] = MachineState(i)
	}
}

func (ms MachineState) String() string {
	if ms < 0 || int(ms) >= len(machineStateStrs) {
		ms = machineStateServerSideError
	}
	return machineStateStrs[ms]
}

func ParseMachineState(str string) MachineState {
	ms, ok := machineStateMap[str]
	if !ok {
		return machineStateServerSideError
	}
	return ms
}
