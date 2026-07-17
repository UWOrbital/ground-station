/**
 * Navigation links for the MCC frontend
 */

export interface NavLink {
  text: string;
  url: string;
}

export const NAVIGATION_LINKS: NavLink[] = [
  {
    text: "Dashboard",
    url: "/",
  },
  {
    text: "Commands",
    url: "/commands",
  },
  {
    text: "ARO Admin",
    url: "/aro-admin",
  },
  {
    text: "Passes",
    url: "/passes",
  },
  {
    text: "Live Sessions",
    url: "/live-sessions",
  },
];
