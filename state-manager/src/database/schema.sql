-- Schema dump of the ground-station database (pg_dump --schema-only).
-- Source of truth for sqlc code generation; regenerate with:
--   pg_dump --schema-only --no-owner --no-privileges "$DATABASE_URL"


CREATE SCHEMA aro_users;

CREATE SCHEMA main;

CREATE SCHEMA mcc_users;

CREATE SCHEMA transactional;

CREATE TYPE public.arorequeststatus AS ENUM (
    'PENDING',
    'SCHEDULED',
    'TAKEN',
    'CANCELLED',
    'FAILED',
    'COMPLETED'
);

CREATE TYPE public.commandstatus AS ENUM (
    'PENDING',
    'SCHEDULED',
    'ONGOING',
    'CANCELLED',
    'FAILED',
    'COMPLETED'
);

CREATE TYPE public.mainpackettype AS ENUM (
    'UPLINK',
    'DOWNLINK'
);

CREATE TYPE public.sessionstatus AS ENUM (
    'PENDING',
    'SCHEDULED',
    'ONGOING',
    'COMPLETED'
);

CREATE TABLE aro_users.auth_tokens (
    id uuid NOT NULL,
    user_id uuid CONSTRAINT auth_tokens_user_data_id_not_null NOT NULL,
    created_on timestamp with time zone NOT NULL,
    expiry timestamp with time zone NOT NULL,
    family_id uuid NOT NULL,
    token_hash character varying NOT NULL,
    rotated_at timestamp with time zone,
    revoked_at timestamp with time zone
);

CREATE TABLE aro_users.callsigns (
    call_sign character varying(6) NOT NULL,
    first_name character varying(255),
    last_name character varying(255),
    personal_address character varying(255),
    personal_city character varying(255),
    personal_province character varying(255),
    personal_postal_code character varying(255),
    qual_level_a boolean NOT NULL,
    qual_level_b boolean NOT NULL,
    qual_level_c boolean NOT NULL,
    qual_level_d boolean NOT NULL,
    qual_level_e boolean NOT NULL,
    club_name character varying(255),
    second_club_name character varying(255),
    club_address character varying(255),
    club_city character varying(255),
    club_province character varying(255),
    club_postal_code character varying(255)
);

CREATE TABLE aro_users.user_login (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    password character varying(128) NOT NULL,
    created_on timestamp with time zone NOT NULL,
    user_id uuid CONSTRAINT user_login_user_data_id_not_null NOT NULL
);

CREATE TABLE aro_users.users_data (
    id uuid NOT NULL,
    call_sign character varying(6),
    email character varying(255) NOT NULL,
    first_name character varying(255) NOT NULL,
    last_name character varying(255),
    phone_number character varying,
    is_callsign_verified boolean NOT NULL,
    is_active boolean NOT NULL,
    is_superuser boolean NOT NULL
);

CREATE TABLE main.commands (
    id integer NOT NULL,
    name character varying NOT NULL,
    params character varying,
    format character varying,
    data_size integer NOT NULL,
    total_size integer NOT NULL,
    priority integer DEFAULT 0 NOT NULL,
    CONSTRAINT ck_main_commands_data_size_ge_0 CHECK ((data_size >= 0))
);

CREATE SEQUENCE main.commands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE main.commands_id_seq OWNED BY main.commands.id;

CREATE TABLE main.telemetry (
    id integer NOT NULL,
    name character varying NOT NULL,
    format character varying,
    data_size integer NOT NULL,
    total_size integer NOT NULL
);

CREATE SEQUENCE main.telemetry_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE main.telemetry_id_seq OWNED BY main.telemetry.id;

CREATE TABLE mcc_users.users_data (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    first_name character varying(255),
    last_name character varying(255),
    phone_number character varying
);

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);

