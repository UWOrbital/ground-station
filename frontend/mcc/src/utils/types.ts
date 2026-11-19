// Types for MCC frontend based on database schema

// Enums matching database schema
export type CommandStatus =
  "pending" | "scheduled" | "ongoing" | "cancelled" | "failed" | "completed";

export type SessionStatus = "pending" | "scheduled" | "ongoing" | "completed";

export type SessionSource = "predicted" | "manual";

export type ARORequestStatus =
  "pending" | "scheduled" | "taken" | "cancelled" | "failed" | "completed";

export type MainPacketType = "uplink" | "downlink";

// Database table interfaces
export interface Session {
  id: string;
  start_time: string; // ISO datetime string
  end_time: string; // ISO datetime string
  status: SessionStatus;
  source: SessionSource;
  // Pass data from the pass predictor, null for manual sessions
  rise_time: string | null;
  peak_time: string | null;
  set_time: string | null;
  min_elevation_deg: number | null;
  max_elevation_deg: number | null;
  rise_azimuth_deg: number | null;
  set_azimuth_deg: number | null;
  orbit_element_id: string | null;
  orphaned_at: string | null; // set when the predictor needs operator to review this session
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
  response: string | null;
}

export interface ARORequest {
  id: string;
  aro_id: string;
  latitude: number;
  longitude: number;
  created_on: string;
  request_sent_to_obc_on: string | null;
  pic_taken_on: string | null;
  pic_transmitted_on: string | null;
  delete_deadline: string | null;
  packet_id: string | null;
  status: ARORequestStatus;
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
