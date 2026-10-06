import { NavLink, Route, Routes } from "react-router-dom";

import { Logo } from "./logo";
import { BatchDetail, BatchForm, BatchList, Dashboard, FindingsPage, RulesPage } from "./pages/index";

export function App() {
  return (
    <div className="app">
      <header className="topbar">
        <Logo />
        <nav>
          <NavLink to="/" end>
            Painel
          </NavLink>
          <NavLink to="/lotes" end>
            Lotes
          </NavLink>
          <NavLink to="/inconsistencias">Inconsistências</NavLink>
          <NavLink to="/regras">Regras</NavLink>
        </nav>
        <NavLink className="button" to="/lotes/novo">
          Novo lote
        </NavLink>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/lotes" element={<BatchList />} />
          <Route path="/lotes/novo" element={<BatchForm />} />
          <Route path="/lotes/:id" element={<BatchDetail />} />
          <Route path="/inconsistencias" element={<FindingsPage />} />
          <Route path="/regras" element={<RulesPage />} />
        </Routes>
      </main>
    </div>
  );
}
