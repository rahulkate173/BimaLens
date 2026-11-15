import { useEffect, useRef, useState } from 'react'
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  AudioLines,
  BadgeCheck,
  Bell,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  FilePlus2,
  FileSearch2,
  FileText,
  HeartHandshake,
  Home,
  Languages,
  Lightbulb,
  ListChecks,
  LockKeyhole,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Plus,
  Search,
  Send,
  Shield,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from 'lucide-react'
import {
  getPolicies,
  getPolicy,
  getPolicyPdfLink,
  getPolicySummary,
  getSarvamTTS,
  getCurrentAccount,
  askQuestion,
  signIn,
  signOut,
  signUp,
  uploadPolicy,
  updateAccount,
  updateNotificationPreferences,
  assessPolicyFit,
  getClaimChecklist,
} from './api/client'

const POLICY = {
  name: "LIC's New Jeevan Shanti",
  kind: 'Deferred annuity plan',
  insurer: 'Life Insurance Corporation of India',
  uin: '512N338V01',
  uploaded: 'Added today',
  pages: 21,
}

const NAV_ITEMS = [
  { id: '/app/overview', label: 'Overview', icon: Home },
  { id: '/app/policies', label: 'My policies', icon: FileText, count: '01' },
  { id: '/app/ask', label: 'Ask your policy', icon: MessageCircle },
  { id: '/app/fit', label: 'Coverage fit', icon: ShieldCheck },
  { id: '/app/claims', label: 'Claim companion', icon: ClipboardCheck },
]

const facts = [
  {
    label: 'Free-look period',
    value: '15 days',
    detail: '30 days when purchased online',
    page: 'Page 1',
    tone: 'mint',
  },
  {
    label: 'Important document',
    value: 'Existence certificate',
    detail: 'Required when requested for annuity payments',
    page: 'Page 2',
    tone: 'peach',
  },
  {
    label: 'Death claim notice',
    value: 'Within 90 days',
    detail: 'Written notice with the death certificate',
    page: 'Page 2',
    tone: 'lavender',
  },
]

