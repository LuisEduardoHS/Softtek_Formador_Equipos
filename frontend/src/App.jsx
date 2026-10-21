import { Navigate, Route, Routes } from "react-router-dom"
import AppLayout from "./components/layout/AppLayout"
import LandingPage from "./pages/LandingPage"
import AuthPage from "./pages/AuthPage"
import ProfileSetupPage from "./pages/ProfileSetupPage"
import MatchPage from "./pages/MatchPage"
import MeetingPage from "./pages/MeetingPage"
import DesignSystemPage from "./pages/DesignSystemPage"
import HomePage from "./pages/HomePage"
import ProjectsPage from "./pages/ProjectsPage"
import CreateProjectPage from "./pages/CreateProjectPage"
import ProjectDetailPage from "./pages/ProjectDetailPage"
import TeamsPage from "./pages/TeamsPage"
import TeamPage from "./pages/TeamPage"
import InvitationsPage from "./pages/InvitationsPage"
import NotificationsPage from "./pages/NotificationsPage"
import ProfilePage from "./pages/ProfilePage"
import StudentsPage from "./pages/StudentsPage"

function App() {
  return (
    <Routes>
      {/* Públicas: Landing → Auth → Profile (onboarding) */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/profile" element={<ProfileSetupPage />} />
      <Route path="/sistema-diseno" element={<DesignSystemPage />} />

      {/* Alias */}
      <Route path="/entrar" element={<Navigate to="/auth" replace />} />
      <Route path="/bienvenida" element={<Navigate to="/profile" replace />} />

      {/* App autenticada */}
      <Route element={<AppLayout />}>
        <Route path="/inicio" element={<HomePage />} />
        <Route path="/match" element={<MatchPage />} />
        <Route path="/meeting" element={<MeetingPage />} />
        <Route path="/proyectos" element={<ProjectsPage />} />
        <Route path="/estudiantes" element={<StudentsPage />} />
        <Route path="/proyectos/nuevo" element={<CreateProjectPage />} />
        <Route path="/proyectos/:id" element={<ProjectDetailPage />} />
        <Route path="/equipos" element={<TeamsPage />} />
        <Route path="/equipos/:id" element={<TeamPage />} />
        <Route path="/invitaciones" element={<InvitationsPage />} />
        <Route path="/notificaciones" element={<NotificationsPage />} />
        <Route path="/perfil" element={<ProfilePage />} />
        <Route path="/perfil/:id" element={<ProfilePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
