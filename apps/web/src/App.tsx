import { Navigate, Route, Routes } from "react-router-dom";
import { useMe } from "./lib/api";
import Dashboard from "./screens/Dashboard";
import NewInterview from "./screens/NewInterview";
import SessionDetail from "./screens/SessionDetail";
import SignIn from "./screens/SignIn";

export default function App() {
  const me = useMe();

  if (me.isLoading) {
    return <div className="p-8 text-slate-500">Loading…</div>;
  }

  return (
    <Routes>
      <Route path="/" element={me.data ? <Dashboard user={me.data} /> : <SignIn />} />
      <Route
        path="/new"
        element={me.data ? <NewInterview user={me.data} /> : <Navigate to="/" />}
      />
      <Route
        path="/sessions/:id"
        element={me.data ? <SessionDetail user={me.data} /> : <Navigate to="/" />}
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