CREATE TABLE transactional.aro_requests (
    id uuid NOT NULL,
    aro_id uuid NOT NULL,
    latitude numeric(5,3) NOT NULL,
    longitude numeric(6,3) NOT NULL,
    created_on timestamp with time zone NOT NULL,
    request_sent_to_obc_on timestamp with time zone,
    pic_taken_on timestamp with time zone,
    pic_transmitted_on timestamp with time zone,
    packet_id uuid,
    status public.arorequeststatus NOT NULL,
    delete_deadline timestamp with time zone
);

CREATE TABLE transactional.commands (
    id uuid NOT NULL,
    status public.commandstatus NOT NULL,
    type_ integer NOT NULL,
    params character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id uuid,
    packet_id uuid,
    sequence_index integer,
    session_id uuid NOT NULL,
    response character varying
);

CREATE TABLE transactional.images (
    id uuid NOT NULL,
    data character varying NOT NULL,
    packet_id uuid,
    aro_id uuid
);

CREATE TABLE transactional.packets (
    id uuid CONSTRAINT packet_id_not_null NOT NULL,
    session_id uuid CONSTRAINT packet_session_id_not_null NOT NULL,
    raw_data bytea CONSTRAINT packet_raw_data_not_null NOT NULL,
    type_ public.mainpackettype CONSTRAINT packet_type__not_null NOT NULL,
    payload_data bytea CONSTRAINT packet_payload_data_not_null NOT NULL,
    created_on timestamp with time zone CONSTRAINT packet_created_on_not_null NOT NULL,
    "offset" integer CONSTRAINT packet_offset_not_null NOT NULL,
    subtype character varying
);

CREATE TABLE transactional.sessions (
    id uuid CONSTRAINT comms_session_id_not_null NOT NULL,
    start_time timestamp with time zone CONSTRAINT comms_session_start_time_not_null NOT NULL,
    end_time timestamp with time zone NOT NULL,
    status public.sessionstatus CONSTRAINT comms_session_status_not_null NOT NULL
);

CREATE TABLE transactional.telemetry (
    id uuid NOT NULL,
    type_ integer NOT NULL,
    value character varying,
    packet_id uuid,
    sequence_index integer,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY main.commands ALTER COLUMN id SET DEFAULT nextval('main.commands_id_seq'::regclass);

ALTER TABLE ONLY main.telemetry ALTER COLUMN id SET DEFAULT nextval('main.telemetry_id_seq'::regclass);

ALTER TABLE ONLY aro_users.auth_tokens
    ADD CONSTRAINT auth_tokens_pkey PRIMARY KEY (id);

ALTER TABLE ONLY aro_users.callsigns
    ADD CONSTRAINT callsigns_pkey PRIMARY KEY (call_sign);

ALTER TABLE ONLY aro_users.user_login
    ADD CONSTRAINT user_login_email_key UNIQUE (email);

ALTER TABLE ONLY aro_users.user_login
    ADD CONSTRAINT user_login_pkey PRIMARY KEY (id);

ALTER TABLE ONLY aro_users.user_login
    ADD CONSTRAINT user_login_user_id_key UNIQUE (user_id);

ALTER TABLE ONLY aro_users.users_data
    ADD CONSTRAINT users_data_email_key UNIQUE (email);

ALTER TABLE ONLY aro_users.users_data
    ADD CONSTRAINT users_data_pkey PRIMARY KEY (id);

ALTER TABLE ONLY main.commands
    ADD CONSTRAINT commands_pkey PRIMARY KEY (id);

ALTER TABLE ONLY main.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY (id);

ALTER TABLE ONLY mcc_users.users_data
    ADD CONSTRAINT users_data_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);

ALTER TABLE ONLY transactional.aro_requests
    ADD CONSTRAINT aro_requests_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transactional.commands
    ADD CONSTRAINT commands_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transactional.sessions
    ADD CONSTRAINT comms_session_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transactional.images
    ADD CONSTRAINT images_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transactional.packets
    ADD CONSTRAINT packet_pkey PRIMARY KEY (id);

ALTER TABLE ONLY transactional.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY (id);