function routeFromHash() {
  const hash = window.location.hash.replace(/^#/, '')
  return hash.startsWith('/app/') || hash === '/login' || hash === '/signup' ? hash : '/'
}

function AppLink({ to, onNavigate, className = '', children, ...props }) {
  return (
    <a
      href={`#${to}`}
      className={className}
      onClick={(event) => {
        event.preventDefault()
        onNavigate(to)
      }}
      {...props}
    >
      {children}
    </a>
  )
}

function Brand({ compact = false }) {
  return (
    <span className={`brand ${compact ? 'brand-compact' : ''}`}>
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span>Bima<span className="brand-lens">Lens</span></span>
    </span>
  )
}

function LandingPage({ navigate }) {
  return (
    <div className="landing">
      <header className="landing-header">
        <AppLink to="/" onNavigate={navigate} className="brand-link" aria-label="BimaLens home">
          <Brand />
        </AppLink>
        <nav className="landing-nav" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#features">What you can do</a>
          <a href="#trust">Our promise</a>
        </nav>
        <div className="landing-actions">
          <AppLink to="/login" onNavigate={navigate} className="text-link">Sign in</AppLink>
          <button className="button button-dark button-small" onClick={() => navigate('/signup')}>
            Create account <ArrowRight size={15} />
          </button>
        </div>
      </header>

      <main>
        <section className="hero-section">
          <div className="hero-orbit hero-orbit-one" />
          <div className="hero-orbit hero-orbit-two" />
          <div className="hero-content">
            <div className="eyebrow eyebrow-centered"><span className="eyebrow-dot" /> Insurance, in focus</div>
            <h1>Why don’t people understand<br className="desktop-break" /> the insurance policies they buy?</h1>
            <p className="hero-description">
              Because the important details are buried in the fine print.
              BimaLens makes your policy easier to understand, one cited answer at a time.
            </p>
            <div className="hero-actions">
              <button className="button button-dark button-large" onClick={() => navigate('/signup')}>
                Understand my policy <ArrowRight size={17} />
              </button>
              <a className="button button-light button-large" href="#how-it-works">
                See how it works <ArrowDown size={16} />
              </a>
            </div>
            <div className="hero-note">
              <span className="avatar-stack" aria-hidden="true"><i>R</i><i>A</i><i>M</i></span>
              <span>Built for real policyholders, not insurance jargon.</span>
            </div>
          </div>

          <div className="preview-wrap" aria-label="Product preview">
            <div className="preview-topbar">
              <div className="window-dots"><i /><i /><i /></div>
              <div className="preview-crumb"><FileText size={13} /> Your policy, made clear</div>
              <div className="preview-status"><span /> Analysis complete</div>
              <button className="preview-more" aria-label="More options"><MoreHorizontal size={18} /></button>
            </div>
            <div className="preview-body">
              <aside className="preview-side">
                <div className="preview-mini-label">POLICY OVERVIEW</div>
                <div className="preview-doc-icon"><FileText size={20} /></div>
                <strong>{POLICY.name}</strong>
                <span>{POLICY.kind} · {POLICY.pages} pages</span>
                <div className="preview-progress"><i /></div>
                <div className="preview-mini-label preview-mini-spaced">KEY DETAILS</div>
                <div className="preview-side-row"><span>Free-look</span><b>15 days</b></div>
                <div className="preview-side-row"><span>Plan type</span><b>Annuity</b></div>
                <div className="preview-side-row"><span>Source</span><b>Page 1–2</b></div>
                <button className="preview-ask" onClick={() => navigate('/app/ask')}><MessageCircle size={14} /> Ask a question</button>
              </aside>
              <div className="preview-main">
                <div className="preview-greeting">
                  <div>
                    <div className="preview-mini-label">YOUR POLICY SNAPSHOT</div>
                    <h3>A clearer view of what matters.</h3>
                  </div>
                  <span className="preview-sparkle"><Sparkles size={16} /></span>
                </div>
                <div className="preview-facts">
                  <div className="preview-fact fact-green">
                    <span><Clock3 size={15} /> Free-look period</span>
                    <strong>15 days</strong>
                    <small>30 days for online purchase</small>
                  </div>
                  <div className="preview-fact fact-cream">
                    <span><FileCheck2 size={15} /> To remember</span>
                    <strong>Existence certificate</strong>
                    <small>May be required for annuity payments</small>
                  </div>
                </div>
                <div className="preview-citation">
                  <div className="citation-mark"><BookOpen size={15} /></div>
                  <div><small>STRAIGHT FROM YOUR POLICY</small><p>“You may return the policy within 15 days...”</p><span>Page 1 <ChevronRight size={12} /> Free Look Period</span></div>
                  <BadgeCheck size={17} className="citation-check" />
                </div>
                <div className="preview-bottom">
                  <span><ShieldCheck size={13} /> Every detail links to its source</span>
                  <span className="preview-bottom-link" onClick={() => navigate('/app/reader')}>Open policy <ArrowUpRight size={13} /></span>
                </div>
              </div>
            </div>
          </div>
          <div className="hero-under"><span>POLICY CLARITY, FROM THE FIRST PAGE</span><span>01 — 04</span></div>
        </section>

        <section className="ticker" aria-label="BimaLens capabilities">
          <span><FileSearch2 size={16} /> Read the fine print</span><i />
          <span><MessageCircle size={16} /> Ask with confidence</span><i />
          <span><ClipboardCheck size={16} /> Get claim-ready</span><i />
          <span><Languages size={16} /> In your language</span>
        </section>

        <section id="how-it-works" className="section how-section">
          <div className="section-heading">
            <div><div className="eyebrow">A little less fine print</div><h2>From policy pile<br />to peace of mind.</h2></div>
            <p>One place to understand the cover you have, find the answers you need, and prepare for the moments that matter.</p>
          </div>
          <div className="steps-grid">
            <article className="step-card step-card-upload">
              <div className="step-number">01 / ADD</div>
              <div className="step-illustration upload-illustration"><FileText /><span className="upload-spark"><Sparkles size={15} /></span><span className="upload-plus"><Plus size={14} /></span></div>
              <h3>Bring your policy</h3><p>Upload a policy PDF to your private workspace.</p>
              <button className="step-link" onClick={() => navigate('/app/overview')}>Add a policy <ArrowRight size={15} /></button>
            </article>
            <article className="step-card step-card-ask">
              <div className="step-number">02 / UNDERSTAND</div>
              <div className="step-illustration chat-illustration"><div className="chat-bubble">Does the policy have a free-look period?</div><div className="chat-answer"><Check size={12} /> Yes — find the exact wording on page 1.</div><span className="chat-star"><Sparkles size={15} /></span></div>
              <h3>Ask in plain language</h3><p>Get simple explanations grounded in your actual policy wording.</p>
              <button className="step-link" onClick={() => navigate('/app/ask')}>Ask a question <ArrowRight size={15} /></button>
            </article>
            <article className="step-card step-card-ready">
              <div className="step-number">03 / MOVE FORWARD</div>
              <div className="step-illustration ready-illustration"><div className="ready-ring"><ShieldCheck size={27} /></div><div className="ready-label"><CheckCircle2 size={13} /> Your next steps, clearly laid out</div><span className="ready-sun">✳</span></div>
              <h3>Feel ready for what’s next</h3><p>See important details and prepare documents before you need them.</p>
              <button className="step-link" onClick={() => navigate('/app/claims')}>Explore claim help <ArrowRight size={15} /></button>
            </article>
          </div>
        </section>

        <section id="features" className="section feature-section">
          <div className="feature-copy">
            <div className="eyebrow">Your policy, not the guesswork</div>
            <h2>Clarity you can<br /><span>check for yourself.</span></h2>
            <p>Every explanation points back to the page and clause it came from. Read the source, ask a follow-up, and make your own informed decision.</p>
            <button className="button button-dark" onClick={() => navigate('/app/reader')}>Explore the policy reader <ArrowRight size={16} /></button>
            <div className="feature-points">
              <div><span><Check size={13} /></span>Answers grounded in your document</div>
              <div><span><Check size={13} /></span>Page and clause references included</div>
              <div><span><Check size={13} /></span>Honest when something isn’t clear</div>
            </div>
          </div>
          <div className="feature-visual">
            <div className="paper-shadow" />
            <div className="paper-card">
              <div className="paper-header"><span>POLICY EXTRACT</span><span>PAGE 01 / 21</span></div>
              <h4>LIC’s New Jeevan Shanti</h4>
              <p className="paper-subtitle">A Non-Linked, Non-Participating, Individual, Single Premium, Deferred Annuity Plan</p>
              <div className="paper-rule" />
              <p className="paper-paragraph">We would request you to go through the terms and conditions of the Policy and in case you disagree with any of the terms and conditions...</p>
              <div className="paper-highlight"><span className="highlight-pin"><Search size={12} /></span><mark>you may return the Policy within a period of 15 days (30 days if this policy is purchased online)</mark></div>
              <div className="paper-citation"><BookOpen size={13} /> Free Look Period <span>·</span> Page 1</div>
              <div className="paper-footer"><span>Verified against your document</span><BadgeCheck size={14} /></div>
            </div>
            <div className="source-float"><span><BookOpen size={14} /></span><div><b>Page 1</b><small>Original policy source</small></div><ChevronRight size={14} /></div>
            <span className="visual-orbit orbit-a" /><span className="visual-orbit orbit-b" />
          </div>
        </section>

        <section id="trust" className="trust-band">
          <div className="trust-icon"><LockKeyhole size={21} /></div>
          <div><div className="eyebrow">A promise worth keeping</div><h2>Your policy stays the source of truth.</h2><p>BimaLens explains what it finds in your document. It does not replace your insurer, policy wording, or professional advice.</p></div>
          <div className="trust-signature"><span>01</span><b>Grounded.<br />Clear. Yours.</b></div>
        </section>

        <section className="closing-cta">
          <div className="closing-flower">✳</div>
          <div className="eyebrow eyebrow-centered">Make the fine print feel smaller</div>
          <h2>Know what your policy says.<br />Know where to find it.</h2>
          <button className="button button-dark button-large" onClick={() => navigate('/signup')}>Create your BimaLens account <ArrowRight size={16} /></button>
          <small>Your private workspace is ready after signup.</small>
        </section>
      </main>
      <footer className="landing-footer">
        <AppLink to="/" onNavigate={navigate} className="brand-link"><Brand compact /></AppLink>
        <span>Insurance, in focus.</span>
        <span>© 2026 BimaLens · A prototype for clearer cover</span>
      </footer>
    </div>
  )
}

function initialsFor(name = '') {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'U'
}

function AppShell({ route, navigate, account, policies, onOpenPolicy, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const active = route === '/app/reader' ? '/app/policies' : route
  const initials = initialsFor(account?.name)
  const workspacePolicy = policies[0]

  return (
    <div className="app-shell">
      {sidebarOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
      <aside className={`app-sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <AppLink to="/" onNavigate={navigate} className="app-brand"><Brand /></AppLink>
        <div className="workspace-picker"><div className="workspace-avatar">P</div><span><b>Personal space</b><small>My policies</small></span><ChevronDown size={15} /></div>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="side-nav" aria-label="Workspace">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            return <AppLink key={item.id} to={item.id} onNavigate={(path) => { navigate(path); setSidebarOpen(false) }} className={`side-nav-link ${active === item.id ? 'active' : ''}`}>
              <Icon size={17} strokeWidth={1.8} /><span>{item.label}</span>{item.count && <small>{item.count}</small>}
            </AppLink>
          })}
        </nav>
        <div className="sidebar-policy">
          <div className="sidebar-policy-top"><span className="sidebar-policy-icon"><FileText size={15} /></span><span className="sidebar-policy-status">{workspacePolicy?.status?.toUpperCase() || 'EMPTY'}</span></div>
          <b>{workspacePolicy?.filename || 'No policy added yet'}</b>
          <small>{workspacePolicy ? 'Private policy document' : 'Upload a PDF to get started'}</small>
          {workspacePolicy?.status === 'ready'
            ? <button className="sidebar-policy-link" onClick={() => { onOpenPolicy(workspacePolicy.id); setSidebarOpen(false) }}>View policy <ArrowRight size={13} /></button>
            : <AppLink to="/app/policies" onNavigate={(path) => { navigate(path); setSidebarOpen(false) }}>{workspacePolicy ? 'Check status' : 'Add a policy'} <ArrowRight size={13} /></AppLink>}
        </div>
        <div className="sidebar-bottom">
          <button className="sidebar-help"><CircleHelp size={16} /> Help & support <ArrowUpRight size={13} /></button>
          <button className="user-profile user-profile-button" onClick={() => navigate('/app/account')}><div className="profile-avatar">{initials}</div><div><b>{account?.name}</b><small>Personal account</small></div><MoreHorizontal size={17} /></button>
        </div>
      </aside>
      <div className="app-main">
        <header className="app-topbar">
          <button className="mobile-menu" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}><Menu size={19} /></button>
          <div className="breadcrumb"><span>Workspace</span><ChevronRight size={14} /><b>{NAV_ITEMS.find((item) => item.id === active)?.label ?? (route === '/app/account' ? 'Account' : route === '/app/notifications' ? 'Notifications' : 'Policy reader')}</b></div>
          <div className="topbar-actions"><span className="secure-label"><LockKeyhole size={12} /> Private workspace</span><button className="icon-button notification-button" aria-label="Notifications" title="Notifications" onClick={() => navigate('/app/notifications')}><Bell size={17} /></button><button className="topbar-avatar topbar-avatar-button" aria-label="Account settings" title="Account settings" onClick={() => navigate('/app/account')}>{initials}</button></div>
        </header>
        <main className="app-content">{children}</main>
      </div>
    </div>
  )
}

function AuthPage({ mode, navigate, onAuthenticated, bootstrapError = '' }) {
  const isSignup = mode === 'signup'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const account = isSignup
        ? await signUp(name, email, password)
        : await signIn(email, password)
      onAuthenticated(account)
      navigate('/app/overview')
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'We could not connect to BimaLens. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return <main className="auth-page">
    <AppLink to="/" onNavigate={navigate} className="auth-brand"><Brand /></AppLink>
    <section className="auth-card">
      <div className="eyebrow">{isSignup ? 'YOUR PRIVATE WORKSPACE' : 'WELCOME BACK'}</div>
      <h1>{isSignup ? 'Create your account.' : 'Sign in to BimaLens.'}</h1>
      <p>{isSignup ? 'Keep your policies and clear answers together in one place.' : 'Pick up where you left off with your policies.'}</p>
      {bootstrapError && <div className="form-error" role="alert">{bootstrapError}</div>}
      <form className="auth-form" onSubmit={submit}>
        {isSignup && <label>Full name<input autoComplete="name" required minLength="2" maxLength="80" value={name} onChange={(event) => setName(event.target.value)} /></label>}
        <label>Email address<input type="email" autoComplete="email" required maxLength="254" value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>Password<input type="password" autoComplete={isSignup ? 'new-password' : 'current-password'} required minLength={isSignup ? 8 : 1} maxLength="128" value={password} onChange={(event) => setPassword(event.target.value)} />{isSignup && <small>Use at least 8 characters.</small>}</label>
        {error && <div className="form-error" role="alert">{error}</div>}
        <button className="button button-dark auth-submit" type="submit" disabled={submitting}>{submitting ? 'Please wait…' : isSignup ? 'Create account' : 'Sign in'} <ArrowRight size={15} /></button>
      </form>
      <div className="auth-switch">{isSignup ? 'Already have an account?' : 'New to BimaLens?'} <button onClick={() => navigate(isSignup ? '/login' : '/signup')}>{isSignup ? 'Sign in' : 'Create an account'}</button></div>
      <div className="auth-privacy"><LockKeyhole size={13} /> Your account is protected with a secure, private session.</div>
    </section>
  </main>
}

function AccountPage({ account, onAccountChange, onSignOut }) {
  const [name, setName] = useState(account.name)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [signOutError, setSignOutError] = useState('')

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const updated = await updateAccount(name)
      onAccountChange(updated)
      setMessage('Your account details have been saved.')
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not save your account details.')
    } finally {
      setSaving(false)
    }
  }

  const signOutAccount = async () => {
    setSignOutError('')
    try {
      await onSignOut()
    } catch {
      setSignOutError('Could not sign out. Check your connection and try again.')
    }
  }

  return <div className="page settings-page">
    <PageTitle eyebrow="YOUR PROFILE" title="Account" description="Manage the details attached to your private BimaLens workspace." />
    <form className="dashboard-card settings-card" onSubmit={save}>
      <div className="settings-avatar">{initialsFor(account.name)}</div>
      <label className="settings-field">Full name<input required minLength="2" maxLength="80" value={name} onChange={(event) => setName(event.target.value)} /></label>
      <label className="settings-field">Email address<input value={account.email} readOnly /></label>
      {message && <p className="settings-success" role="status">{message}</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {signOutError && <p className="form-error" role="alert">{signOutError}</p>}
      <div className="settings-actions"><button className="button button-dark" type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</button><button className="button button-outline" type="button" onClick={signOutAccount}>Sign out</button></div>
    </form>
  </div>
}

function NotificationsPage({ account, onAccountChange }) {
  const [preferences, setPreferences] = useState(account.notifications)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [savingKey, setSavingKey] = useState('')

  const updatePreference = async (key) => {
    const updatedPreferences = { ...preferences, [key]: !preferences[key] }
    setSavingKey(key)
    setError('')
    setSaved(false)
    try {
      const updated = await updateNotificationPreferences(updatedPreferences)
      setPreferences(updated.notifications)
      onAccountChange(updated)
      setSaved(true)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not save notification preferences.')
    } finally {
      setSavingKey('')
    }
  }

  return <div className="page settings-page">
    <PageTitle eyebrow="STAY IN THE LOOP" title="Notifications" description="Choose which account updates you want to keep enabled." />
    <section className="dashboard-card notification-settings">
      <div className="notification-setting"><div><b>Policy updates</b><p>Important changes to policy processing and analysis.</p></div><button className={`setting-switch ${preferences.policy_updates ? 'setting-switch-on' : ''}`} role="switch" aria-checked={preferences.policy_updates} aria-label="Policy updates" disabled={Boolean(savingKey)} onClick={() => updatePreference('policy_updates')}><span /></button></div>
      <div className="notification-setting"><div><b>Product updates</b><p>Occasional news about BimaLens features and improvements.</p></div><button className={`setting-switch ${preferences.product_updates ? 'setting-switch-on' : ''}`} role="switch" aria-checked={preferences.product_updates} aria-label="Product updates" disabled={Boolean(savingKey)} onClick={() => updatePreference('product_updates')}><span /></button></div>
      {saved && <p className="settings-success" role="status">Notification preferences saved.</p>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <small className="notification-note">Preferences are saved to your account. Email delivery is not enabled in this version.</small>
    </section>
  </div>
}

function PageTitle({ eyebrow, title, description, action, navigate }) {
  return <div className="page-title-row"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <button className="button button-dark" onClick={() => navigate('/app/overview')}><Plus size={16} />{action}</button>}</div>
}

function MetricCard({ icon: Icon, label, value, note, className = '' }) {
  return <div className={`metric-card ${className}`}><div className="metric-icon"><Icon size={17} /></div><span className="metric-label">{label}</span><strong>{value}</strong><small>{note}</small></div>
}

function PolicySummaryCard({ policy }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [language, setLanguage] = useState('English')
  const [speaking, setSpeaking] = useState(false)
  const audioRef = useRef(null)

  const LANGUAGE_MAP = {
    'English': 'en-IN', 'Hindi': 'hi-IN', 'Marathi': 'mr-IN',
    'Bengali': 'bn-IN', 'Tamil': 'ta-IN', 'Telugu': 'te-IN',
    'Kannada': 'kn-IN', 'Gujarati': 'gu-IN',
  }

  const loadSummary = async (lang) => {
    if (!policy) return
    setLoading(true); setError(''); setSummary(null)
    try {
      const result = await getPolicySummary(policy.id, lang)
      setSummary(result.summary)
    } catch { setError('Could not generate summary. Please try again.') }
    finally { setLoading(false) }
  }

  const speakSummary = async () => {
    if (!summary || speaking) return
    setSpeaking(true)
    const langCode = LANGUAGE_MAP[language] || 'en-IN'
    try {
      const result = await getSarvamTTS(policy.id, summary, langCode)
      if (result.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${result.audio_base64}`)
        audioRef.current = audio
        audio.onended = () => setSpeaking(false)
        audio.onerror = () => setSpeaking(false)
        await audio.play(); return
      }
    } catch { /* fall through */ }
    if ('speechSynthesis' in window) {
      const utt = new SpeechSynthesisUtterance(summary)
      utt.onend = () => setSpeaking(false)
      utt.onerror = () => setSpeaking(false)
      window.speechSynthesis.speak(utt)
    } else { setSpeaking(false) }
  }

  const stopSpeaking = () => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null }
    window.speechSynthesis?.cancel()
    setSpeaking(false)
  }

  if (!policy) return null
  const bullets = summary ? summary.split(/\n+/).filter(Boolean) : []

  return (
    <section className="dashboard-card policy-summary-card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">POLICY INTELLIGENCE · AI SUMMARY</span>
          <h2>Critical points summary.</h2>
        </div>
        <div className="summary-controls">
          <div className="language-picker">
            <Languages size={15} />
            <select value={language} onChange={e => { setLanguage(e.target.value); setSummary(null) }} aria-label="Summary language">
              {Object.keys(LANGUAGE_MAP).map(l => <option key={l}>{l}</option>)}
            </select>
            <ChevronDown size={13} />
          </div>
          <button className="button button-outline button-small" onClick={() => loadSummary(language)} disabled={loading}>
            {loading ? <><span className="processing-spinner" aria-hidden="true" /> Summarizing…</> : <><Sparkles size={14} /> Generate summary</>}
          </button>
        </div>
      </div>
      {!summary && !loading && !error && (
        <div className="summary-empty">
          <FileText size={22} />
          <p>Get a plain-language summary of your policy's critical points — coverage, exclusions, obligations, and red flags.</p>
        </div>
      )}
      {loading && (
        <div className="summary-loading" role="status" aria-live="polite">
          <div className="summary-loading-bar"><span /></div>
          <p>Reading your policy and extracting key points in {language}…</p>
        </div>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
      {summary && (
        <div className="summary-content">
          <div className="summary-text">
            {bullets.map((line, i) => <div key={i} className="summary-bullet">{line}</div>)}
          </div>
          <div className="summary-voice-row">
            <span className="summary-voice-label"><AudioLines size={14} /> Read aloud in {language} via Sarvam AI</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {speaking
                ? <button className="button button-outline button-small voice-stop-btn" onClick={stopSpeaking}><X size={14} /> Stop</button>
                : <button className="button button-dark button-small" onClick={speakSummary}><AudioLines size={14} /> Listen</button>}
              <button className="button button-outline button-small" onClick={() => loadSummary(language)} disabled={loading}><Sparkles size={13} /> Refresh</button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}

function OverviewPage({ account, policies, navigate, openUpload, onOpenPolicy, onAskPolicy }) {
  const readyPolicies = policies.filter((policy) => policy.status === 'ready')
  const processingPolicies = policies.filter((policy) => policy.status === 'processing')
  const failedPolicies = policies.filter((policy) => policy.status === 'failed')
  const extractedDetails = policies.reduce((total, policy) => total + (policy.analysis?.pages || []).reduce(
    (pageTotal, page) => pageTotal + (page.extracted_points || []).length,
    0,
  ), 0)
  const firstName = account.name.trim().split(/\s+/)[0]
  const greeting = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening'
  const dateLabel = new Date().toLocaleDateString('en-IN', { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()
  const firstPolicy = policies[0]

  return <div className="page">
    <div className="welcome-strip"><div><span className="welcome-date">{dateLabel}</span><h1>{greeting}, {firstName} <span>✳</span></h1><p>{policies.length ? 'Your policy workspace is up to date.' : 'Add your first policy to get started.'}</p></div><div className="welcome-art" aria-hidden="true"><span className="welcome-sun" /><span className="welcome-leaf leaf-one" /><span className="welcome-leaf leaf-two" /><span className="welcome-stem" /></div></div>
    <div className="overview-metrics">
      <MetricCard icon={FileText} label="POLICIES ADDED" value={policies.length} note="In your private workspace" className="metric-mint" />
      <MetricCard icon={BadgeCheck} label="ANALYSIS READY" value={readyPolicies.length} note="Ready to read and ask about" className="metric-lilac" />
      <MetricCard icon={Clock3} label="PROCESSING" value={processingPolicies.length} note="Documents being analyzed" className="metric-peach" />
      <MetricCard icon={CircleHelp} label="NEEDS ATTENTION" value={failedPolicies.length} note="Documents that could not be analyzed" className="metric-yellow" />
    </div>
    <div className="dashboard-grid">
      <section className="dashboard-card policy-overview-card">
        <div className="card-heading"><div><span className="eyebrow">YOUR POLICY LIBRARY</span><h2>{firstPolicy ? 'Your latest policy.' : 'Start with your first policy.'}</h2></div><button className="button button-outline button-small" onClick={() => navigate('/app/policies')}>View all</button></div>
        {firstPolicy ? <div className="policy-summary">
          <div className="policy-cover"><div className="cover-emblem"><Shield size={25} /></div><span>PRIVATE<br />DOCUMENT</span><span className="cover-lines">— — — —</span></div>
          <div className="policy-summary-info"><div className="insurer-label"><span className="insurer-dot" /> Private policy document</div><h3>{firstPolicy.filename}</h3><p>Added {new Date(firstPolicy.uploaded_at).toLocaleDateString()}</p><div className="policy-tags"><span>{firstPolicy.status === 'ready' ? <CheckCircle2 size={12} /> : firstPolicy.status === 'processing' ? <span className="processing-spinner" /> : <Clock3 size={12} />} {firstPolicy.status === 'processing' ? 'Analyzing…' : firstPolicy.status}</span><span>{extractedDetails} details found</span></div><div className="policy-summary-actions"><button className="button button-dark button-small" disabled={firstPolicy.status !== 'ready'} onClick={() => firstPolicy.status === 'ready' ? onOpenPolicy(firstPolicy.id) : navigate('/app/policies')} title={firstPolicy.status !== 'ready' ? 'Analysis not ready yet — click to view policy library' : ''}>Open policy <ArrowRight size={14} /></button><button className="button button-outline button-small" disabled={firstPolicy.status !== 'ready'} onClick={() => firstPolicy.status === 'ready' ? onAskPolicy(firstPolicy.id) : navigate('/app/policies')} title={firstPolicy.status !== 'ready' ? 'Analysis not ready yet — click to view policy library' : ''}><MessageCircle size={14} /> Ask a question</button></div></div>
        </div> : <div className="overview-empty"><p>Your policies will appear here after upload.</p><button className="button button-dark button-small" onClick={openUpload}><Upload size={14} /> Add a policy</button></div>}
      </section>
      <section className="dashboard-card next-step-card">
        <div className="card-heading"><div><span className="eyebrow">WORKSPACE STATUS</span><h2>{policies.length ? 'Your documents, at a glance.' : 'Your next step is simple.'}</h2></div><span className="next-step-icon"><ListChecks size={17} /></span></div>
        <p>{policies.length ? 'Analysis runs securely on each policy you add.' : 'Upload a policy PDF to start document analysis and ask source-grounded questions.'}</p>
        <div className="next-step-list"><div><span className="todo-check"><Check size={12} /></span><span><b>{readyPolicies.length} ready to explore</b><small>Documents with completed analysis</small></span><ChevronRight size={15} /></div><div><span className={failedPolicies.length ? 'todo-dot todo-dot-warning' : 'todo-dot'} /><span><b>{processingPolicies.length} processing · {failedPolicies.length} need attention</b><small>Check your policy library for details</small></span><ChevronRight size={15} /></div></div>
        <button className="text-button" onClick={() => navigate('/app/policies')}>View policy library <ArrowRight size={14} /></button>
      </section>
      <section className="dashboard-card ask-prompt-card">
        <div className="ask-prompt-icon"><Sparkles size={17} /></div><div><span className="eyebrow">POLICY COMPANION</span><h2>Have a policy question?</h2><p>Get a source-grounded answer from one of your analyzed policies.</p></div>
        <button className="button button-dark button-small" onClick={() => readyPolicies.length ? onAskPolicy(readyPolicies[0].id) : navigate('/app/policies')}>Ask your policy <ArrowRight size={14} /></button>
        <div className="prompt-suggestions"><span>{readyPolicies.length ? 'Ready to help' : 'Add and analyze a policy first'}</span></div>
      </section>
      <section className="dashboard-card trust-note-card">
        <div className="trust-note-icon"><ShieldCheck size={17} /></div><div><b>Grounded in your document</b><p>Policy answers show where the information came from. If a detail isn’t clear, BimaLens will say so.</p></div><AppLink to="/app/policies" onNavigate={navigate} aria-label="View your policies"><ArrowUpRight size={16} /></AppLink>
      </section>
    </div>
    <PolicySummaryCard policy={firstPolicy || null} />
  </div>
}

function PoliciesPage({ policies, policyError, onOpenPolicy, onAskPolicy, openUpload }) {
  const [query, setQuery] = useState('')
  const matches = policies.filter((policy) => policy.filename.toLowerCase().includes(query.toLowerCase()))
  return <div className="page">
    <PageTitle eyebrow="YOUR DOCUMENT LIBRARY" title="My policies" description="Your policy documents, with the details that matter made easier to find." />
    <div className="library-toolbar"><div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search policies" aria-label="Search policies" /><kbd>⌘ K</kbd></div><button className="button button-dark" onClick={openUpload}><Upload size={15} /> Add a policy</button></div>
    <div className="library-caption"><span>{policies.length} {policies.length === 1 ? 'POLICY' : 'POLICIES'}</span><span>Recently added</span></div>
    {policyError && <p className="form-error" role="alert">{policyError}</p>}
    {matches.length ? matches.map((policy) => {
      const ready = policy.status === 'ready'
      const failed = policy.status === 'failed'
      const processing = policy.status === 'processing'
      return <div className={`policy-library-card${processing ? ' policy-card-processing' : ''}`} key={policy.id}>
        <div className="library-document-art"><div className="library-paper"><span>PDF</span><i /><i /><i /><i /></div><div className="library-art-spark">✳</div></div>
        <div className="library-card-content">
          <div className="library-status"><span className={`${failed ? 'policy-status-failed' : ''} ${processing ? 'policy-status-processing' : ''}`}>{processing ? <span className="processing-spinner" /> : ready ? <CheckCircle2 size={13} /> : <Clock3 size={13} />}{ready ? 'Analysis ready' : failed ? 'Analysis failed' : 'Analyzing policy…'}</span><span>{new Date(policy.uploaded_at).toLocaleDateString()}</span></div>
          <div className="insurer-label"><span className="insurer-dot" /> Private policy document</div>
          <h2>{policy.filename}</h2>
          <p>Uploaded document · {policy.status}</p>
          {failed && policy.error && <p className="policy-error-text">{policy.error}</p>}
          {processing && <div className="processing-bar"><span /></div>}
          <div className="library-card-tags"><span><FileText size={13} /> PDF document</span><span>{ready ? <><Sparkles size={13} /> Analysis complete</> : failed ? 'Needs attention' : <><span className="processing-spinner" /> Analysis in progress</>}</span></div>
          <div className="library-card-footer"><small><LockKeyhole size={12} /> Stored in your private workspace</small><div><button className="button button-outline button-small" disabled={!ready} onClick={() => onAskPolicy(policy.id)}><MessageCircle size={13} /> Ask</button><button className="button button-dark button-small" disabled={!ready} onClick={() => onOpenPolicy(policy.id)}>{ready ? 'Open policy' : failed ? 'Unavailable' : 'Processing…'} {ready && <ArrowRight size={14} />}</button></div></div>
        </div>
      </div>
    }) : <div className="empty-state"><FileSearch2 size={24} /><h3>{policies.length ? 'No matching policies' : 'No policies yet'}</h3><p>{policies.length ? 'Try another search term.' : 'Add a policy PDF to begin analysis in your private workspace.'}</p>{!policies.length && <button className="button button-dark button-small" onClick={openUpload}><Upload size={14} /> Add a policy</button>}</div>}
    {policies.length > 0 && <div className="upload-banner"><div className="upload-banner-icon"><FilePlus2 size={19} /></div><div><b>Have another policy to understand?</b><p>Upload a PDF and track its analysis here.</p></div><button className="button button-outline button-small" onClick={openUpload}>Add a policy <Plus size={14} /></button></div>}
  </div>
}

function UploadedPolicyReader({ policyId, navigate }) {
  const [policy, setPolicy] = useState(null)
  const [pdfUrl, setPdfUrl] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([getPolicy(policyId), getPolicyPdfLink(policyId)])
      .then(([document, link]) => {
        if (!active) return
        setPolicy(document)
        setPdfUrl(link.url)
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'The policy document could not be opened.')
      })
    return () => { active = false }
  }, [policyId])

  return <div className="page reader-page">
    <div className="reader-heading"><button className="back-link" onClick={() => navigate('/app/policies')}><ArrowLeft size={15} /> My policies</button><div className="reader-title-line"><div><span className="eyebrow">YOUR POLICY DOCUMENT</span><h1>{policy?.filename || 'Loading policy…'}</h1></div><span className="uploaded-policy-status">{policy?.status || 'Loading'}</span></div></div>
    {error ? <div className="empty-state"><FileSearch2 size={24} /><h3>Could not open this policy</h3><p>{error}</p></div> : pdfUrl ? <div className="uploaded-pdf-viewer"><iframe title={`Policy document: ${policy?.filename || ''}`} src={pdfUrl} /></div> : <div className="empty-state"><Clock3 size={24} /><h3>Opening your policy</h3><p>Loading the secure document link…</p></div>}
  </div>
}

function ReaderPage({ navigate, policyId }) {
  const [page, setPage] = useState(1)
  const [activeFact, setActiveFact] = useState(0)
  const highlightedFact = facts[activeFact]
  if (policyId) return <UploadedPolicyReader key={policyId} policyId={policyId} navigate={navigate} />
  return <div className="page reader-page">
    <div className="reader-heading"><button className="back-link" onClick={() => navigate('/app/policies')}><ArrowLeft size={15} /> My policies</button><div className="reader-title-line"><div><span className="eyebrow">POLICY READER · {POLICY.uin}</span><h1>{POLICY.name}</h1></div><button className="button button-outline button-small" onClick={() => navigate('/app/ask')}><MessageCircle size={14} /> Ask about this policy</button></div></div>
    <div className="reader-layout">
      <section className="document-viewer">
        <div className="document-toolbar"><div className="document-file"><FileText size={15} /><span>{POLICY.name}.pdf</span><span className="file-badge">SAMPLE</span></div><div className="document-tools"><button aria-label="Previous page" onClick={() => setPage((value) => Math.max(1, value - 1))}><ChevronLeft size={16} /></button><span>Page <b>{page}</b> of {POLICY.pages}</span><button aria-label="Next page" onClick={() => setPage((value) => Math.min(POLICY.pages, value + 1))}><ChevronRight size={16} /></button><i /><button aria-label="Download document"><ArrowDown size={15} /></button></div></div>
        <div className="document-canvas"><div className="document-page">
          <div className="doc-brand"><span className="doc-emblem">LIC</span><div><small>LIFE INSURANCE CORPORATION OF INDIA</small><b>{POLICY.name}</b></div><span className="doc-page-count">PAGE {page}</span></div>
          <div className="doc-title"><b>{page === 1 ? 'PART - A' : page === 2 ? 'IMPORTANT INFORMATION' : 'POLICY TERMS'}</b><span>UIN: {POLICY.uin}</span></div>
          <div className="doc-line doc-line-long" /><div className="doc-line" /><div className="doc-line doc-line-short" />
          <h3>{page === 1 ? 'Free Look Period' : page === 2 ? 'Existence Certificate' : 'Annuity Contract'}</h3>
          {page === 1 ? <>
            <p>We would request you to go through the terms and conditions of the Policy and in case you disagree with any of the terms and conditions, you may return the Policy within a period of <span className="doc-highlight">15 days (30 days if this policy is purchased online)</span> from the date of receipt of Policy Document stating the reasons of your objections and disagreement.</p>
            <p>On receipt of the policy, we shall cancel the same and the amount of premium deposited by you shall be refunded to you after deducting the charges for stamp duty and Annuity paid (if any).</p>
          </> : page === 2 ? <>
            <p>The <span className="doc-highlight">Existence Certificate must be submitted by the Annuitant / Primary Annuitant / Secondary Annuitant (as applicable)</span> in the prescribed format as and when required by the Corporation.</p>
            <p>The Annuity payments shall be released only on receipt of the Existence Certificate. Please refer to the full policy wording for the conditions and process.</p>
          </> : <>
            <p>This policy document contains the terms and conditions for LIC’s New Jeevan Shanti deferred annuity plan. Review the complete document for applicable benefits, options, and requirements.</p>
            <p>This preview recreates only selected sample text. Refer to the original policy wording for all terms and conditions.</p>
          </>}
          <div className="doc-line doc-line-long" /><div className="doc-line" /><div className="doc-line doc-line-short" />
          <div className="doc-page-footer">LIC’S NEW JEEVAN SHANTI <span>•</span> {page}</div>
        </div></div>
        <div className="document-pagination"><span>Showing selected policy text for this product demo</span><div><button onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={page === 1}>Previous</button><button onClick={() => setPage((value) => Math.min(POLICY.pages, value + 1))}>Next page <ChevronRight size={13} /></button></div></div>
      </section>
      <aside className="reader-aside">
        <div className="reader-aside-heading"><div><span className="eyebrow">BIMALENS FOUND</span><h2>Key details</h2></div><span className="detail-count">03</span></div>
        <p className="reader-aside-intro">Tap a detail to see its source in the policy preview.</p>
        <div className="detail-list">{facts.map((fact, index) => <button key={fact.label} className={`detail-card ${activeFact === index ? 'detail-active' : ''}`} onClick={() => { setActiveFact(index); setPage(index === 0 ? 1 : 2) }}><span className={`detail-icon ${fact.tone}`}>{index === 0 ? <Clock3 size={15} /> : index === 1 ? <FileCheck2 size={15} /> : <HeartHandshake size={15} />}</span><span className="detail-copy"><b>{fact.label}</b><strong>{fact.value}</strong><small>{fact.detail}</small><span className="detail-source"><BookOpen size={11} /> {fact.page} <ChevronRight size={11} /></span></span><ChevronRight size={15} className="detail-arrow" /></button>)}</div>
        <div className="reader-ask-box"><div className="reader-ask-icon"><Sparkles size={15} /></div><div><b>Need another detail?</b><p>Ask a question about this policy and check the cited page.</p></div><button onClick={() => navigate('/app/ask')}>Ask Bima <ArrowRight size={14} /></button></div>
        <div className="reader-notice"><ShieldCheck size={14} /><span>Explanations are based on the displayed sample text. Please verify terms in your complete policy.</span></div>
      </aside>
    </div>
  </div>
}

function AskPage({ navigate, policy }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [language, setLanguage] = useState('English')
  const [recording, setRecording] = useState(false)
  const [sending, setSending] = useState(false)
  const [requestError, setRequestError] = useState('')
  useEffect(() => {
    setMessages(policy ? [{ role: 'assistant', text: `Ask me about ${policy.filename}. I’ll use the policy analysis to answer and cite its source.`, source: null }] : [])
  }, [policy?.id])

  const sendQuestion = async (value) => {
    const trimmed = value.trim()
    if (!trimmed || sending) return
    setRequestError('')
    setMessages((current) => [...current, { role: 'user', text: trimmed }])
    setQuestion('')
    setRecording(false)
    if (!policy) return
    setSending(true)
    try {
      const result = await askQuestion(policy.id, trimmed, language)
      setMessages((current) => [...current, {
        role: 'assistant',
        text: result.answer,
        source: result.sources?.map((source) => `Page ${source.page}${source.section ? ` · ${source.section}` : ''}`).join(', ') || null,
      }])
    } catch (error) {
      setRequestError(error.response?.data?.detail || 'Your question could not be answered. Please try again.')
    } finally {
      setSending(false)
    }
  }
  if (!policy) return <div className="page"><PageTitle eyebrow="YOUR POLICY, ON YOUR TERMS" title="Ask your policy" description="Upload and analyze a policy before asking document-grounded questions." /><div className="empty-state"><MessageCircle size={24} /><h3>No analyzed policy selected</h3><p>Choose a ready policy from your library to ask questions about its wording.</p><button className="button button-dark button-small" onClick={() => navigate('/app/policies')}>Open policy library <ArrowRight size={14} /></button></div></div>
  return <div className="page ask-page">
    <div className="ask-page-header"><div><div className="eyebrow">YOUR POLICY, ON YOUR TERMS</div><h1>Ask your policy</h1><p>Simple answers, grounded in your document. No guesswork.</p></div><div className="language-picker"><Languages size={15} /><select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label="Answer language"><option>English</option><option>Hindi</option><option>Marathi</option><option>Bengali</option><option>Tamil</option><option>Telugu</option><option>Kannada</option><option>Gujarati</option></select><ChevronDown size={13} /></div></div>
    <div className="chat-layout">
      <section className="chat-panel">
        <div className="chat-policy-bar"><div className="chat-policy-icon"><FileText size={16} /></div><div><b>{policy?.filename || POLICY.name}</b><small>{policy ? 'Your uploaded policy' : `${POLICY.kind} · ${POLICY.pages} pages`}</small></div><span className="chat-rag-badge"><Sparkles size={9} /> RAG</span><span className="chat-ready"><span /> {policy?.status?.toUpperCase() || 'READY'}</span></div>
        <div className="chat-messages">
          <div className="chat-day-divider"><span>TODAY</span></div>
          {messages.map((message, index) => <div key={`${message.role}-${index}`} className={`chat-message ${message.role === 'user' ? 'message-user' : ''}`}><div className={`chat-avatar ${message.role === 'user' ? 'user-chat-avatar' : ''}`}>{message.role === 'user' ? 'You' : <span className="brand-mark"><span /><span /><span /></span>}</div><div className="chat-message-content"><div className="chat-message-meta"><b>{message.role === 'user' ? 'You' : 'Bima'}</b><span>{message.role === 'user' ? '10:42 AM' : 'Just now'}</span></div><p>{message.text}</p>{message.source && <button className="source-chip" onClick={() => navigate('/app/reader')}><BookOpen size={13} /> {message.source} <ArrowUpRight size={12} /></button>}</div></div>)}
          {sending && <div className="recording-state" role="status"><span className="processing-spinner" />Checking your policy for an answer…</div>}
          {requestError && <p className="form-error chat-request-error" role="alert">{requestError}</p>}
          {recording && <div className="recording-state"><AudioLines size={17} /> Listening for your question… <button onClick={() => setRecording(false)}>Cancel</button></div>}
        </div>
        <div className="chat-input-area"><div className="suggestion-row"><span>TRY ASKING</span><button onClick={() => sendQuestion('What is covered under this policy?')}>What is covered?</button><button onClick={() => sendQuestion('What are the exclusions in this policy?')}>What is excluded?</button><button onClick={() => sendQuestion('How do I make a claim?')}>How to claim?</button></div><form className="chat-input" onSubmit={(event) => { event.preventDefault(); sendQuestion(question) }}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={`Ask anything about ${policy?.filename || POLICY.name}...`} aria-label="Ask your policy" disabled={sending} /><button type="button" className={`voice-button ${recording ? 'voice-active' : ''}`} aria-label="Voice input" onClick={() => setRecording((value) => !value)}><AudioLines size={17} /></button><button className="send-button" type="submit" aria-label="Send question" disabled={sending}><Send size={16} /></button></form><div className="chat-privacy-note"><LockKeyhole size={11} /> {policy ? 'Answers grounded in your policy document via RAG (SQLite) · Sources cited per response.' : 'Answers are grounded in the sample policy · This demo doesn’t send data to a service'}</div></div>
      </section>
      <aside className="chat-context">
        <div className="context-card"><div className="context-heading"><span className="eyebrow">POLICY CONTEXT</span></div><div className="context-doc-icon"><FileText size={19} /></div><h3>{policy?.filename || POLICY.name}</h3><p>{policy ? 'Your private policy document' : POLICY.insurer}</p><div className="context-divider" /><div className="context-row"><span>Plan type</span><b>{policy ? 'Uploaded PDF' : POLICY.kind}</b></div><div className="context-row"><span>Policy UIN</span><b>{policy ? 'From document analysis' : POLICY.uin}</b></div><div className="context-row"><span>Document</span><b>{policy?.status || `${POLICY.pages} pages`}</b></div><button className="context-open" onClick={() => navigate('/app/reader')}>Open policy <ArrowRight size={14} /></button></div>
        <div className="grounding-card"><div><ShieldCheck size={16} /><b>Grounded answers</b></div><p>Answers reference the analyzed policy. When the source does not support a clear answer, BimaLens should say so rather than guess.</p><AppLink to="/app/reader" onNavigate={navigate}>See how citations work <ArrowRight size={13} /></AppLink></div>
        <div className="language-note"><Languages size={15} /><span>Choose your answer language above. 8 Indian languages supported via Sarvam AI.</span></div>
      </aside>
    </div>
  </div>
}

function FitPage({ navigate, policy }) {
  const [age, setAge] = useState('')
  const [goal, setGoal] = useState('')
  const [dependents, setDependents] = useState('0')
  const [saved, setSaved] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const saveContext = async () => {
    setError('')
    setResult(null)
    if (!policy) {
      setError('Add and analyze a policy before checking its fit.')
      return
    }
    if (!goal) {
      setError('Choose a priority before continuing.')
      return
    }
    setLoading(true)
    try {
      const analysis = await assessPolicyFit(policy.id, {
        age: age ? Number(age) : undefined,
        dependents: Number(dependents),
        goal,
      })
      setResult(analysis)
      setSaved(true)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not compare your context with this policy.')
    } finally {
      setLoading(false)
    }
  }
  return <div className="page">
    <PageTitle eyebrow="UNDERSTAND THE FIT" title="Coverage fit" description="See how the policy you have connects to what matters to you." />
    <div className="fit-intro"><div className="fit-intro-mark"><ShieldCheck size={20} /></div><div><b>A thoughtful fit starts with your goals.</b><p>Your answers are compared with the analysis of your selected policy. This is not a financial recommendation.</p></div><span className="fit-preview-tag">{policy ? 'POLICY LINKED' : 'NO POLICY'}</span></div>
    <div className="fit-grid">
      <section className="dashboard-card fit-profile-card"><div className="card-heading"><div><span className="eyebrow">YOUR CONTEXT</span><h2>What are you planning for?</h2></div><span className="profile-step">01 / 02</span></div><p className="fit-form-copy">A little context helps make a policy review more relevant. All fields are optional.</p>
        <label className="form-label">What matters most to you?<select value={goal} onChange={(event) => { setGoal(event.target.value); setSaved(false); setResult(null) }}><option value="">Choose a priority</option><option>Retirement income</option><option>Family protection</option><option>Health expenses</option><option>Understanding this policy</option></select><ChevronDown size={14} /></label>
        <div className="form-two-col"><label className="form-label">Your age <div className="input-suffix"><input type="number" min="18" max="120" value={age} onChange={(event) => { setAge(event.target.value); setSaved(false); setResult(null) }} placeholder="e.g. 35" /><span>years</span></div></label><label className="form-label">People who depend on you<select value={dependents} onChange={(event) => { setDependents(event.target.value); setSaved(false); setResult(null) }}><option value="0">Just me</option><option value="1">1 person</option><option value="2">2 people</option><option value="3">3 or more</option></select><ChevronDown size={14} /></label></div>
        <button className="button button-dark" onClick={saveContext} disabled={loading || !policy}><Sparkles size={15} /> {loading ? 'Reviewing policy…' : saved ? 'Review again' : 'Compare with policy'} {saved && !loading && <Check size={14} />}</button>
        {error && <p className="form-error fit-result-error" role="alert">{error}</p>}
        {result && <div className="fit-result"><b>Policy-grounded comparison</b><p>{result.summary}</p>{result.observations?.map((observation, index) => <small key={`${observation.page}-${index}`}><BookOpen size={12} /> Page {observation.page}{observation.section ? ` · ${observation.section}` : ''}: “{observation.quote}”</small>)}</div>}
      </section>
      <section className="dashboard-card fit-policy-card"><span className="eyebrow">SELECTED POLICY</span><div className="fit-policy-header"><div className="fit-policy-icon"><FileText size={18} /></div><span className="fit-policy-status"><span /> {policy?.status?.toUpperCase() || 'NOT SELECTED'}</span></div><h2>{policy?.filename || 'No analyzed policy selected'}</h2><p>{policy ? `Uploaded ${new Date(policy.uploaded_at).toLocaleDateString()}` : 'Upload a policy PDF to compare it with your context.'}</p><div className="fit-type-row"><span>Analysis status</span><b>{policy?.status || 'Not available'}</b></div><div className="fit-policy-note"><Lightbulb size={14} /><span>This comparison is a document-grounded summary only. Confirm all coverage details with the insurer.</span></div><button className="text-button" onClick={() => navigate(policy ? '/app/reader' : '/app/policies')}>{policy ? 'Review policy document' : 'Browse policies'} <ArrowRight size={14} /></button></section>
    </div>
    <div className="fit-disclaimer"><ShieldCheck size={16} /><span><b>A clearer view, not a financial recommendation.</b> This comparison does not calculate a suitability score or suggest insurance products. Always confirm details with your insurer or a qualified adviser.</span></div>
  </div>
}

function UploadedClaimsPage({ navigate, policy }) {
  const [checklist, setChecklist] = useState(null)
  const [checked, setChecked] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getClaimChecklist(policy.id)
      .then((result) => {
        if (!active) return
        setChecklist(result)
        setChecked(result.items.map(() => false))
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'Could not load the policy claim checklist.')
      })
    return () => { active = false }
  }, [policy.id])

  const count = checked.filter(Boolean).length
  const items = checklist?.items || []
  const toggle = (index) => setChecked((current) => current.map((value, itemIndex) => itemIndex === index ? !value : value))

  return <div className="page claims-page">
    <PageTitle eyebrow="ONE STEP AT A TIME" title="Claim companion" description={`Checklist details extracted from ${policy.filename}.`} />
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="claims-progress-card"><div className="claims-progress-top"><div><span className="eyebrow">YOUR CHECKLIST</span><h2>Policy claim details</h2><p>Items are summarized from the analyzed policy. Check them off for your own tracking.</p></div><div className="progress-ring" style={{ '--progress': `${items.length ? Math.round((count / items.length) * 100) : 0}%` }}><span>{count}<small>/{items.length}</small></span></div></div><div className="progress-track"><span style={{ width: `${items.length ? (count / items.length) * 100 : 0}%` }} /></div><span className="progress-caption">{count} of {items.length} items marked done</span></div>
    <section className="dashboard-card checklist-card">
      <div className="card-heading"><div><span className="eyebrow">EXTRACTED FROM YOUR POLICY</span><h2>Important clauses and steps</h2></div><span className="list-count">{items.length}</span></div>
      {items.length ? <div className="checklist-items">{items.map((item, index) => <button key={`${item.page}-${item.section}-${index}`} className={`checklist-item ${checked[index] ? 'checklist-done' : ''}`} onClick={() => toggle(index)} aria-pressed={checked[index]}><span className="checklist-box">{checked[index] && <Check size={13} />}</span><span><b>{item.section || `Policy detail ${index + 1}`}</b><small>{item.quote}</small><span className="checklist-source"><BookOpen size={11} /> Page {item.page} · {item.category}</span></span><ChevronRight size={14} /></button>)}</div> : !error && <div className="empty-state"><FileSearch2 size={22} /><h3>No claim details were extracted</h3><p>The policy analysis did not identify checklist items.</p></div>}
      {checklist?.disclaimer && <p className="claim-caution"><ShieldCheck size={14} /> {checklist.disclaimer}</p>}
      <button className="button button-outline button-small" onClick={() => navigate('/app/reader')}>Open policy document <ArrowRight size={14} /></button>
    </section>
  </div>
}

