import { NavLink, Route, Routes } from "react-router-dom";

import { BatchDetail, BatchForm, BatchList, Dashboard } from "./pages";

export function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <p className="brand">RegulaFlow</p>
        <nav>
          <NavLink to="/" end>
            Painel
          </NavLink>
          <NavLink to="/lotes" end>
            Lotes
          </NavLink>
          <NavLink to="/lotes/novo">Novo lote</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/lotes" element={<BatchList />} />
          <Route path="/lotes/novo" element={<BatchForm />} />
          <Route path="/lotes/:id" element={<BatchDetail />} />
        </Routes>
      </main>
    </div>
  );
}
