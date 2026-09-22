package main

import (
	"fmt"
	"time"

	"github.com/joho/godotenv"
)

// How long before a session starts we should have commands packed and ready.
const PreSessionLeadTime = 5 * time.Minute

// How often to re-check for a scheduled session when none is currently pending.
const NoSessionPollInterval = 60 * time.Second

func init() {
	if err := godotenv.Load(); err != nil {
		fmt.Println("no .env file found, using system env vars")
	}
}

func main() {
	for {

		time.Sleep(NoSessionPollInterval)
	}
}