function ClaimsPage({ navigate, policy }) {
  if (policy) return <UploadedClaimsPage navigate={navigate} policy={policy} />
  return <div className="page"><PageTitle eyebrow="ONE STEP AT A TIME" title="Claim companion" description="Review claim-related details extracted from your analyzed policy." /><div className="empty-state"><ClipboardCheck size={24} /><h3>No analyzed policy selected</h3><p>Choose a ready policy to see relevant checklist items from its document.</p><button className="button button-dark button-small" onClick={() => navigate('/app/policies')}>Open policy library <ArrowRight size={14} /></button></div></div>
}

function UploadModal({ onClose, navigate, onUploaded }) {
  const [file, setFile] = useState(null)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    if (!file) return
    setSubmitting(true)
    setError('')
    try {
      await uploadPolicy(file, setProgress)
      await onUploaded()
      onClose()
      navigate('/app/policies')
    } catch (requestError) {
      const detail = requestError.response?.data?.detail
      let message = typeof detail === 'string' ? detail : detail?.message || 'The policy could not be uploaded. Please try again.'
      if (requestError.response?.status === 502) {
        try {
          await onUploaded()
        } catch {
          message += ' The policy list could not be refreshed.'
        }
      }
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !submitting) onClose() }}><section className="upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title"><button className="modal-close" onClick={onClose} aria-label="Close" disabled={submitting}><X size={18} /></button><span className="modal-icon"><Upload size={20} /></span><div className="eyebrow">ADD A POLICY</div><h2 id="upload-title">Bring your policy into focus.</h2><p>Upload a PDF to store it in your private workspace and start document analysis.</p><label className="drop-zone"><input type="file" accept="application/pdf,.pdf" disabled={submitting} onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError('') }} /><span className="drop-icon"><FilePlus2 size={20} /></span><b>{file?.name || 'Choose a policy PDF'}</b><small>{file ? 'Ready to upload securely' : 'PDF · Maximum file size 25 MB'}</small><span className="drop-browse">{file ? 'Choose another file' : 'Browse files'}</span></label><div className="upload-local-note"><LockKeyhole size={13} /> Your document is uploaded to your private workspace for analysis.</div>{submitting && <div className="upload-progress" role="status"><div className="processing-bar"><span /></div>Uploading… {progress}%</div>}{error && <div className="form-error" role="alert">{error}</div>}<button className="button button-dark modal-primary" disabled={!file || submitting} onClick={submit}>{submitting ? 'Uploading policy…' : 'Upload and analyze'} <ArrowRight size={15} /></button><button className="modal-cancel" onClick={onClose} disabled={submitting}>Cancel</button></section></div>
}

