
import { useState } from "react";

import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Cases from "./pages/Cases";
import CaseDetails from "./pages/CaseDetails";
import SimilarityReports from "./pages/SimilarityReports";
import Reviewers from "./pages/Reviewers";
import Decisions from "./pages/Decisions";
import "./styles/layout.css";
import Appeals from "./pages/Appeals";
import AuditHistory from "./pages/AuditHistory";

export default function App() {
  const [active, setActive] = useState("Overview");
  const [selectedCaseId, setSelectedCaseId] = useState(null);

  const navigate = (page) => {
    setSelectedCaseId(null);
    setActive(page);
  };

  const openCase = (caseId) => {
    setSelectedCaseId(caseId);
  };

  const renderPage = () => {
    if (selectedCaseId) {
      return (
        <CaseDetails
          caseId={selectedCaseId}
          onBack={() => setSelectedCaseId(null)}
        />
      );
    }

    switch (active) {
      case "Overview":
        return <Dashboard />;

      case "Cases":
        return <Cases onOpenCase={openCase} />;

      case "Similarity reports":
        return <SimilarityReports />;

      case "Reviewers":
        return <Reviewers />;

      case "Decisions":
        return <Decisions />;
      case "Appeals":
        return <Appeals />;
      case "Audit history":
        return <AuditHistory />;

      default:
        return (
          <main className="dashboard-page">
            <p className="eyebrow">ACADEMIC INTEGRITY / WORKSPACE</p>
            <h1>{active}</h1>
            <p className="dashboard-subtitle">
              This module is coming next. Your dashboard and case management
              modules are available.
            </p>
          </main>
        );
    }
  };

  return (
    <AppLayout active={active} onNavigate={navigate}>
      {renderPage()}
    </AppLayout>
  );
}
