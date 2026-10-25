import { Link } from "react-router-dom";
import orbital_logo from "../assets/orbital_logo.png";
// import { CSS_VARIABLES } from "../utils/themes";
import { NAVIGATION_LINKS } from "../utils/routes";

/**
 * @brief Nav component displaying the navigation bar
 * @return tsx element of Nav component
 */
function Nav() {
  // TODO: create user auth that checks if the user is logged in
  const isLoggedIn = false;

  return (
    <nav className="px-7 h-12 pb-3 flex items-center justify-between m-4 text-white border-b border-border/40 z-50">
      {/* Logo */}
      <div>
        <Link to="/" className="inline-block hover:opacity-80 transition-opacity">
          <img src={orbital_logo} alt="orbital-logo" className="h-10 w-auto" />
        </Link>
      </div>

      {/* Navigation Links */}
      {isLoggedIn ? (
        <div className="flex items-center space-x-7">
          {NAVIGATION_LINKS.map((link) => (
            <Link key={link.url} to={link.url} className="hover:underline">
              {link.text}
            </Link>
          ))}
          <div className="border-1 border-white rounded-xl p-1 px-2 hover:bg-white hover:text-black">
            <Link to="/profile" className="">
              Profile
            </Link>
          </div>
        </div>
      ) : (
        <div className="flex items-center space-x-7">
          {NAVIGATION_LINKS.filter((link) => link.url !== "/new-request").map((link) => (
            <Link key={link.url} to={link.url} className="hover:underline">
              {link.text}
            </Link>
          ))}
          <div className="border-1 border-white rounded-xl py-2 px-4 hover:bg-white hover:text-black">
            <Link to="/login" className="">
              Login
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Nav;