export default function App() {
  const [route, setRoute] = useState(routeFromHash)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [account, setAccount] = useState(null)
  const [policies, setPolicies] = useState([])
  const [policyError, setPolicyError] = useState('')
  const [selectedPolicyId, setSelectedPolicyId] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [sessionError, setSessionError] = useState('')
  const refreshPolicies = async () => {
    const currentPolicies = await getPolicies()
    setPolicies(currentPolicies)
    setPolicyError('')
  }
  const navigate = (path) => {
    if (path === '/') {
      window.history.pushState(null, '', `${window.location.pathname}${window.location.search}`)
      setRoute('/')
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }
    window.location.hash = path
    setRoute(path)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    const syncRoute = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', syncRoute)
    window.addEventListener('popstate', syncRoute)
    return () => {
      window.removeEventListener('hashchange', syncRoute)
      window.removeEventListener('popstate', syncRoute)
    }
  }, [])

  useEffect(() => {
    let active = true
    getCurrentAccount()
      .then((currentAccount) => {
        if (active) setAccount(currentAccount)
      })
      .catch((error) => {
        if (!active) return
        if (error.response?.status !== 401) {
          setSessionError(error.response?.data?.detail || 'BimaLens could not connect to the account service.')
        }
      })
      .finally(() => {
        if (active) setCheckingSession(false)
      })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!account) {
      setPolicies([])
      setPolicyError('')
      setSelectedPolicyId(null)
      return
    }
    let active = true
    getPolicies()
      .then((currentPolicies) => {
        if (active) {
          setPolicies(currentPolicies)
          setPolicyError('')
        }
      })
      .catch((error) => {
        if (active) setPolicyError(error.response?.data?.detail || 'Could not load your policies.')
      })
    return () => { active = false }
  }, [account?.id])

  useEffect(() => {
    if (!selectedPolicyId) {
      const firstReadyPolicy = policies.find((policy) => policy.status === 'ready')
      if (firstReadyPolicy) setSelectedPolicyId(firstReadyPolicy.id)
    }
  }, [policies, selectedPolicyId])

  useEffect(() => {
    if (!account) return
    const hasProcessing = policies.some(p => p.status === 'processing')
    if (!hasProcessing) return
    // Poll every 5s while processing; auto-stop after 5 minutes (60 attempts)
    let attempts = 0
    const interval = setInterval(async () => {
      attempts++
      try {
        const updated = await getPolicies()
        setPolicies(updated)
        const stillProcessing = updated.some(p => p.status === 'processing')
        if (!stillProcessing || attempts >= 60) clearInterval(interval)
      } catch { /* silent */ }
    }, 5000)
    return () => clearInterval(interval)
  }, [account, policies])

  useEffect(() => {
    document.body.classList.toggle('modal-open', uploadOpen)
    return () => document.body.classList.remove('modal-open')
  }, [uploadOpen])

  if (route === '/') return <LandingPage navigate={navigate} />
  if (route === '/login' || route === '/signup') {
    return <AuthPage mode={route.slice(1)} navigate={navigate} onAuthenticated={setAccount} />
  }
  if (checkingSession) return <main className="auth-page"><div className="auth-loading"><Brand /><p>Checking your private workspace…</p></div></main>
  if (!account) {
    return <AuthPage mode="login" navigate={navigate} onAuthenticated={setAccount} bootstrapError={sessionError} />
  }

  const handleSignOut = async () => {
    await signOut()
    setAccount(null)
    navigate('/login')
  }

  const activePolicy = policies.find((policy) => policy.id === selectedPolicyId && policy.status === 'ready')
    || policies.find((policy) => policy.status === 'ready')
  let page
  if (route === '/app/policies') page = <PoliciesPage policies={policies} policyError={policyError} onOpenPolicy={(id) => { setSelectedPolicyId(id); navigate('/app/reader') }} onAskPolicy={(id) => { setSelectedPolicyId(id); navigate('/app/ask') }} openUpload={() => setUploadOpen(true)} />
  else if (route === '/app/reader') page = <ReaderPage navigate={navigate} policyId={selectedPolicyId} />
  else if (route === '/app/ask') page = <AskPage navigate={navigate} policy={activePolicy} />
  else if (route === '/app/fit') page = <FitPage navigate={navigate} policy={activePolicy} />
  else if (route === '/app/claims') page = <ClaimsPage navigate={navigate} policy={activePolicy} />
  else if (route === '/app/account') page = <AccountPage account={account} onAccountChange={setAccount} onSignOut={handleSignOut} />
  else if (route === '/app/notifications') page = <NotificationsPage account={account} onAccountChange={setAccount} />
  else page = <OverviewPage account={account} policies={policies} navigate={navigate} openUpload={() => setUploadOpen(true)} onOpenPolicy={(id) => { setSelectedPolicyId(id); navigate('/app/reader') }} onAskPolicy={(id) => { setSelectedPolicyId(id); navigate('/app/ask') }} />

  return <AppShell route={route} navigate={navigate} account={account} policies={policies} onOpenPolicy={(id) => { setSelectedPolicyId(id); navigate('/app/reader') }}>
    {page}
    {uploadOpen && <UploadModal onClose={() => setUploadOpen(false)} navigate={navigate} onUploaded={refreshPolicies} />}
  </AppShell>
}
