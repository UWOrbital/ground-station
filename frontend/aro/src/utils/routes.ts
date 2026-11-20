/**
 * Routes for the ARO frontend
 */

export interface Route {
  text: string;
  url: string;
  /** Only shown to signed-in users; the route itself must also be nested under ProtectedRoute in App.tsx. */
  requiresAuth?: boolean;
}

export const NAVIGATION_LINKS: Route[] = [
  {
    text: "Home",
    url: "/",
  },
  {
    text: "New",
    url: "/new-request",
    requiresAuth: true,
  },
  {
    text: "Requests",
    url: "/requests",
  },
];
