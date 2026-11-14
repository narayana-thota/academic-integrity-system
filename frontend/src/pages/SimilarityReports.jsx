import { useEffect, useMemo, useState } from "react";

import {
  fetchSimilarityReports,
  fetchSimilarityReport,
} from "../services/api";

import SimilarityStats from "../components/similarity/SimilarityStats";
import SimilarityFilters from "../components/similarity/SimilarityFilters";
import SimilarityTable from "../components/similarity/SimilarityTable";
import MatchComparison from "../components/similarity/MatchComparison";

import "../styles/similarity.css";

const PAGE_SIZE = 20;

function extractReports(response) {
  if (Array.isArray(response?.reports)) return response.reports;
  if (Array.isArray(response?.data?.reports)) return response.data.reports;
  return [];
}

function extractDetail(response) {
  return response?.report ?? response?.data?.report ?? response?.data ?? response;
}

export default function SimilarityReports() {
  const [reports, setReports] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);


  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [action, setAction] = useState("");

  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");


  useEffect(() => {
    let active = true;

    async function loadReports() {
      try {
        setLoading(true);
        setError("");

        const response = await fetchSimilarityReports(page, PAGE_SIZE, {
          report_category: category,
          review_action: action,
        });

        if (!active) return;

        setReports(extractReports(response));
        setTotal(Number(response?.total ?? response?.data?.total ?? 0));
      } catch (err) {
        if (active) {
          setError(
            err?.response?.data?.detail ??
              err?.message ??
              "Unable to load similarity reports."
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadReports();

    return () => {
      active = false;
    };
  }, [page, category, action, refreshKey]);

  const categories = useMemo(
    () => [
      ...new Set(
        reports
          .map((report) => report.report_category)
          .filter(Boolean)
      ),
    ],
    [reports]
  );

  const actions = useMemo(
    () => [
      ...new Set(
        reports
          .map((report) => report.review_action)
          .filter(Boolean)
      ),
    ],
    [reports]
  );

  const filteredReports = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return reports;

    return reports.filter((report) =>
      [
        report.report_id,
        report.submission_id,
        report.report_category,
        report.review_action,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(query))
    );
  }, [reports, search]);

  const handleSelectReport = async (reportId) => {
    try {
      setDetailLoading(true);
      setDetailError("");
      setSelectedReport(null);

      const response = await fetchSimilarityReport(reportId);
      setSelectedReport(extractDetail(response));
    } catch (err) {
      setDetailError(
        err?.response?.data?.detail ??
          err?.message ??
          "Unable to load report details."
      );
    } finally {
      setDetailLoading(false);
    }
  };

  const clearFilters = () => {
    setSearch("");
    setCategory("");
    setAction("");
    setPage(1);
    setSelectedReport(null);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="similarity-page">
      <header className="similarity-header">
        <div>
          <p className="eyebrow">ACADEMIC INTEGRITY / REPORT ANALYSIS</p>
          <h1>Similarity Reports</h1>
          <p>
            Inspect generated similarity reports, matched sources, and
            their associated case records.
          </p>
        </div>

        <div className="report-count-pill">
          <span />
          {total.toLocaleString()} reports recorded
        </div>
      </header>

      {!loading && !error && (
        <SimilarityStats reports={reports} total={total} />
      )}

      <section className="similarity-content">
        <div className="similarity-section-heading">
          <div>
            <h2>Generated reports</h2>
            <p>Review the similarity analysis records.</p>
          </div>
        </div>

        <SimilarityFilters
          search={search}
          setSearch={setSearch}
          category={category}
          setCategory={(value) => {
            setCategory(value);
            setPage(1);
            setSelectedReport(null);
          }}
          action={action}
          setAction={(value) => {
            setAction(value);
            setPage(1);
            setSelectedReport(null);
          }}
          categories={categories}
          actions={actions}
          onClear={clearFilters}
        />

        {loading ? (
          <div className="similarity-state">
            <div className="similarity-spinner" />
            <p>Loading similarity reports...</p>
          </div>
        ) : error ? (
          <div className="similarity-state error">
            <h3>Unable to load reports</h3>
            <p>{error}</p>
            <button onClick={() => setRefreshKey((value) => value + 1)}>
                Retry
            </button>
          </div>
        ) : (
          <>
            <SimilarityTable
              reports={filteredReports}
              onSelect={handleSelectReport}
              selectedReportId={selectedReport?.report_id}
            />

            <div className="similarity-pagination">
              <span>
                Showing {filteredReports.length} of {total} reports on
                this page
              </span>

              <div>
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  Previous
                </button>

                <strong>
                  {page} / {totalPages}
                </strong>

                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {detailLoading && (
        <div className="similarity-state">
          <div className="similarity-spinner" />
          <p>Loading report details...</p>
        </div>
      )}

      {detailError && (
        <div className="similarity-state error">
          <p>{detailError}</p>
        </div>
      )}

      {selectedReport && (
        <MatchComparison
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </main>
  );
}