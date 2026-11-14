
import { Bell, Menu, Search } from "lucide-react";

export default function Topbar({ onMenu, title }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="topbar-menu"
          onClick={onMenu}
          aria-label="Open navigation"
        >
          <Menu size={21} />
        </button>

        <div className="topbar-heading">
          <div className="topbar-eyebrow">
            ACADEMIC INTEGRITY / WORKSPACE
          </div>
          <div className="topbar-title">{title || "Overview"}</div>
        </div>
      </div>

      <div className="topbar-actions">
        <div className="topbar-search">
          <Search size={17} />
          <span>Integrity management</span>
        </div>

        <button className="topbar-icon" aria-label="Notifications">
          <Bell size={19} />
          <i />
        </button>

        <div className="profile-avatar" title="Administrator">
          AD
        </div>
      </div>
    </header>
  );
}
