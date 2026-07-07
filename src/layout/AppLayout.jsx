import React from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <nav className="top-nav">
        <Link to="/" className="nav-brand">
          JayQuant
        </Link>
        <div className="nav-links">
          <NavLink to="/" end>
            Today
          </NavLink>
          <NavLink to="/analyze">Analyze</NavLink>
          <NavLink to="/watchlist">Watchlist</NavLink>
          <NavLink to="/alerts">Alerts</NavLink>
          <NavLink to="/portfolio">Portfolio</NavLink>
          <NavLink to="/compare">Compare</NavLink>
          <NavLink to="/breakout-strategy">Strategy</NavLink>
          <NavLink to="/intraday-scanner">Scanner</NavLink>
          <NavLink to="/stock-prediction">Prediction</NavLink>
          <NavLink to="/ai-recommendations">AI Picks</NavLink>
          <NavLink to="/intraday-picks">Intraday</NavLink>
          {user ? (
            <span className="nav-user">
              <span className="nav-email">{user.email}</span>
              <button type="button" className="btn-ghost" onClick={logout}>
                Log out
              </button>
            </span>
          ) : (
            <NavLink to="/login">Log in</NavLink>
          )}
        </div>
      </nav>
      <main className="main-area">
        <Outlet />
      </main>
    </div>
  );
}
