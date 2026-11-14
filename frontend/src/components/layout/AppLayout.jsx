
import { useState } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function AppLayout({ active, onNavigate, children }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="app-layout">
      <Sidebar
        active={active}
        onNavigate={onNavigate}
        open={menuOpen}
        onClose={closeMenu}
      />

      <div className="app-main">
        <Topbar
          title={active}
          onMenu={() => setMenuOpen(true)}
        />

        <div className="page-content">
          {children}
        </div>
      </div>
    </div>
  );
}
