import { useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Link, Route, Routes, useNavigate, useParams } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

const DEMO_QUERIES = [
  'Assess the latest FDA guidance on generative AI in healthcare workflows.',
  'Compare major cloud providers on 2026 enterprise AI governance offerings.',
  'What are the strongest arguments for and against AI model watermarking?',
]

function getToken() {
  return localStorage.getItem('astra_token')
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...options.headers,
    },
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Request failed')
  }
  if (response.status === 204) return null
  return response.json()
}

function decomposeQuery(query) {
  return query
    .split(/,|;|\band\b/gi)
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 4)
}

function confidenceBadge(level) {
  if (level === 'high') return 'bg-emerald-100 text-emerald-700'
  if (level === 'medium') return 'bg-amber-100 text-amber-700'
  return 'bg-rose-100 text-rose-700'
}

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <nav className="mx-auto flex max-w-6xl items-center justify-between p-4">
          <Link className="text-lg font-semibold" to="/dashboard">
            Astra AI
          </Link>
          <div className="flex gap-4 text-sm">
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/research">Research Query</Link>
            <Link to="/settings">Settings</Link>
          </div>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl p-4">{children}</main>
    </div>
  )
}

function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const submit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      const data = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      localStorage.setItem('astra_token', data.access_token)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }
  return (
    <Layout>
      <div className="mx-auto mt-12 max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold">Login</h1>
        <p className="mt-2 text-sm text-slate-600">Sign in to run research sessions.</p>
        <form className="mt-6 space-y-4" onSubmit={submit}>
          <input
            className="w-full rounded-md border border-slate-300 p-2"
            placeholder="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <input
            className="w-full rounded-md border border-slate-300 p-2"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="w-full rounded-md bg-slate-900 p-2 text-white" type="submit">
            Sign in
          </button>
        </form>
      </div>
    </Layout>
  )
}

function DashboardPage() {
  const [items, setItems] = useState([])
  useEffect(() => {
    api('/api/research')
      .then(setItems)
      .catch(() => setItems([]))
  }, [])
  return (
    <Layout>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p className="mb-4 mt-1 text-slate-600">Recent research history</p>
      <div className="space-y-3">
        {items.map((item) => (
          <Link
            key={item.id}
            className="block rounded-lg border border-slate-200 bg-white p-4 hover:border-slate-400"
            to={`/results/${item.id}`}
          >
            <div className="flex items-center justify-between">
              <p className="font-medium">{item.query}</p>
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{item.status}</span>
            </div>
            <p className="mt-1 text-sm text-slate-500">Version: {item.version}</p>
          </Link>
        ))}
        {items.length === 0 && <p className="text-sm text-slate-500">No sessions yet.</p>}
      </div>
    </Layout>
  )
}

