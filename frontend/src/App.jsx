import { useState, useEffect, useRef } from 'react'
import {
  fetchTrades,
  fetchTasks,
  createUser,
  startCertification,
  uploadFile,
  assessTask,
  skipTask,
  generateCorrections,
  issueCertificate,
  createOrg,
  getOrg,
  getCustomRubric,
  saveCustomRubric,
  getOrgAssessment,
} from './api'

const SKIPPABLE = new Set(['T1', 'T2', 'T3', 'T4', 'T5', 'P1', 'P2', 'P3', 'P4', 'P5'])
const BACKEND = 'http://localhost:8000'

export default function App() {
  const [step, setStep] = useState('welcome')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [user, setUser] = useState(null)
  const [trades, setTrades] = useState([])
  const [tradeKey, setTradeKey] = useState(null)
  const [tradeName, setTradeName] = useState('')
  const [tasks, setTasks] = useState([])
  const [certId, setCertId] = useState(null)
  const [taskIdx, setTaskIdx] = useState(0)
  const [results, setResults] = useState({})
  const [skipped, setSkipped] = useState(new Set())
  const [lastResult, setLastResult] = useState(null)
  const [cert, setCert] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState(null)
  const [correctionVideos, setCorrectionVideos] = useState(null)
  const [genLoading, setGenLoading] = useState(false)
  const [procStage, setProcStage] = useState(0)
  const [filePreview, setFilePreview] = useState(null)
  const [howVisible, setHowVisible] = useState(false)
  const stepsRef = useRef(null)

  // B2B state
  const [org, setOrg] = useState(null)
  const [orgName, setOrgName] = useState('')
  const [orgLogo, setOrgLogo] = useState('')
  const [editingRubric, setEditingRubric] = useState(null)
  const [editTrade, setEditTrade] = useState(null)
  const [editThreshold, setEditThreshold] = useState(70)
  const [copiedTrade, setCopiedTrade] = useState(null)
  // Branded assessment
  const [brandedOrg, setBrandedOrg] = useState(null)

  // Animated score counter
  const [animatedScore, setAnimatedScore] = useState(0)

  // Processing stage animation
  useEffect(() => {
    if (step !== 'processing') { setProcStage(0); return }
    if (step !== 'task') { setFilePreview(null) }
    const timers = [
      setTimeout(() => setProcStage(1), 3000),
      setTimeout(() => setProcStage(2), 10000),
      setTimeout(() => setProcStage(3), 20000),
    ]
    return () => timers.forEach(clearTimeout)
  }, [step])

  // Score counter animation (0 → actual score, 800ms ease-out)
  useEffect(() => {
    if (step !== 'result' || !lastResult) return
    setAnimatedScore(0)
    const target = lastResult.weighted_total
    const duration = 800
    const start = performance.now()
    function tick(now) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setAnimatedScore(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [step, lastResult])

  // Scroll-triggered animation for how-it-works cards
  useEffect(() => {
    if (step !== 'welcome' || brandedOrg) return
    setHowVisible(false)
    const node = stepsRef.current
    if (!node) return
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setHowVisible(true) },
      { threshold: 0.2 }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [step, brandedOrg])

  // Check URL for branded assessment link: ?org=slug&trade=tiling
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const orgSlug = params.get('org')
    const trade = params.get('trade')
    if (orgSlug && trade) {
      getOrgAssessment(orgSlug, trade).then(data => {
        setBrandedOrg(data.org)
        setTasks(data.tasks)
        setTradeKey(trade)
        setTradeName(data.trade)
        setStep('welcome') // will show branded welcome
      }).catch(() => {})
    }
  }, [])

  function isUnlocked(idx) {
    for (let i = 0; i < idx; i++) {
      const tid = tasks[i].id
      if (!results[tid] && !skipped.has(tid)) return false
    }
    return true
  }

  function allRequiredDone() {
    return tasks.every(t => results[t.id] || skipped.has(t.id))
  }

  function passedCount() {
    return tasks.filter(t => results[t.id]?.passed).length
  }

  function requiredCount() {
    return tasks.filter(t => !skipped.has(t.id)).length
  }

  async function handleRegister(e) {
    e.preventDefault()
    setErr(null)
    setLoading(true)
    try {
      const u = await createUser(name, email)
      setUser(u)
      if (brandedOrg) {
        // Branded flow — go straight to dashboard with pre-loaded tasks
        const c = await startCertification(u.user_id, tradeKey)
        setCertId(c.certification_id)
        setResults({})
        setSkipped(new Set())
        setStep('dashboard')
      } else {
        const data = await fetchTrades()
        setTrades(data.trades)
        setStep('trades')
      }
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSelectTrade(key) {
    setErr(null)
    setLoading(true)
    try {
      const data = await fetchTasks(key)
      setTasks(data.tasks)
      setTradeKey(key)
      setTradeName(data.trade)
      const c = await startCertification(user.user_id, key)
      setCertId(c.certification_id)
      setResults({})
      setSkipped(new Set())
      setStep('dashboard')
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  function handleTaskClick(idx) {
    if (!isUnlocked(idx)) return
    if (results[tasks[idx].id]?.passed) return
    if (skipped.has(tasks[idx].id)) return
    setTaskIdx(idx)
    setErr(null)
    setStep('task')
  }

  async function handleUpload(e) {
    e.preventDefault()
    const file = e.target.elements.file?.files?.[0]
    if (!file) return
    setErr(null)
    setLoading(true)
    setStep('processing')
    try {
      const upload = await uploadFile(file)
      const task = tasks[taskIdx]
      const result = await assessTask(certId, task.id, tradeKey, upload.path)
      setLastResult(result)
      setResults(prev => ({ ...prev, [task.id]: result }))
      setStep('result')
    } catch (error) {
      setErr(error.message)
      setStep('task')
    } finally {
      setLoading(false)
    }
  }

  async function handleSkip(score) {
    const task = tasks[taskIdx]
    setLoading(true)
    try {
      await skipTask(certId, task.id, score)
      setSkipped(prev => new Set([...prev, task.id]))
      setResults(prev => ({
        ...prev,
        [task.id]: {
          passed: score >= 70,
          weighted_total: score,
          scores: { safety: score, technique: score, result: score },
          feedback: `Skipped with default score of ${score}%`,
        },
      }))
      setStep('dashboard')
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  function handleNextTask() {
    for (let i = 0; i < tasks.length; i++) {
      const tid = tasks[i].id
      if (!results[tid]?.passed && !skipped.has(tid) && isUnlocked(i)) {
        setTaskIdx(i)
        setStep('task')
        return
      }
    }
    setStep('dashboard')
  }

  async function handleGetCert() {
    setErr(null)
    setLoading(true)
    try {
      const data = await issueCertificate(certId, name)
      setCert(data)
      setStep('certificate')
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  // ---- B2B: Create Org ----
  async function handleCreateOrg(e) {
    e.preventDefault()
    setErr(null)
    setLoading(true)
    try {
      const o = await createOrg(orgName, orgLogo || null)
      setOrg(o)
      const data = await fetchTrades()
      setTrades(data.trades)
      setStep('org-dashboard')
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  // ---- B2B: Load rubric for editing ----
  async function handleEditRubric(trade) {
    setErr(null)
    setLoading(true)
    try {
      const data = await getCustomRubric(org.slug, trade)
      setEditingRubric(data.rubric)
      setEditTrade(trade)
      setEditThreshold(data.pass_threshold)
      setStep('rubric-editor')
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  // ---- B2B: Save rubric ----
  async function handleSaveRubric() {
    setErr(null)
    setLoading(true)
    try {
      await saveCustomRubric(org.slug, editTrade, editingRubric, editThreshold)
      setStep('org-dashboard')
    } catch (error) {
      setErr(error.message)
    } finally {
      setLoading(false)
    }
  }

  // ---- Rubric editing helpers ----
  function updateTask(taskIdx, field, value) {
    const r = { ...editingRubric }
    r.tasks = [...r.tasks]
    r.tasks[taskIdx] = { ...r.tasks[taskIdx], [field]: value }
    setEditingRubric(r)
  }

  function updateCheck(taskIdx, category, checkIdx, value) {
    const r = { ...editingRubric }
    r.tasks = [...r.tasks]
    const task = { ...r.tasks[taskIdx] }
    task.criteria = { ...task.criteria }
    task.criteria[category] = { ...task.criteria[category] }
    task.criteria[category].checks = [...task.criteria[category].checks]
    task.criteria[category].checks[checkIdx] = value
    r.tasks[taskIdx] = task
    setEditingRubric(r)
  }

  function addCheck(taskIdx, category) {
    const r = { ...editingRubric }
    r.tasks = [...r.tasks]
    const task = { ...r.tasks[taskIdx] }
    task.criteria = { ...task.criteria }
    task.criteria[category] = { ...task.criteria[category] }
    task.criteria[category].checks = [...task.criteria[category].checks, '']
    r.tasks[taskIdx] = task
    setEditingRubric(r)
  }

  function removeCheck(taskIdx, category, checkIdx) {
    const r = { ...editingRubric }
    r.tasks = [...r.tasks]
    const task = { ...r.tasks[taskIdx] }
    task.criteria = { ...task.criteria }
    task.criteria[category] = { ...task.criteria[category] }
    task.criteria[category].checks = task.criteria[category].checks.filter((_, i) => i !== checkIdx)
    r.tasks[taskIdx] = task
    setEditingRubric(r)
  }

  function addTask() {
    const r = { ...editingRubric }
    const newId = `C${r.tasks.length + 1}`
    r.tasks = [...r.tasks, {
      id: newId,
      title: 'New Task',
      format: 'video',
      time_minutes: 5,
      instruction: 'Describe what the worker should demonstrate.',
      criteria: {
        safety: { weight: 0.3, checks: ['Safety check 1'] },
        technique: { weight: 0.4, checks: ['Technique check 1'] },
        result: { weight: 0.3, checks: ['Result check 1'] },
      }
    }]
    setEditingRubric(r)
  }

  function removeTask(taskIdx) {
    const r = { ...editingRubric }
    r.tasks = r.tasks.filter((_, i) => i !== taskIdx)
    setEditingRubric(r)
  }

  // ---- WELCOME (branded — worker via org link) ----
  if (step === 'welcome' && brandedOrg) {
    return (
      <div className="app">
        <header>
          <div className="branded-header">
            {brandedOrg.logo_url && <img src={brandedOrg.logo_url} alt="" className="org-logo" />}
            <h1>{brandedOrg.name}</h1>
            <p className="powered-by">Powered by SkillProof</p>
          </div>
        </header>
        <main key="branded-welcome" className="page-enter">
          <h2>{tradeName} Assessment</h2>
          <p className="subtitle">Complete your {tradeName.toLowerCase()} skills assessment for {brandedOrg.name}.</p>
          <form onSubmit={handleRegister}>
            <input type="text" placeholder="Your full name" value={name} onChange={e => setName(e.target.value)} required />
            <input type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} required />
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Loading...' : 'Start Assessment'}
            </button>
          </form>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- LANDING PAGE (main entry) ----
  if (step === 'welcome') {
    return (
      <div className="app landing">
        <header>
          <div className="header-inner">
            <h1>SkillProof</h1>
            <button
              className="header-link"
              onClick={async () => {
                setLoading(true)
                setErr(null)
                try {
                  const o = await createOrg('Demo Company', null)
                  setOrg(o)
                  const data = await fetchTrades()
                  setTrades(data.trades)
                  setStep('org-dashboard')
                } catch (error) {
                  setErr(error.message)
                } finally {
                  setLoading(false)
                }
              }}
              disabled={loading}
            >
              For Business
            </button>
          </div>
        </header>

        <section className="hero">
          <div className="hero-glow" />
          <h2 className="hero-headline">
            Trade Certification<br />in Minutes, Not Weeks
          </h2>
          <p className="hero-subtitle">
            AI-powered skill assessment for construction professionals. Upload a video. Get certified.
          </p>
          <button
            className="btn-hero"
            onClick={() => setStep('worker-register')}
          >
            Start Assessment &rarr;
          </button>
          <p className="hero-trust">
            Used by 500+ tradespeople &middot; BS 5385 compliant &middot; 30-second AI review
          </p>
        </section>

        <section className="how-it-works" ref={stepsRef}>
          <p className="section-label">How it works</p>
          <div className={`steps-grid${howVisible ? ' visible' : ''}`}>
            <div className="step-card">
              <span className="step-number">01</span>
              <h3>Upload Your Work</h3>
              <p>Record a short video demonstrating your trade skills on the assigned task.</p>
            </div>
            <div className="step-card">
              <span className="step-number">02</span>
              <h3>AI Assesses</h3>
              <p>Evaluated against BS 5385 and NVQ Level 2 standards in under 30 seconds.</p>
            </div>
            <div className="step-card">
              <span className="step-number">03</span>
              <h3>Get Certified</h3>
              <p>Receive a verifiable digital certificate with a unique QR code.</p>
            </div>
          </div>
        </section>

        <section className="trust-strip">
          <span className="trust-pill">30s average review time</span>
          <span className="trust-pill">97% accuracy</span>
          <span className="trust-pill">BS 5385 &amp; NVQ Level 2</span>
          <span className="trust-pill">Verifiable QR certificates</span>
        </section>

        <section className="final-cta">
          <h2>Ready to prove your skills?</h2>
          <button
            className="btn-hero"
            onClick={() => setStep('worker-register')}
          >
            Start Assessment &rarr;
          </button>
          <p className="final-cta-sub">No account needed. Takes 5 minutes.</p>
        </section>

        <footer className="landing-footer">
          <p>SkillProof &copy; 2026 &middot; Built with AI</p>
        </footer>

        {err && <p className="error landing-error">{err}</p>}
      </div>
    )
  }

  // ---- WORKER REGISTER ----
  if (step === 'worker-register') {
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')} style={{cursor:'pointer'}}>SkillProof</h1></header>
        <main key="worker-register" className="page-enter">
          <button className="btn-back" onClick={() => setStep('welcome')}>&larr; Back</button>
          <h2>Get Started</h2>
          <p className="subtitle">Enter your details to begin the assessment.</p>
          <form onSubmit={handleRegister}>
            <input type="text" placeholder="Your full name" value={name} onChange={e => setName(e.target.value)} required />
            <input type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} required />
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Loading...' : 'Continue'}
            </button>
          </form>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- ORG SETUP ----
  if (step === 'org-setup') {
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')}>SkillProof</h1><p className="header-sub">Business Setup</p></header>
        <main key="org-setup" className="page-enter">
          <button className="btn-back" onClick={() => setStep('welcome')}>
            &larr; Back
          </button>
          <h2>Set Up Your Organisation</h2>
          <p className="subtitle">Create branded assessments for your workers and candidates.</p>
          <form onSubmit={handleCreateOrg}>
            <input
              type="text"
              placeholder="Organisation name (e.g. ABC Recruitment)"
              value={orgName}
              onChange={e => setOrgName(e.target.value)}
              required
            />
            <input
              type="url"
              placeholder="Logo URL (optional)"
              value={orgLogo}
              onChange={e => setOrgLogo(e.target.value)}
            />
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Organisation'}
            </button>
          </form>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- ORG DASHBOARD ----
  if (step === 'org-dashboard') {
    const assessLink = (trade) =>
      `${window.location.origin}?org=${org.slug}&trade=${trade}`

    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')}>SkillProof</h1><p className="header-sub">{org.name}</p></header>
        <main key="org-dashboard" className="page-enter">
          <button className="btn-back" onClick={() => setStep('welcome')}>&larr; Back to home</button>
          <h2>Your Assessments</h2>
          <p className="subtitle">Customise templates and share assessment links with candidates.</p>

          <div className="org-trade-cards">
            {trades.map(t => (
              <div key={t.key} className="trade-card org-trade-card">
                <h3>{t.name}</h3>
                <p>{t.task_count} tasks · {t.level}</p>
                <div className="org-card-actions">
                  <button
                    className="btn-small"
                    onClick={() => handleEditRubric(t.key)}
                    disabled={loading}
                  >
                    Customise
                  </button>
                  <button
                    className="btn-small btn-copy"
                    onClick={() => {
                      navigator.clipboard.writeText(assessLink(t.key))
                      setCopiedTrade(t.key)
                      setTimeout(() => setCopiedTrade(null), 2000)
                    }}
                  >
                    {copiedTrade === t.key ? 'Copied' : 'Copy Link'}
                  </button>
                </div>
                <p className="assess-link">{assessLink(t.key)}</p>
              </div>
            ))}
          </div>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- RUBRIC EDITOR ----
  if (step === 'rubric-editor' && editingRubric) {
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')}>SkillProof</h1><p className="header-sub">{org.name} — Rubric Editor</p></header>
        <main key="rubric-editor" className="page-enter">
          <button className="btn-back" onClick={() => setStep('org-dashboard')}>
            &larr; Back to dashboard
          </button>
          <h2>Customise: {editingRubric.trade || editTrade}</h2>

          <div className="threshold-row">
            <label>Pass threshold: </label>
            <input
              type="number"
              min="0"
              max="100"
              value={editThreshold}
              onChange={e => setEditThreshold(Number(e.target.value))}
              className="threshold-input"
            />
            <span>%</span>
          </div>

          <div className="rubric-grid">
            {editingRubric.tasks.map((task, ti) => (
              <div key={ti} className="rubric-task-card">
                <div className="rubric-task-header">
                  <input
                    className="rubric-task-id"
                    value={task.id}
                    onChange={e => updateTask(ti, 'id', e.target.value)}
                  />
                  <input
                    className="rubric-task-title"
                    value={task.title}
                    onChange={e => updateTask(ti, 'title', e.target.value)}
                  />
                  <button className="btn-remove" onClick={() => removeTask(ti)}>✕</button>
                </div>
                <textarea
                  className="rubric-instruction"
                  value={task.instruction}
                  onChange={e => updateTask(ti, 'instruction', e.target.value)}
                  rows={2}
                />
                <div className="rubric-meta-row">
                  <label>Format:
                    <input value={task.format} onChange={e => updateTask(ti, 'format', e.target.value)} />
                  </label>
                  <label>Time (min):
                    <input type="number" value={task.time_minutes} onChange={e => updateTask(ti, 'time_minutes', Number(e.target.value))} />
                  </label>
                </div>

                {['safety', 'technique', 'result'].map(cat => (
                  <div key={cat} className="rubric-criteria-section">
                    <h4>{cat} (weight: {task.criteria[cat]?.weight || 0})</h4>
                    {(task.criteria[cat]?.checks || []).map((check, ci) => (
                      <div key={ci} className="rubric-check-row">
                        <input
                          value={check}
                          onChange={e => updateCheck(ti, cat, ci, e.target.value)}
                          className="rubric-check-input"
                        />
                        <button className="btn-remove-sm" onClick={() => removeCheck(ti, cat, ci)}>✕</button>
                      </div>
                    ))}
                    <button className="btn-add-check" onClick={() => addCheck(ti, cat)}>+ Add check</button>
                  </div>
                ))}
              </div>
            ))}
          </div>

          <button className="btn-secondary btn-add-task" onClick={addTask}>
            + Add Task
          </button>

          <button className="btn-primary" onClick={handleSaveRubric} disabled={loading}>
            {loading ? 'Saving...' : 'Save Rubric'}
          </button>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- TRADE SELECT ----
  if (step === 'trades') {
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')} style={{cursor:'pointer'}}>SkillProof</h1></header>
        <main key="trades" className="page-enter">
          <h2>Select Your Trade</h2>
          <div className="trade-cards">
            {trades.map(t => (
              <button
                key={t.key}
                className="trade-card"
                onClick={() => handleSelectTrade(t.key)}
                disabled={loading}
              >
                <h3>{t.name}</h3>
                <p>{t.task_count} tasks &middot; {t.level}</p>
                <p className="threshold">Pass: {t.pass_threshold}%</p>
              </button>
            ))}
          </div>
          {loading && <p className="loading-text">Loading tasks...</p>}
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- DASHBOARD ----
  if (step === 'dashboard') {
    const done = passedCount()
    const total = requiredCount()
    return (
      <div className="app">
        <header>
          {brandedOrg ? (
            <div className="branded-header">
              {brandedOrg.logo_url && <img src={brandedOrg.logo_url} alt="" className="org-logo" />}
              <h1>{brandedOrg.name}</h1>
              <p className="powered-by">Powered by SkillProof</p>
            </div>
          ) : (
            <h1>SkillProof</h1>
          )}
        </header>
        <main key="dashboard" className="page-enter">
          <h2>{tradeName}</h2>
          <div className="dashboard-grid">
            <div className="dashboard-tasks">
              <div className="task-list">
                {tasks.map((t, i) => {
                  const passed = results[t.id]?.passed
                  const failed = results[t.id] && !results[t.id].passed
                  const isSkipped = skipped.has(t.id)
                  const unlocked = isUnlocked(i)
                  let status = ''
                  if (passed) status = 'passed'
                  else if (failed) status = 'failed'
                  else if (isSkipped) status = 'skipped'
                  else if (!unlocked) status = 'locked'

                  return (
                    <button
                      key={t.id}
                      className={`task-card ${status}`}
                      onClick={() => handleTaskClick(i)}
                      disabled={!unlocked || passed || isSkipped}
                    >
                      <div className="task-header">
                        <span className="task-id">{t.id}</span>
                        <span className="task-title">{t.title}</span>
                        {passed && <span className="badge pass">PASS</span>}
                        {failed && <span className="badge fail">FAIL</span>}
                        {isSkipped && <span className="badge skip">SKIP</span>}
                        {!unlocked && !passed && !isSkipped && (
                          <span className="badge lock">LOCKED</span>
                        )}
                      </div>
                      <div className="task-meta">
                        {t.format} &middot; {t.time_minutes} min
                        {passed && ` \u00b7 ${results[t.id].weighted_total}%`}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
            <div className="dashboard-sidebar">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${total > 0 ? (done / total) * 100 : 0}%` }}
                />
              </div>
              <p className="progress-text">{done} / {total} tasks passed</p>
              {done > 0 && (
                <>
                  <p className="total-score">
                    {(
                      tasks
                        .filter(t => results[t.id]?.passed)
                        .reduce((sum, t) => sum + results[t.id].weighted_total, 0) /
                      done
                    ).toFixed(1)}%
                  </p>
                  <p className="total-score-label">Average Score</p>
                </>
              )}
              {allRequiredDone() && (
                <button
                  className="btn-primary"
                  style={{ width: '100%' }}
                  onClick={handleGetCert}
                  disabled={loading}
                >
                  {loading ? 'Generating Certificate...' : 'Get Certificate'}
                </button>
              )}
            </div>
          </div>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- TASK BRIEF + UPLOAD ----
  if (step === 'task') {
    const task = tasks[taskIdx]
    const canSkip = SKIPPABLE.has(task.id)
    return (
      <div className="app">
        <header>
          {brandedOrg ? (
            <div className="branded-header">
              <h1>{brandedOrg.name}</h1>
              <p className="powered-by">Powered by SkillProof</p>
            </div>
          ) : (
            <h1>SkillProof</h1>
          )}
        </header>
        <main key="task" className="page-enter">
          <button className="btn-back" onClick={() => setStep('dashboard')}>
            &larr; Back to tasks
          </button>
          <h2>{task.id}: {task.title}</h2>
          <div className="task-grid">
            <div className="task-instructions">
              <div className="task-info">
                <p><strong>Format:</strong> {task.format}</p>
                <p><strong>Time limit:</strong> {task.time_minutes} minutes</p>
              </div>
              <div className="instruction">
                <p>{task.instruction}</p>
              </div>
              {canSkip && (
                <div className="skip-options">
                  <button className="btn-skip" onClick={() => handleSkip(40)}>
                    Skip (40%)
                  </button>
                  <button className="btn-skip high" onClick={() => handleSkip(80)}>
                    Skip (80%)
                  </button>
                </div>
              )}
            </div>
            <div>
              <form onSubmit={handleUpload}>
                <label className="file-label">
                  <svg className="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Select photo or video
                  <input type="file" name="file" accept="image/*,video/*" required
                    onChange={e => {
                      const f = e.target.files?.[0]
                      if (f) setFilePreview({ url: URL.createObjectURL(f), type: f.type })
                      else setFilePreview(null)
                    }}
                  />
                </label>
                {filePreview && (
                  <div className="file-preview">
                    {filePreview.type.startsWith('video/') ? (
                      <video src={filePreview.url} controls playsInline className="preview-media" />
                    ) : (
                      <img src={filePreview.url} alt="Preview" className="preview-media" />
                    )}
                  </div>
                )}
                <button type="submit" className="btn-primary" style={{ width: '100%' }} disabled={loading}>
                  Upload &amp; Assess
                </button>
              </form>
            </div>
          </div>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- PROCESSING ----
  if (step === 'processing') {
    const task = tasks[taskIdx]
    const stages = [
      'Uploading video',
      'AI analyzing your work',
      'Checking against standards',
      'Generating feedback',
    ]
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')}>{brandedOrg ? brandedOrg.name : 'SkillProof'}</h1></header>
        <main key="processing" className="page-enter">
          <h2>Assessing: {task.title}</h2>
          <div className="processing">
            <div className="spinner">
              <div className="spinner-dot"></div>
              <div className="spinner-dot"></div>
              <div className="spinner-dot"></div>
            </div>
            <p className="processing-title">{stages[procStage]}</p>
            <div className="stage-list">
              {stages.map((s, i) => (
                <p key={i} className={`stage-item ${i < procStage ? 'done' : i === procStage ? 'active' : 'pending'}`}>
                  <span className="stage-check">{i < procStage ? '\u2713' : i === procStage ? '\u25CF' : '\u25CB'}</span> {s}
                </p>
              ))}
            </div>
            <p className="processing-note">Usually takes 20-60 seconds</p>
          </div>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- RESULT ----
  if (step === 'result') {
    const r = lastResult
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')}>{brandedOrg ? brandedOrg.name : 'SkillProof'}</h1></header>
        <main key="result" className="page-enter">
          <div className={`result-banner ${r.passed ? 'pass' : 'fail'}`}>
            <h2>{r.passed ? 'PASSED' : 'FAILED'}</h2>
            <p className="result-score">{animatedScore}%</p>
          </div>

          <div className="result-grid">
            <div className="result-scores-col">
              <div className="score-bars">
                {['safety', 'technique', 'result'].map(key => (
                  <div className="score-row" key={key}>
                    <span className="score-label">{key}</span>
                    <div className="bar">
                      <div
                        className="bar-fill"
                        style={{ width: `${r.scores[key]}%` }}
                      />
                    </div>
                    <span className="score-val">{r.scores[key]}%</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="result-feedback-col">
              {r.feedback && <p className="feedback">{r.feedback}</p>}
              {r.fail_reason && <p className="fail-reason">{r.fail_reason}</p>}

              {r.corrections && r.corrections.length > 0 && (
                <div className="corrections">
                  <h3>Issues Found ({r.corrections.length})</h3>

                  {!correctionVideos && (
                    <button
                      className="btn-generate"
                      onClick={async () => {
                        setGenLoading(true)
                        setCorrectionVideos(null)
                        try {
                          const data = await generateCorrections(r.task_result_id)
                          setCorrectionVideos(data.corrections)
                        } catch (e) {
                          setErr(e.message)
                        } finally {
                          setGenLoading(false)
                        }
                      }}
                      disabled={genLoading}
                    >
                      {genLoading ? 'Generating correction videos... (1-2 min)' : 'Show Me The Correct Way'}
                    </button>
                  )}

                  {r.corrections.map((c, i) => {
                    const cv = correctionVideos?.[i]
                    return (
                      <div key={i} className="correction-block">
                        <div className="correction-header">
                          <span className="correction-num">Error {i + 1}</span>
                          <span className={`correction-cat ${c.category}`}>{c.category}</span>
                        </div>
                        <p className="correction-error">{c.error}</p>
                        <p className="correction-explain">{c.explanation}</p>
                        {cv && cv.skipped_reason && (
                          <p className="correction-skip">{cv.skipped_reason}</p>
                        )}
                        {cv && !cv.skipped_reason && (
                          <div className="correction-demo">
                            {cv.video_path ? (
                              <video controls width="100%" playsInline>
                                <source src={`${BACKEND}/${cv.video_path}`} type="video/mp4" />
                              </video>
                            ) : (
                              <p className="correction-novid">Video failed to generate</p>
                            )}
                            {cv.narration_steps && cv.narration_steps.length > 0 && (
                              <div className="narration-steps">
                                {cv.narration_steps.map((ns, ni) => (
                                  <p key={ni} className="narration-step">
                                    <span className="step-num">&#x25CF;</span> {ns}
                                  </p>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                        {cv && cv.video_error && (
                          <p className="correction-novid">Error: {cv.video_error}</p>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>

          {r.passed ? (
            allRequiredDone() ? (
              <button
                className="btn-primary"
                onClick={handleGetCert}
                disabled={loading}
              >
                {loading ? 'Generating...' : 'Get Certificate'}
              </button>
            ) : (
              <button className="btn-primary" onClick={handleNextTask}>
                Next Task
              </button>
            )
          ) : (
            <button className="btn-primary" onClick={() => setStep('task')}>
              Retry
            </button>
          )}
          <button
            className="btn-secondary"
            onClick={() => setStep('dashboard')}
          >
            Back to Dashboard
          </button>
          {err && <p className="error">{err}</p>}
        </main>
      </div>
    )
  }

  // ---- CERTIFICATE ----
  if (step === 'certificate') {
    return (
      <div className="app">
        <header><h1 className="logo-link" onClick={() => setStep('welcome')}>{brandedOrg ? brandedOrg.name : 'SkillProof'}</h1></header>
        <main key="certificate" className="page-enter">
          <div className="certificate-wrapper">
            <h2>Certificate Issued</h2>
            <div className="cert-card">
              {cert.org_name && <p className="cert-org">{cert.org_name}</p>}
              <p className="cert-name">{cert.worker_name}</p>
              <p className="cert-trade">{cert.trade}</p>
              <p className="cert-score">
                Overall Score: {cert.overall_score.toFixed(1)}%
              </p>
              <div className="cert-scores">
                <span>Safety: {cert.scores.safety}%</span>
                <span>Technique: {cert.scores.technique}%</span>
                <span>Result: {cert.scores.result}%</span>
              </div>
              <p className="cert-meta">ID: {cert.cert_id}</p>
              <p className="cert-meta">
                Issued: {new Date(cert.issued_at).toLocaleDateString()}
              </p>
              {cert.org_name && (
                <p className="cert-verified">Verified by SkillProof</p>
              )}
            </div>
            <a
              href={`${BACKEND}/${cert.pdf_path}`}
              className="btn-primary"
              style={{ width: '100%', display: 'block' }}
              target="_blank"
              rel="noopener noreferrer"
            >
              Download PDF Certificate
            </a>
            <button
              className="btn-secondary"
              style={{ width: '100%' }}
              onClick={() => setStep('dashboard')}
            >
              Back to Dashboard
            </button>
          </div>
        </main>
      </div>
    )
  }

  return null
}
