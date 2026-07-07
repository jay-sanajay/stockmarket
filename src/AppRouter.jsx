import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import AppLayout from "./layout/AppLayout.jsx";
import HomePage from "./pages/HomePage.jsx";
import AnalyzePage from "./pages/AnalyzePage.jsx";
import WatchlistPage from "./pages/WatchlistPage.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";
import PortfolioPage from "./pages/PortfolioPage.jsx";
import ComparePage from "./pages/ComparePage.jsx";
import BreakoutStrategyPage from "./pages/BreakoutStrategyPage.jsx";
import IntradayScannerPage from "./pages/IntradayScannerPage.jsx";
import StockPredictionPage from "./pages/StockPredictionPage.jsx";
import AiRecommendationsPage from "./pages/AiRecommendationsPage.jsx";
import IntradayPicksPage from "./pages/IntradayPicksPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/breakout-strategy" element={<BreakoutStrategyPage />} />
            <Route path="/intraday-scanner" element={<IntradayScannerPage />} />
            <Route path="/stock-prediction" element={<StockPredictionPage />} />
            <Route path="/ai-recommendations" element={<AiRecommendationsPage />} />
            <Route path="/intraday-picks" element={<IntradayPicksPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
