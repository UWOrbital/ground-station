/**
 * Number of decimal places the backend stores per coordinate (~110 m of
 * latitude). Mirrors `COORDINATE_DECIMAL_NUMBER` in `backend/app/config/data_values.py`.
 */
const COORDINATE_DECIMAL_PLACES = 3;

/**
 * @brief Data Validation for Latitude and Longitude
 *
 * Checks if latitude is a float between -90 and 90 degrees inclusive and
 * Checks if longitude is a float between -180 and 180 degrees inclusive
 * @param latitude - north-south position
 * @param longitude - east-west position
 * @return Returns true if both coordinates are valid, otherwise false.
 */
export function ValidateCoords(latitude: number, longitude: number): boolean {
  return latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180;
}

/**
 * @brief Round a coordinate to the precision the backend accepts.
 *
 * Browser geolocation and map clicks produce many decimal places, which the
 * backend rejects with a 422, so round before submitting.
 *
 * @param value coordinate in decimal degrees.
 * @return the coordinate rounded to {@link COORDINATE_DECIMAL_PLACES} places.
 */
export function roundCoord(value: number): number {
  const factor = 10 ** COORDINATE_DECIMAL_PLACES;
  return Math.round(value * factor) / factor;
}
