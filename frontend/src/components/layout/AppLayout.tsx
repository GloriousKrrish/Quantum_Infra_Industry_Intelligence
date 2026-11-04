import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";

/**
 * Main application layout.
 * Fixed sidebar + scrollable content area with sticky header.
 */
export default function AppLayout() {
  return (
    <div className="flex min-h-screen bg-slate-950">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content Area — offset by sidebar width */}
      <div className="ml-64 flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
