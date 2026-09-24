package impls

import (
	"fmt"

	"go.bug.st/serial"
)

type UartConnection struct {
	ComPort         string
	BaudRate        int
	Timeout         float64
	Serial          serial.Port
	IsOpen          bool
	ConnRequestSent bool
}

func NewUartConnection(comPort string, baudRate int, timeout float64) *UartConnection {
	return &UartConnection{
		ComPort:  comPort,
		BaudRate: baudRate,
		Timeout:  timeout,
	}
}

func (uc *UartConnection) ConnectUart() error {
	if uc.IsOpen {
		return fmt.Errorf("UART already connected.")
	}

	port, err := serial.Open(uc.ComPort, &serial.Mode{
		BaudRate: uc.BaudRate,
	})
	if err != nil {
		return fmt.Errorf("Could not open UART port {%s}: {%v}", uc.ComPort, err)
	}
	uc.Serial = port
	uc.IsOpen = true
	return nil
}

func (uc *UartConnection) DisconnectUart() error {
	if !uc.IsOpen {
		return fmt.Errorf("UART already disconnected.")
	}

	if err := uc.Serial.Close(); err != nil {
		return err
	}

	uc.IsOpen = false
	uc.ConnRequestSent = false
	return nil
}
