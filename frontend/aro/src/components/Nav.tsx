import { Link } from "react-router-dom";
import orbital_logo from "../assets/orbital_logo.png";
// import { CSS_VARIABLES } from "../utils/themes";
import { NAVIGATION_LINKS } from "../utils/routes";
import { useAuth } from "../contexts/AuthContext";

/**
 * @brief Nav component displaying the navigation bar
 * @return tsx element of Nav component
 */
function Nav() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <nav className="m-7 text-white">
      {/* Logo */}
      <div className="absolute left-14">
        <Link to="/" className="hover:opacity-80 transition-opacity">
          <img src={orbital_logo} alt="orbital-logo" className="h-12 w-auto" />
        </Link>
      </div>

      {/* Navigation Links */}
      <div className="absolute right-14 mt-2 flex space-x-7">
        {NAVIGATION_LINKS.filter((link) => isAuthenticated || link.url !== "/new-request").map(
          (link) => (
            <Link key={link.url} to={link.url} className="mt-1 hover:underline">
              {link.text}
            </Link>
          ),
        )}
        {/* Hidden until the auth check settles so a signed-in user never sees Login flash */}
        {!isLoading && (
          <div className="border-1 border-white rounded-xl p-1 px-2 hover:bg-white hover:text-black">
            {isAuthenticated ? <Link to="/profile">Profile</Link> : <Link to="/login">Login</Link>}
          </div>
        )}
      </div>
    </nav>
  );
}

export default Nav;
