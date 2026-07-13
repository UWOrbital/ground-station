// Types for MCC frontend based on database schema

// Enums matching database schema
export type CommandStatus =
  | "pending"
  | "scheduled"
  | "ongoing"
  | "cancelled"
  | "failed"
  | "completed";

export type SessionStatus = "pending" | "scheduled" | "ongoing" | "completed";

export type MainPacketType = "uplink" | "downlink";

// Database table interfaces
export interface Session {
  id: string;
  start_time: string; // ISO datetime string
  end_time: string | null;
  status: SessionStatus;
}

export interface Packet {
  id: string;
  session_id: string;
  raw_data: string;
  type_: MainPacketType;
  subtype: string | null; // enum - TODO: Define specific values when known
  payload_data: string;
  created_on: string;
  offset: number;
}

export interface Command {
  id: string;
  user_id: string | null;
  session_id: string;
  status: CommandStatus;
  type_: number;
  params: string | null;
  created_at: string;
  packet_id: string | null;
  sequence_index: number | null;
}

export interface Telemetry {
  id: string;
  type_: number;
  value: string | null;
  packet_id: string | null;
  sequence_index: number | null;
  timestamp: string;
}

export interface MainCommand {
  id: number;
  name: string;
  params: string | null;
  format: string | null;
  data_size: number;
  total_size: number;
  priority: number;
}

export interface MainTelemetry {
  id: number;
  name: string;
  format: string | null;
  data_size: number;
  total_size: number;
}

// User-related interfaces
export interface UserData {
  id: number;
  call_sign: string;
  first_name: string;
  last_name: string | null;
  phone_number: string | null;
}

export interface UserLogin {
  id: number;
  email: string;
  created_on: string;
  user_data_id: number;
  email_verification_token: string | null;
}
