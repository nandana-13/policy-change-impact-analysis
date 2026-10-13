import { useNavigate } from "react-router-dom";
import "./PolicyLanding.css";

export default function PolicyLanding() {
  const navigate = useNavigate();

  return (
    <div className="landing-page">

      {/* TOP NAVIGATION */}
      <header className="landing-topbar">
        <div className="brand">
          <div className="brand-mark">PL</div>

          <div>
            <h2>PolicyLens</h2>
            <p>Regulatory Intelligence</p>
          </div>
        </div>

        <button
          className="landing-login-button"
          onClick={() => navigate("/login")}
        >
          Sign In
        </button>
      </header>


      {/* MAIN */}
      <main className="landing-main">

        {/* HERO */}
        <header className="landing-header">

          <div>
            <div className="eyebrow">
              ENTERPRISE POLICY INTELLIGENCE
            </div>

            <h1>
              Understand how policy changes
              <br />
              affect your organization.
            </h1>

            <p>
              PolicyLens analyzes regulatory changes, traces dependencies,
              identifies affected policies, and provides evidence-grounded
              explanations.
            </p>

            <div className="landing-actions">

              <button
                className="primary-button"
                onClick={() => navigate("/login")}
              >
                Enter Workspace
                <span>→</span>
              </button>

              <button
                className="secondary-button"
                onClick={() => navigate("/login")}
              >
                View Analysis
              </button>

            </div>
          </div>


          {/* STATUS */}
          <div className="landing-status-card">

            <div className="status-card-label">
              ANALYSIS ENGINE
            </div>

            <div className="status-card-main">
              <span className="large-status-dot" />
              Ready
            </div>

            <div className="status-card-meta">
              Evidence-grounded analysis
            </div>

          </div>

        </header>


        {/* METRICS */}
        <section className="landing-metrics">

          <div className="landing-metric">
            <span>POLICY DOCUMENTS</span>
            <strong>40</strong>
            <small>Regulatory corpus</small>
          </div>

          <div className="landing-metric">
            <span>POLICY VERSIONS</span>
            <strong>82</strong>
            <small>Tracked versions</small>
          </div>

          <div className="landing-metric">
            <span>RELATIONSHIPS</span>
            <strong>316</strong>
            <small>Cross-policy links</small>
          </div>

          <div className="landing-metric">
            <span>ANALYSIS RUNS</span>
            <strong>128</strong>
            <small>Completed analyses</small>
          </div>

        </section>


        {/* FEATURE GRID */}
        <section className="landing-section">

          <div className="section-heading">

            <div>
              <div className="eyebrow">
                CORE CAPABILITIES
              </div>

              <h2>
                From policy change to impact.
              </h2>
            </div>

            <p>
              A structured workflow for investigating regulatory change and
              cascading policy impact.
            </p>

          </div>


          <div className="feature-grid">

            <div className="feature-card">
              <div className="feature-number">01</div>

              <h3>
                Change Detection
              </h3>

              <p>
                Compare policy versions and identify clauses that have changed
                between releases.
              </p>
            </div>


            <div className="feature-card">
              <div className="feature-number">02</div>

              <h3>
                Dependency Analysis
              </h3>

              <p>
                Trace relationships between policies, clauses, procedures, and
                regulatory requirements.
              </p>
            </div>


            <div className="feature-card">
              <div className="feature-number">03</div>

              <h3>
                Impact Ranking
              </h3>

              <p>
                Rank affected policies according to the significance and
                propagation of the identified change.
              </p>
            </div>


            <div className="feature-card">
              <div className="feature-number">04</div>

              <h3>
                Explainable Evidence
              </h3>

              <p>
                Connect every finding to supporting regulatory evidence for
                transparent analysis.
              </p>
            </div>

          </div>

        </section>


        {/* FOOTER */}
        <footer className="landing-footer">
          PolicyLens · Enterprise Regulatory Intelligence Workspace
        </footer>

      </main>

    </div>
  );
}