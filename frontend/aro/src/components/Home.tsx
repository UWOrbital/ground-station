import logo from "../assets/aro_logo.png";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "./ui/button";
import {
  Satellite,
  Radio,
  Camera,
  ArrowRight,
  List,
  Key,
  Plus,
  Sparkles,
} from "lucide-react";

/**
 * @brief Home page for the ARO frontend.
 * Shows a hero landing for unauthenticated users and a dashboard
 * with quick actions for authenticated users.
 * @return tsx element of Home component
 */
function Home() {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return null;
  }

  // ---- Unauthenticated: Hero landing ----

  if (!isAuthenticated) {
    return (
      <div className="relative flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] px-4 overflow-hidden">
        {/* Subtle radial glow behind the logo */}
        <div className="absolute top-1/4 w-[600px] h-[600px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col items-center gap-6 relative z-10">
          {/* Logo */}
          <img
            src={logo}
            alt="aro-logo"
            className="w-24 md:w-28 lg:w-32 drop-shadow-[0_0_30px_rgba(59,130,246,0.3)]"
          />

          {/* Headline */}
          <h1 className="font-[Jaldi] font-bold text-5xl md:text-6xl lg:text-7xl text-center leading-tight">
            <span className="bg-gradient-to-b from-white via-blue-100 to-blue-300/70 bg-clip-text text-transparent">
              Amateur Radio
              <br />
              Operator
            </span>
          </h1>

          {/* Tagline */}
          <p className="text-blue-200/70 text-lg md:text-xl text-center max-w-xl font-light leading-relaxed">
            Request satellite imagery from orbit — no club affiliation needed.
            UW Orbital opens space to licensed amateur operators worldwide.
          </p>

          {/* Feature cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8 w-full max-w-2xl">
            {[
              {
                icon: Camera,
                label: "Satellite Imagery",
                desc: "Request photos from low Earth orbit",
              },
              {
                icon: Radio,
                label: "Radio Linked",
                desc: "AX.25 uplink over amateur bands",
              },
              {
                icon: Satellite,
                label: "Direct Access",
                desc: "Schedule passes over your QTH",
              },
            ].map(({ icon: Icon, label, desc }) => (
              <div
                key={label}
                className="group backdrop-blur-md bg-white/5 border border-white/10 rounded-xl p-5 text-center hover:bg-white/[0.08] hover:border-blue-400/30 transition-all duration-300"
              >
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10 text-blue-300 mb-3 group-hover:bg-blue-500/20 group-hover:scale-110 transition-all">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-white font-semibold text-sm">{label}</h3>
                <p className="text-blue-200/50 text-xs mt-1">{desc}</p>
              </div>
            ))}
          </div>

          {/* CTA buttons */}
          <div className="flex gap-4 mt-4">
            <Link to="/sign-up">
              <Button
                size="lg"
                className="bg-blue-500 hover:bg-blue-400 text-white font-[Jaldi] font-bold text-lg px-8 py-6 shadow-lg shadow-blue-500/25 hover:shadow-blue-400/40 transition-all"
              >
                Get Started
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
            <Link to="/login">
              <Button
                size="lg"
                variant="outline"
                className="border-white/20 text-white/80 hover:text-white hover:bg-white/10 font-[Jaldi] font-bold text-lg px-8 py-6"
              >
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ---- Authenticated: Dashboard ----

  return (
    <div className="flex flex-col items-center px-4 pt-12 pb-20">
      {/* Greeting */}
      <div className="flex items-center gap-3 mb-2">
        <Sparkles className="w-6 h-6 text-blue-300" />
        <h1 className="font-[Jaldi] font-bold text-4xl md:text-5xl text-white">
          Welcome back{user?.first_name ? `, ${user.first_name}` : ""}
        </h1>
      </div>
      <p className="text-blue-200/50 text-lg mb-4">
        {user?.call_sign ? (
          <>
            Signed in as <span className="text-blue-300 font-mono">{user.call_sign}</span>
          </>
        ) : (
          "Ready for your next pass?"
        )}
      </p>

      {/* Action cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-6 w-full max-w-3xl">
        {[
          {
            icon: Plus,
            title: "New Request",
            desc: "Submit an imaging request for the next satellite pass",
            to: "/new-request",
            color: "from-blue-500/20 to-blue-600/5 border-blue-500/30",
            iconBg: "bg-blue-500/15 text-blue-300",
            hover: "hover:border-blue-400/50",
          },
          {
            icon: List,
            title: "My Requests",
            desc: "Track status and history of all your past requests",
            to: "/requests",
            color: "from-purple-500/20 to-purple-600/5 border-purple-500/30",
            iconBg: "bg-purple-500/15 text-purple-300",
            hover: "hover:border-purple-400/50",
          },
          {
            icon: Key,
            title: "Callsign & Keys",
            desc: "Manage your callsign verification and API keys",
            to: "/keys",
            color: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/30",
            iconBg: "bg-emerald-500/15 text-emerald-300",
            hover: "hover:border-emerald-400/50",
          },
        ].map(({ icon: Icon, title, desc, to, color, iconBg, hover }) => (
          <Link key={title} to={to} className="group">
            <div
              className={`backdrop-blur-md bg-gradient-to-br ${color} ${hover} border rounded-2xl p-6 transition-all duration-300 group-hover:scale-[1.02] group-hover:shadow-lg`}
            >
              <div
                className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${iconBg} mb-4 group-hover:scale-110 transition-transform`}
              >
                <Icon className="w-6 h-6" />
              </div>
              <h3 className="text-white font-semibold text-lg mb-1">{title}</h3>
              <p className="text-white/50 text-sm leading-relaxed">{desc}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default Home;
