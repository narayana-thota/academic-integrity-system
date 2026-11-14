
import {
  Activity,
  BookOpenCheck,
  ChevronRight,
  ClipboardCheck,
  FileSearch,
  FolderKanban,
  LayoutDashboard,
  Scale,
  Users,
  X,
} from "lucide-react";

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Cases", icon: FolderKanban },
  { label: "Similarity reports", icon: FileSearch },
  { label: "Reviewers", icon: Users },
  { label: "Decisions", icon: ClipboardCheck },
  { label: "Appeals", icon: Scale },
  { label: "Audit history", icon: Activity },
];

export default function Sidebar({ active, onNavigate, open, onClose }) {
  return (
    <>
      <button
        className={`sidebar-backdrop ${open ? "visible" : ""}`}
        onClick={onClose}
        aria-label="Close navigation"
        tabIndex={open ? 0 : -1}
      />

      <aside className={`sidebar ${open ? "sidebar--open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-mark">
            <BookOpenCheck size={23} strokeWidth={1.8} />
          </div>

          <div className="brand-copy">
            <strong>
              Integrity<span>Hub</span>
            </strong>
            <small>ACADEMIC OVERSIGHT</small>
          </div>

          <button
            className="sidebar-close"
            onClick={onClose}
            aria-label="Close menu"
          >
            <X size={19} />
          </button>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          {navigation.map(({ label, icon: Icon }) => {
            const selected = active === label;

            return (
              <button
                key={label}
                className={`sidebar-link ${selected ? "is-active" : ""}`}
                onClick={() => {
                  onNavigate(label);
                  onClose();
                }}
                aria-current={selected ? "page" : undefined}
              >
                <Icon size={19} strokeWidth={1.8} />
                <span>{label}</span>
                {selected && (
                  <ChevronRight className="active-indicator" size={16} />
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-system">
            <span className="online-dot" />
            <div>
              <strong>System connected</strong>
              <small>API operational</small>
            </div>
          </div>

          <p>Academic Integrity System · 2026</p>
        </div>
      </aside>
    </>
  );
}
