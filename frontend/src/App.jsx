import { useEffect, useMemo, useState } from 'react'
import {
  BrowserRouter,
  Link,
  Route,
  Routes,
  useNavigate,
  useParams,
} from 'react-router-dom'

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

function formatTimestamp(value) {
  if (!value) return 'Unknown'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Unknown'
  return date.toLocaleString()
}

function LoadingState({ label = 'Loading...' }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
      {label}
    </div>
  )
}

function EmptyState({ title, subtitle }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
      <p className="font-medium text-slate-700">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
    </div>
  )
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
        <p className="mt-2 text-sm text-slate-600">
          Sign in to run research sessions.
        </p>
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
          <button
            className="w-full rounded-md bg-slate-900 p-2 text-white"
            type="submit"
          >
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
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
                {item.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Version: {item.version}
            </p>
          </Link>
        ))}
        {items.length === 0 && (
          <p className="text-sm text-slate-500">No sessions yet.</p>
        )}
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
  const [recencyDays, setRecencyDays] = useState(30)
  const [allowDomains, setAllowDomains] = useState('')
  const [denyDomains, setDenyDomains] = useState('')
  const [advancedOpen, setAdvancedOpen] = useState(false)
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
          recency_days: recencyDays,
          allow_domains: allowDomains
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean),
          deny_domains: denyDomains
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean),
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
      <p className="mt-1 text-sm text-slate-600">
        Use demo prompts or configure search controls.
      </p>
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
        <button
          type="button"
          className="text-sm text-slate-600 underline decoration-slate-300 underline-offset-4"
          onClick={() => setAdvancedOpen((value) => !value)}
        >
          {advancedOpen ? 'Hide advanced controls' : 'Show advanced controls'}
        </button>
        {advancedOpen && (
          <div className="grid grid-cols-1 gap-3 rounded-md border border-slate-200 bg-white p-3 md:grid-cols-3">
            <label className="text-sm">
              Recency days
              <input
                className="mt-1 w-full rounded-md border border-slate-300 p-2"
                type="number"
                min="1"
                max="3650"
                value={recencyDays}
                onChange={(event) => setRecencyDays(Number(event.target.value))}
              />
            </label>
            <label className="text-sm md:col-span-2">
              Allow domains (comma-separated)
              <input
                className="mt-1 w-full rounded-md border border-slate-300 p-2"
                placeholder="nature.com, fda.gov"
                value={allowDomains}
                onChange={(event) => setAllowDomains(event.target.value)}
              />
            </label>
            <label className="text-sm md:col-span-2">
              Deny domains (comma-separated)
              <input
                className="mt-1 w-full rounded-md border border-slate-300 p-2"
                placeholder="reddit.com, quora.com"
                value={denyDomains}
                onChange={(event) => setDenyDomains(event.target.value)}
              />
            </label>
          </div>
        )}
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
        <button
          className="rounded-md bg-slate-900 px-5 py-2 text-white"
          type="submit"
        >
          Run research
        </button>
      </form>
    </Layout>
  )
}