CREATE INDEX ix_aro_users_auth_tokens_family_id ON aro_users.auth_tokens USING btree (family_id);

CREATE INDEX ix_aro_users_auth_tokens_id ON aro_users.auth_tokens USING btree (id);

CREATE UNIQUE INDEX ix_aro_users_auth_tokens_token_hash ON aro_users.auth_tokens USING btree (token_hash);

CREATE INDEX ix_aro_users_user_login_id ON aro_users.user_login USING btree (id);

CREATE INDEX ix_aro_users_users_data_id ON aro_users.users_data USING btree (id);

CREATE INDEX ix_main_commands_id ON main.commands USING btree (id);

CREATE INDEX ix_main_telemetry_id ON main.telemetry USING btree (id);

CREATE INDEX ix_mcc_users_users_data_id ON mcc_users.users_data USING btree (id);

CREATE INDEX ix_transactional_aro_requests_id ON transactional.aro_requests USING btree (id);

CREATE INDEX ix_transactional_commands_id ON transactional.commands USING btree (id);

CREATE INDEX ix_transactional_images_id ON transactional.images USING btree (id);

CREATE INDEX ix_transactional_packets_id ON transactional.packets USING btree (id);

CREATE INDEX ix_transactional_sessions_id ON transactional.sessions USING btree (id);

CREATE INDEX ix_transactional_telemetry_id ON transactional.telemetry USING btree (id);

ALTER TABLE ONLY aro_users.auth_tokens
    ADD CONSTRAINT auth_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES aro_users.users_data(id);

ALTER TABLE ONLY aro_users.user_login
    ADD CONSTRAINT user_login_user_id_fkey FOREIGN KEY (user_id) REFERENCES aro_users.users_data(id);

ALTER TABLE ONLY transactional.aro_requests
    ADD CONSTRAINT aro_requests_aro_id_fkey FOREIGN KEY (aro_id) REFERENCES aro_users.users_data(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY transactional.aro_requests
    ADD CONSTRAINT aro_requests_packet_id_fkey FOREIGN KEY (packet_id) REFERENCES transactional.packets(id) ON DELETE CASCADE;

ALTER TABLE ONLY transactional.commands
    ADD CONSTRAINT commands_packet_id_fkey FOREIGN KEY (packet_id) REFERENCES transactional.packets(id) ON DELETE SET NULL;

ALTER TABLE ONLY transactional.commands
    ADD CONSTRAINT commands_session_id_fkey FOREIGN KEY (session_id) REFERENCES transactional.sessions(id) ON DELETE CASCADE;

ALTER TABLE ONLY transactional.commands
    ADD CONSTRAINT commands_type__fkey FOREIGN KEY (type_) REFERENCES main.commands(id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY transactional.commands
    ADD CONSTRAINT commands_user_id_fkey FOREIGN KEY (user_id) REFERENCES mcc_users.users_data(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE ONLY transactional.images
    ADD CONSTRAINT images_aro_id_fkey FOREIGN KEY (aro_id) REFERENCES transactional.aro_requests(id) ON DELETE SET NULL;

ALTER TABLE ONLY transactional.images
    ADD CONSTRAINT images_packet_id_fkey FOREIGN KEY (packet_id) REFERENCES transactional.packets(id) ON DELETE SET NULL;

ALTER TABLE ONLY transactional.packets
    ADD CONSTRAINT packet_session_id_fkey FOREIGN KEY (session_id) REFERENCES transactional.sessions(id) ON DELETE CASCADE;

ALTER TABLE ONLY transactional.telemetry
    ADD CONSTRAINT telemetry_packet_id_fkey FOREIGN KEY (packet_id) REFERENCES transactional.packets(id) ON DELETE SET NULL;

ALTER TABLE ONLY transactional.telemetry
    ADD CONSTRAINT telemetry_type__fkey FOREIGN KEY (type_) REFERENCES main.telemetry(id) ON UPDATE CASCADE ON DELETE CASCADE;
