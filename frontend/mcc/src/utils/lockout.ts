export const SESSION_LOCKOUT_SECONDS = 10;

export function isSessionLockedOut(startTime: string | Date): boolean {
  const start = typeof startTime === "string" ? new Date(startTime) : startTime;
  const lockoutStart = new Date(start.getTime() - SESSION_LOCKOUT_SECONDS * 1000);
  return new Date() >= lockoutStart;
}
