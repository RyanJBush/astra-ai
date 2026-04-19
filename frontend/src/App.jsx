import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import ResearchQueryPage from "./pages/ResearchQueryPage";
import ResultsViewPage from "./pages/ResultsViewPage";
import SourceViewerPage from "./pages/SourceViewerPage";

function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/research" element={<ResearchQueryPage />} />
        <Route path="/results/:runId" element={<ResultsViewPage />} />
        <Route path="/sources" element={<SourceViewerPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}

export default App;
