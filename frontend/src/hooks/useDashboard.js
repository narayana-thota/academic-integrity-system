import { useCallback, useEffect, useState } from "react";
import { fetchDashboard, fetchCases } from "../services/api";

export default function useDashboard() {
  const [summary, setSummary] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [summaryData, casesData] = await Promise.all([
        fetchDashboard(),
        fetchCases(1, 8),
      ]);

      setSummary(summaryData);
      setCases(
        Array.isArray(casesData)
          ? casesData
          : casesData?.cases || casesData?.items || []
      );
    } catch (err) {
      setError(err.message || "Unable to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return { summary, cases, loading, error, refresh: loadDashboard };
}