function ResearchQueryPage() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [depth, setDepth] = useState(2)
  const [breadth, setBreadth] = useState(3)
  const [maxSources, setMaxSources] = useState(5)
  const planPreview = useMemo(() => decomposeQuery(query), [query])

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      const data = await api('/api/research', {
        method: 'POST',
        body: JSON.stringify({
          query,
          depth,
          breadth,
          max_sources: maxSources,
        }),
      })
      navigate(`/results/${data.research_id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <Layout>
      <h1 className="text-2xl font-semibold">Research Query</h1>
      <p className="mt-1 text-sm text-slate-600">Use demo prompts or configure search controls.</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {DEMO_QUERIES.map((item) => (
          <button
            key={item}
            type="button"
            className="rounded-full border border-slate-300 px-3 py-1 text-xs hover:bg-slate-100"
            onClick={() => setQuery(item)}
          >
            {item}
          </button>
        ))}
      </div>
      <form className="mt-4 space-y-4" onSubmit={submit}>
        <textarea
          className="min-h-36 w-full rounded-md border border-slate-300 p-3"
          placeholder="Ask Astra AI to research a topic..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          required
        />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <label className="text-sm">
            Depth
            <input
              className="mt-1 w-full rounded-md border border-slate-300 p-2"
              type="number"
              min="1"
              max="5"
              value={depth}
              onChange={(event) => setDepth(Number(event.target.value))}
            />
          </label>
          <label className="text-sm">
            Breadth
            <input
              className="mt-1 w-full rounded-md border border-slate-300 p-2"
              type="number"
              min="1"
              max="6"
              value={breadth}
              onChange={(event) => setBreadth(Number(event.target.value))}
            />
          </label>
          <label className="text-sm">
            Max Sources
            <input
              className="mt-1 w-full rounded-md border border-slate-300 p-2"
              type="number"
              min="1"
              max="10"
              value={maxSources}
              onChange={(event) => setMaxSources(Number(event.target.value))}
            />
          </label>
        </div>
        {planPreview.length > 0 && (
          <div className="rounded-md border border-slate-200 bg-white p-3 text-sm">
            <p className="mb-1 font-medium">Research plan preview</p>
            <ul className="list-inside list-disc text-slate-600">
              {planPreview.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </div>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="rounded-md bg-slate-900 px-5 py-2 text-white" type="submit">
          Run research
        </button>
      </form>
    </Layout>
  )
}

function ResearchResultsPage() {
  const params = useParams()
  const [detail, setDetail] = useState(null)
  const [trace, setTrace] = useState([])
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    api(`/api/research/${params.id}`)
      .then(setDetail)
      .catch(() => setDetail(null))
    api(`/api/research/${params.id}/trace`)
      .then(setTrace)
      .catch(() => setTrace([]))
    api(`/api/research/${params.id}/metrics`)
      .then(setMetrics)
      .catch(() => setMetrics(null))
  }, [params.id])

  const exportReport = async (format) => {
    const response = await fetch(`${API_BASE}/api/research/${params.id}/export?format=${format}`, {
      headers: authHeaders(),
    })
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `research-${params.id}.${format === 'json' ? 'json' : 'md'}`
    link.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <Layout>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Research Results</h1>
        <div className="flex gap-2">
          <button
            className="rounded-md border border-slate-300 px-3 py-1 text-sm"
            onClick={() => exportReport('markdown')}
            type="button"
          >
            Export Markdown
          </button>
          <button
            className="rounded-md border border-slate-300 px-3 py-1 text-sm"
            onClick={() => exportReport('json')}
            type="button"
          >
            Export JSON
          </button>
        </div>
      </div>
      {!detail && <p className="mt-4 text-slate-600">Loading...</p>}
      {detail && (
        <div className="mt-4 space-y-4">
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <p className="font-medium">{detail.research.query}</p>
            {detail.requires_review && (
              <p className="mt-2 rounded-md bg-amber-100 p-2 text-sm text-amber-800">
                Review required: {detail.review_reason || 'Low confidence evidence.'}
              </p>
            )}
            <pre className="mt-3 whitespace-pre-wrap rounded-md bg-slate-100 p-3 text-sm">
              {detail.summary}
            </pre>
          </section>

          {metrics && (
            <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <MetricCard label="Sources" value={metrics.source_count} />
              <MetricCard label="Coverage" value={metrics.evidence_coverage_score} />
              <MetricCard label="Support ratio" value={metrics.fact_support_ratio} />
              <MetricCard label="Contradictions" value={metrics.contradiction_rate} />
            </section>
          )}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Findings</h2>
            <div className="mt-3 space-y-3">
              {(detail.report?.findings || []).map((finding) => (
                <article key={finding.claim_id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{finding.claim}</p>
                    <span className={`rounded-full px-2 py-0.5 text-xs ${confidenceBadge(finding.confidence_level)}`}>
                      {finding.confidence_level}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">Confidence: {finding.confidence}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-semibold">Evidence table</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {(detail.report?.evidence_table || []).map((source) => (
                  <li key={source.source_id} className="rounded border border-slate-200 p-2">
                    <a className="font-medium text-blue-600" href={source.url} target="_blank" rel="noreferrer">
                      {source.title}
                    </a>
                    <p className="text-xs text-slate-500">
                      {source.source_type} • credibility {source.credibility_score}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-semibold">Contradictions</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {(detail.report?.contradictions || []).length === 0 && (
                  <li className="text-slate-500">No contradictions detected.</li>
                )}
                {(detail.report?.contradictions || []).map((item) => (
                  <li key={`${item.claim_a}-${item.claim_b}`} className="rounded border border-rose-200 bg-rose-50 p-2">
                    <p className="font-medium">{item.claim_a} vs {item.claim_b}</p>
                    <p className="text-xs text-slate-600">{item.reason}</p>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Live execution timeline</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {trace.map((event, index) => (
                <li key={`${event.stage}-${event.created_at}-${index}`} className="rounded border border-slate-200 p-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{event.stage}</span>
                    <span className="text-xs text-slate-500">{event.state}</span>
                  </div>
                  <p className="text-xs text-slate-600">{event.detail}</p>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Source citations</h2>
            <ul className="mt-2 space-y-2 text-sm">
              {detail.citations.map((citation) => (
                <li key={`${citation.marker}-${citation.source_id}`}>
                  <Link className="text-blue-600" to={`/sources/${detail.research.id}`}>
                    {citation.marker}
                  </Link>{' '}
                  {citation.excerpt}
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </Layout>
  )
}

function MetricCard({ label, value }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </article>
  )
}

function SourceViewerPage() {
  const params = useParams()
  const [sources, setSources] = useState([])
  useEffect(() => {
    api(`/api/sources/${params.researchId}`)
      .then(setSources)
      .catch(() => setSources([]))
  }, [params.researchId])
  return (
    <Layout>
      <h1 className="text-2xl font-semibold">Source Viewer</h1>
      <div className="mt-4 space-y-3">
        {sources.map((source) => (
          <article key={source.id} className="rounded-md border border-slate-200 bg-white p-4">
            <a className="font-medium text-blue-600" href={source.url} rel="noreferrer" target="_blank">
              {source.title}
            </a>
            <p className="mt-1 text-xs text-slate-500">
              Type: {source.source_type} • credibility: {source.credibility_score}
            </p>
            <p className="mt-2 text-sm text-slate-600">{source.content}</p>
          </article>
        ))}
      </div>
    </Layout>
  )
}

function SettingsPage() {
  const token = useMemo(() => getToken(), [])
  const [workspace, setWorkspace] = useState(null)
  useEffect(() => {
    api('/api/workspaces/current')
      .then(setWorkspace)
      .catch(() => setWorkspace(null))
  }, [])
  return (
    <Layout>
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="mt-2 text-sm text-slate-600">Auth token status: {token ? 'Active' : 'Missing'}</p>
      <p className="mt-1 text-sm text-slate-600">Workspace: {workspace?.name || 'Unavailable'}</p>
      <button
        className="mt-4 rounded-md border border-slate-300 px-4 py-2"
        onClick={() => {
          localStorage.removeItem('astra_token')
          window.location.href = '/'
        }}
        type="button"
      >
        Sign out
      </button>
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<LoginPage />} path="/" />
        <Route element={<DashboardPage />} path="/dashboard" />
        <Route element={<ResearchQueryPage />} path="/research" />
        <Route element={<ResearchResultsPage />} path="/results/:id" />
        <Route element={<SourceViewerPage />} path="/sources/:researchId" />
        <Route element={<SettingsPage />} path="/settings" />
      </Routes>
    </BrowserRouter>
  )
}
