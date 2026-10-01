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
  const { status } = useAuth();
  const signedIn = status === "signedIn";

  return (
    <nav className="px-7 h-12 pb-3 flex items-center justify-between m-4 text-white border-b border-border/40 z-50">
      {/* Logo */}
      <div>
        <Link to="/" className="inline-block hover:opacity-80 transition-opacity">
          <img src={orbital_logo} alt="orbital-logo" className="h-10 w-auto" />
        </Link>
      </div>

      {/* Navigation Links */}
      <div className="flex items-center space-x-7">
        {NAVIGATION_LINKS.filter((link) => signedIn || !link.requiresAuth).map((link) => (
          <Link key={link.url} to={link.url} className="hover:underline">
            {link.text}
          </Link>
        ))}
        {/* Hidden until the auth status is known so a signed-in user never sees Login flash */}
        {(signedIn || status === "signedOut") && (
          <div className="border-1 border-white rounded-xl py-2 px-4 hover:bg-white hover:text-black">
            {signedIn ? <Link to="/profile">Profile</Link> : <Link to="/login">Login</Link>}
          </div>
        )}
      </div>
    </nav>
  );
}

export default Nav;
