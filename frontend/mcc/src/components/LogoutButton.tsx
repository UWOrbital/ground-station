import { API_BASE_URL } from "@/utils/api/config";

export function LogoutButton() {
  const handleLogout = () => {
    window.location.href = `${API_BASE_URL}/auth/logout`;
  };

  return (
    <button
      onClick={handleLogout}
      className="bg-white px-4 py-2 rounded-xl text-black hover:bg-gray-200 transition-colors cursor-pointer"
    >
      Logout
    </button>
  )
}
