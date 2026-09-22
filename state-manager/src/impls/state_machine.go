package impls

import (
	"state-manager/src/enums"
)

type StateMachine struct {
	State             enums.MachineState
	TransitionalState enums.TransitionState
}

func NewStateMachine(initState enums.MachineState) *StateMachine {
	return &StateMachine{
		State:             initState,
		TransitionalState: enums.TransitionStates.NoTransitionTriggered,
	}
}

func (sm *StateMachine) SwitchState(transitionalState enums.TransitionState) {
	sm.TransitionalState = transitionalState

	switch sm.State {
	case enums.MachineStates.Disconnected:
		switch sm.TransitionalState {
		case enums.TransitionStates.EnterEmergency:
			sm.State = enums.MachineStates.EnteringEmergency
		case enums.TransitionStates.BeginUplink:
			sm.State = enums.MachineStates.AttemptingConnection
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.AttemptingConnection:
		switch sm.TransitionalState {
		case enums.TransitionStates.ConnectionEstablished:
			sm.State = enums.MachineStates.AwaitingAck
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.AwaitingAck:
		switch sm.TransitionalState {
		case enums.TransitionStates.AckReceived:
			sm.State = enums.MachineStates.Uplinking
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.Uplinking:
		switch sm.TransitionalState {
		case enums.TransitionStates.UplinkFinished:
			sm.State = enums.MachineStates.Downlinking
		case enums.TransitionStates.Disconnecting:
			sm.State = enums.MachineStates.AwaitingDisconnect
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.AwaitingDisconnect:
		switch sm.TransitionalState {
		case enums.TransitionStates.DisconnectCMDReceived:
			sm.State = enums.MachineStates.SendDisconnectAck
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.SendDisconnectAck:
		switch sm.TransitionalState {
		case enums.TransitionStates.DisconnectComplete:
			sm.State = enums.MachineStates.Disconnected
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.Downlinking:
		switch sm.TransitionalState {
		case enums.TransitionStates.DownlinkingFinished:
			sm.State = enums.MachineStates.Uplinking
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.EnteringEmergency:
		switch sm.TransitionalState {
		case enums.TransitionStates.EmergencyInitiated:
			sm.State = enums.MachineStates.AwaitingConnection
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.AwaitingConnection:
		switch sm.TransitionalState {
		case enums.TransitionStates.ConnectionReceived:
			sm.State = enums.MachineStates.SendConnectionAck
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.SendConnectionAck:
		switch sm.TransitionalState {
		case enums.TransitionStates.ConnectionAckSent:
			sm.State = enums.MachineStates.EmergencyUplink
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	case enums.MachineStates.EmergencyUplink:
		switch sm.TransitionalState {
		case enums.TransitionStates.EmergencyUplinkFinished:
			sm.State = enums.MachineStates.Disconnected
		case enums.TransitionStates.Error:
			sm.State = enums.MachineStates.Disconnected
		default:
			sm.State = enums.MachineStates.ServerSideError
		}
	}
}
