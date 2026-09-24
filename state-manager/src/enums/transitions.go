package enums

type TransitionState int

const (
	// TODO: rename / clarify the specific transition states
	transitionStateError TransitionState = iota

	// UPLINK TRANSITION STATES
	transitionStateBeginUplink
	transitionStateConnectionEstablished
	transitionStateAckReceived

	// UPLINK / DOWNLINK TRANSITION STATES
	transitionStateUplinkFinished
	transitionStateDownlinkingFinished

	// DISCONNECT TRANSITION STATES
	transitionStateDisconnecting
	transitionStateDisconnectCMDReceived
	transitionStateDisconnectComplete

	// EMERGENCY TRANSITION STATES
	transitionStateEnterEmergency
	transitionStateEmergencyInitiated
	transitionStateConnectionReceived
	transitionStateConnectionAckSent
	transitionStateEmergencyUplinkFinished
	transitionStateNoTransitionTriggered // NOT USED IN STATE MACHINE
)

var transitionStateStrs = [...]string{
	// TODO: rename / clarify the specific transition states
	"ERROR",

	// UPLINK TRANSITION STATES
	"BEGIN_UPLINK",
	"CONNECTION_ESTABLISHED",
	"ACK_RECEIVED",

	// UPLINK / DOWNLINK TRANSITION STATES
	"UPLINK_FINISHED",
	"DOWNLINKING_FINISHED",

	// DISCONNECT TRANSITION STATES
	"DISCONNECTING",
	"DISCONNECT_CMD_RECEIVED",
	"DISCONNECT_COMPLETE",

	// EMERGENCY TRANSITION STATES
	"ENTER_EMERGENCY",
	"EMERGENCY_INITIATED",
	"CONNECTION_RECEIVED",
	"CONNECTION_ACK_SENT",
	"EMERGENCY_UPLINK_FINISHED",
	"NO_TRANSITION_TRIGGERED", // NOT USED IN STATE MACHINE
}

var TransitionStates = struct {
	Error TransitionState

	BeginUplink           TransitionState
	ConnectionEstablished TransitionState
	AckReceived           TransitionState

	UplinkFinished      TransitionState
	DownlinkingFinished TransitionState

	Disconnecting         TransitionState
	DisconnectCMDReceived TransitionState
	DisconnectComplete    TransitionState

	EnterEmergency          TransitionState
	EmergencyInitiated      TransitionState
	ConnectionReceived      TransitionState
	ConnectionAckSent       TransitionState
	EmergencyUplinkFinished TransitionState
	NoTransitionTriggered   TransitionState
}{
	Error: transitionStateError,

	BeginUplink:           transitionStateBeginUplink,
	ConnectionEstablished: transitionStateConnectionEstablished,
	AckReceived:           transitionStateAckReceived,

	UplinkFinished:      transitionStateUplinkFinished,
	DownlinkingFinished: transitionStateDownlinkingFinished,

	Disconnecting:         transitionStateDisconnecting,
	DisconnectCMDReceived: transitionStateDisconnectCMDReceived,
	DisconnectComplete:    transitionStateDisconnectComplete,

	EnterEmergency:          transitionStateEnterEmergency,
	EmergencyInitiated:      transitionStateEmergencyInitiated,
	ConnectionReceived:      transitionStateConnectionReceived,
	ConnectionAckSent:       transitionStateConnectionAckSent,
	EmergencyUplinkFinished: transitionStateEmergencyUplinkFinished,
	NoTransitionTriggered:   transitionStateNoTransitionTriggered,
}

var transitionStateMap = make(map[string]TransitionState)

func init() {
	for i, str := range transitionStateStrs {
		transitionStateMap[str] = TransitionState(i)
	}
}

func (ts TransitionState) String() string {
	if ts < 0 || int(ts) >= len(transitionStateStrs) {
		ts = transitionStateError
	}
	return transitionStateStrs[ts]
}

func ParseTransitionState(str string) TransitionState {
	ts, ok := transitionStateMap[str]
	if !ok {
		return transitionStateError
	}
	return ts
}
