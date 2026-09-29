import { useEffect, useState } from 'react'
import { call } from './api'

interface LeaderboardRow {
  rank: number
  model_id: string
  rating: number
  ci_low: number
  ci_high: number
  wins: number
  losses: number
  votes: number
}

interface LeaderboardData {
  rows: LeaderboardRow[]
  total_votes: number
  participants: number
  generated_at: string
  note: string
}

export default function Leaderboard() {
  const [data, setData] = useState<LeaderboardData | null>(null)
  const [taskType, setTaskType] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    setError('')
    call<LeaderboardData>(`/leaderboard${taskType ? `?task_type=${encodeURIComponent(taskType)}` : ''}`).then(setData).catch(err => setError(err instanceof Error ? err.message : 'The leaderboard is unavailable.'))
  }, [taskType])
  return <div className="p-workspace"><p className="p-eyebrow">Shared signal</p><h1>Accountant preferences.</h1><p className="p-lead">A transparent view of which responses participating accountants preferred.</p>
    <label className="p-filter">Task type<select value={taskType} onChange={event => setTaskType(event.target.value)}><option value="">All tasks</option><option value="accounting-question">Accounting question</option><option value="journal-entry">Journal entry</option><option value="treatment-memo">Treatment memo</option><option value="workpaper-review">Workpaper review</option></select></label>
    {error && <p className="p-error" role="alert">{error}</p>}
    {data && <><p className="p-fine">{data.total_votes} votes · {data.participants} participants · updated {new Date(data.generated_at).toLocaleDateString()}</p><div className="p-card p-leaderboard-table"><table><thead><tr><th>Rank</th><th>Model</th><th>Rating</th><th>95% range</th><th>Wins</th><th>Losses</th><th>Votes</th></tr></thead><tbody>{data.rows.map(row => <tr key={row.model_id}><td>{row.rank}</td><th scope="row">{row.model_id}</th><td>{row.rating}</td><td>{row.ci_low}–{row.ci_high}</td><td>{row.wins}</td><td>{row.losses}</td><td>{row.votes}</td></tr>)}</tbody></table></div><p className="p-fine">{data.note}</p></>}
  </div>
}