function ResearchResultsPage() {
  const params = useParams()
  const [detail, setDetail] = useState(null)
  const [detailError, setDetailError] = useState('')
  const [trace, setTrace] = useState([])
  const [traceError, setTraceError] = useState('')
  const [metrics, setMetrics] = useState(null)
  const [metricsError, setMetricsError] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedClaimId, setSelectedClaimId] = useState('')
  const [sourceTypeFilter, setSourceTypeFilter] = useState('all')

  useEffect(() => {
    api(`/api/research/${params.id}`)
      .then((payload) => {
        setDetail(payload)
        setDetailError('')
      })
      .catch(() => {
        setDetail(null)
        setDetailError('Unable to load the research report.')
      })
      .finally(() => setLoading(false))
    api(`/api/research/${params.id}/trace`)
      .then((payload) => {
        setTrace(payload)
        setTraceError('')
      })
      .catch(() => {
        setTrace([])
        setTraceError('Timeline unavailable.')
      })
    api(`/api/research/${params.id}/metrics`)
      .then((payload) => {
        setMetrics(payload)
        setMetricsError('')
      })
      .catch(() => {
        setMetrics(null)
        setMetricsError('Metrics unavailable.')
      })
  }, [params.id])

  const findingMap = useMemo(() => {
    const entries = (detail?.report?.findings || []).map((finding) => [
      finding.claim_id,
      finding,
    ])
    return Object.fromEntries(entries)
  }, [detail?.report?.findings])

  const selectedFinding =
    selectedClaimId && findingMap[selectedClaimId]
      ? findingMap[selectedClaimId]
      : null

  const evidenceTable = useMemo(() => {
    const rows = [...(detail?.report?.evidence_table || [])]
    rows.sort((a, b) => b.credibility_score - a.credibility_score)
    if (sourceTypeFilter === 'all') return rows
    return rows.filter((row) => row.source_type === sourceTypeFilter)
  }, [detail?.report?.evidence_table, sourceTypeFilter])

  const sourceTypeOptions = useMemo(() => {
    return Array.from(
      new Set(
        (detail?.report?.evidence_table || []).map((row) => row.source_type)
      )
    )
  }, [detail?.report?.evidence_table])

  const exportReport = async (format) => {
    const response = await fetch(
      `${API_BASE}/api/research/${params.id}/export?format=${format}`,
      {
        headers: authHeaders(),
      }
    )
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
      {loading && (
        <LoadingState label="Fetching report, metrics, and timeline..." />
      )}
      {!loading && !detail && (
        <EmptyState
          title="Research report unavailable"
          subtitle={
            detailError || 'Try rerunning this query from the dashboard.'
          }
        />
      )}
      {detail && (
        <div className="mt-4 space-y-4">
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <p className="font-medium">{detail.research.query}</p>
            {detail.requires_review && (
              <p className="mt-2 rounded-md bg-amber-100 p-2 text-sm text-amber-800">
                Review required:{' '}
                {detail.review_reason || 'Low confidence evidence.'}
              </p>
            )}
            <pre className="mt-3 whitespace-pre-wrap rounded-md bg-slate-100 p-3 text-sm">
              {detail.summary}
            </pre>
            <p className="mt-2 text-xs text-slate-500">
              Schema {detail.report?.schema_version || 'unknown'} • pipeline{' '}
              {detail.report?.provenance?.pipeline_version || 'unknown'} •
              generated{' '}
              {formatTimestamp(detail.report?.provenance?.generated_at)}
            </p>
          </section>

          {metrics && (
            <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <MetricCard label="Sources" value={metrics.source_count} />
              <MetricCard
                label="Coverage"
                value={metrics.evidence_coverage_score}
              />
              <MetricCard
                label="Support ratio"
                value={metrics.fact_support_ratio}
              />
              <MetricCard
                label="Contradictions"
                value={metrics.contradiction_rate}
              />
            </section>
          )}
          {metricsError && (
            <p className="text-sm text-amber-700">{metricsError}</p>
          )}

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">Findings</h2>
            <p className="mt-1 text-sm text-slate-500">
              Click a claim to inspect linked evidence excerpts and confidence
              rationale.
            </p>
            <div className="mt-3 space-y-3">
              {(detail.report?.findings || []).map((finding) => (
                <article
                  key={finding.claim_id}
                  className={`cursor-pointer rounded-md border p-3 transition ${
                    selectedClaimId === finding.claim_id
                      ? 'border-slate-500 bg-slate-50'
                      : 'border-slate-200'
                  }`}
                  onClick={() => setSelectedClaimId(finding.claim_id)}
                >
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{finding.claim}</p>
                    <span
                      title={finding.confidence_rationale}
                      className={`rounded-full px-2 py-0.5 text-xs ${confidenceBadge(finding.confidence_level)}`}
                    >
                      {finding.confidence_level}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Confidence: {finding.confidence} • Support count:{' '}
                    {finding.support_count}
                  </p>
                  {finding.confidence_rationale && (
                    <p className="mt-1 text-xs text-slate-500">
                      {finding.confidence_rationale}
                    </p>
                  )}
                </article>
              ))}
            </div>
            {selectedFinding && (
              <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
                <p className="font-medium">
                  Evidence for {selectedFinding.claim_id}
                </p>
                <ul className="mt-2 space-y-2">
                  {(selectedFinding.support || []).map((item) => (
                    <li
                      key={`${item.marker}-${item.source_id}`}
                      className="rounded border border-slate-200 bg-white p-2"
                    >
                      <p className="font-medium">
                        {item.marker} • source #{item.source_id}
                      </p>
                      <p className="text-slate-600">{item.excerpt}</p>
                    </li>
                  ))}
                  {selectedFinding.support?.length === 0 && (
                    <li className="text-slate-500">
                      No direct support excerpts captured for this claim.
                    </li>
                  )}
                </ul>
              </div>
            )}
          </section>

          <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-lg font-semibold">Evidence table</h2>
                <select
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                  value={sourceTypeFilter}
                  onChange={(event) => setSourceTypeFilter(event.target.value)}
                >
                  <option value="all">All types</option>
                  {sourceTypeOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
              <ul className="mt-3 space-y-2 text-sm">
                {evidenceTable.map((source) => (
                  <li
                    key={source.source_id}
                    className="rounded border border-slate-200 p-2"
                  >
                    <a
                      className="font-medium text-blue-600"
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {source.title}
                    </a>
                    <p className="text-xs text-slate-500">
                      {source.source_type} • credibility{' '}
                      {source.credibility_score}
                    </p>
                  </li>
                ))}
                {evidenceTable.length === 0 && (
                  <li className="text-slate-500">
                    No evidence rows match the selected source type.
                  </li>
                )}
              </ul>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-5">
              <h2 className="text-lg font-semibold">Contradictions</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {(detail.report?.contradictions || []).length === 0 && (
                  <li className="text-slate-500">
                    No contradictions detected.
                  </li>
                )}
                {(detail.report?.contradictions || []).map((item) => (
                  <li
                    key={`${item.claim_a}-${item.claim_b}`}
                    className="rounded border border-rose-200 bg-rose-50 p-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">
                        {item.claim_a} vs {item.claim_b}
                      </p>
                      <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs text-rose-700">
                        {item.severity || 'medium'}
                      </span>
                    </div>
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
                <li
                  key={`${event.stage}-${event.created_at}-${index}`}
                  className="rounded border border-slate-200 p-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{event.stage}</span>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>{event.state}</span>
                      <span>{Number(event.latency_ms || 0).toFixed(1)} ms</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600">{event.detail}</p>
                  <p className="text-xs text-slate-400">
                    {formatTimestamp(event.created_at)}
                  </p>
                </li>
              ))}
              {trace.length === 0 && (
                <li className="text-slate-500">
                  No timeline events available.
                </li>
              )}
            </ul>
            {traceError && (
              <p className="mt-2 text-xs text-amber-700">{traceError}</p>
            )}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">Source citations</h2>
              <Link
                className="text-sm text-blue-600"
                to={`/sources/${detail.research.id}`}
              >
                Open source viewer →
              </Link>
            </div>
            <ul className="mt-2 space-y-2 text-sm">
              {detail.citations.map((citation) => (
                <li key={`${citation.marker}-${citation.source_id}`}>
                  <Link
                    className="text-blue-600"
                    to={`/sources/${detail.research.id}`}
                  >
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
  const [filterText, setFilterText] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    api(`/api/sources/${params.researchId}`)
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setLoading(false))
  }, [params.researchId])
  const filtered = useMemo(() => {
    const term = filterText.trim().toLowerCase()
    if (!term) return sources
    return sources.filter(
      (source) =>
        source.title.toLowerCase().includes(term) ||
        source.url.toLowerCase().includes(term) ||
        source.content.toLowerCase().includes(term)
    )
  }, [sources, filterText])
  return (
    <Layout>
      <h1 className="text-2xl font-semibold">Source Viewer</h1>
      <input
        className="mt-3 w-full rounded-md border border-slate-300 p-2 text-sm"
        placeholder="Filter by title, URL, or content..."
        value={filterText}
        onChange={(event) => setFilterText(event.target.value)}
      />
      <div className="mt-4 space-y-3">
        {loading && <LoadingState label="Loading source payloads..." />}
        {!loading && filtered.length === 0 && (
          <EmptyState
            title="No sources match this filter"
            subtitle="Try a different keyword or open a different session."
          />
        )}
        {filtered.map((source) => (
          <article
            key={source.id}
            className="rounded-md border border-slate-200 bg-white p-4"
          >
            <a
              className="font-medium text-blue-600"
              href={source.url}
              rel="noreferrer"
              target="_blank"
            >
              {source.title}
            </a>
            <p className="mt-1 text-xs text-slate-500">
              Type: {source.source_type} • credibility:{' '}
              {source.credibility_score}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Author: {source.source_author || 'Unknown'} • Published:{' '}
              {formatTimestamp(source.published_at)} • Retrieved:{' '}
              {formatTimestamp(source.retrieved_at)}
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
      <p className="mt-2 text-sm text-slate-600">
        Auth token status: {token ? 'Active' : 'Missing'}
      </p>
      <p className="mt-1 text-sm text-slate-600">
        Workspace: {workspace?.name || 'Unavailable'}
      </p>
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
