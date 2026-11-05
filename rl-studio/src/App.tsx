import { Navigate, Route, Routes } from 'react-router-dom'
import Shell from './components/Shell'
import DemoGuide from './components/DemoGuide'
import Landing from './pages/Landing'
import Signup from './pages/Signup'
import Onboarding from './pages/Onboarding'
import Overview from './pages/Overview'
import Traces from './pages/Traces'
import Builder from './pages/Builder'
import Experts from './pages/Experts'
import Evals from './pages/Evals'
import Training from './pages/Training'
import NewRun from './pages/NewRun'
import RunDetail from './pages/RunDetail'
import Deploy from './pages/Deploy'
import Monitor from './pages/Monitor'

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/app" element={<Shell />}>
          <Route index element={<Overview />} />
          <Route path="traces" element={<Traces />} />
          <Route path="environment" element={<Builder />} />
          <Route path="experts" element={<Experts />} />
          <Route path="evals" element={<Evals />} />
          <Route path="training" element={<Training />} />
          <Route path="training/new" element={<NewRun />} />
          <Route path="training/:id" element={<RunDetail />} />
          <Route path="deploy" element={<Deploy />} />
          <Route path="monitor" element={<Monitor />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <DemoGuide />
    </>
  )
}
