import { Routes, Route } from "react-router-dom";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import Nav from "./components/Nav";
import Background from "./components/Background";
import ProtectedRoute from "./components/ProtectedRoute";
// import Commands from "./pages/Command/Commands";
import Dashboard from "./pages/Dashboard";
import Commands from "./pages/Commands";
import AROAdmin from "./pages/AROAdmin";
import Images from "./pages/Images";
import LiveSession from "./pages/LiveSession";
import Login from "./pages/Login";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import PageNotFound from "./components/PageNotFound";
import Telemetry from "./pages/Telemetry";

/**
 * @brief App component displaying the main application
 * @return tsx element of App component
 */
function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Nav />
        <Background />
        <div className="pt-16">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route
              path="/commands"
              element={
                <ProtectedRoute>
                  <Commands />
                </ProtectedRoute>
              }
            />
            <Route path="/telemetry-data" element={<AROAdmin />} />
            <Route path="/aro-requests" element={<LiveSession />} />
            <Route path="/login" element={<Login />} />
            <Route path="/telemetry" element={<Telemetry />} />
            <Route path="/images" element={<Images />} />
            <Route path="*" element={<PageNotFound />} />
          </Routes>
        </div>
        <ToastContainer />
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
