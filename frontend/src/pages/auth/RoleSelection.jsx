import { useNavigate } from "react-router-dom";
import "./RoleSelection.css";

export default function RoleSelection() {
  const navigate = useNavigate();

  return (
    <div className="role-page">
      <aside className="role-sidebar">
        <div>
          <div className="role-brand">
            <div className="role-brand-mark">PL</div>
            <div>
              <h2>PolicyLens</h2>
              <p>Regulatory Intelligence</p>
            </div>
          </div>

          <div className="role-sidebar-line" />

          <div className="role-sidebar-label">WORKSPACE</div>

          <div className="role-side-item active">
            <span>◆</span>
            Access Portal
          </div>

          <div className="role-side-item">
            <span>▣</span>
            Policy Analysis
          </div>

          <div className="role-side-item">
            <span>◫</span>
            Evidence
          </div>
        </div>

        <div className="role-sidebar-footer">
          Secure enterprise workspace
        </div>
      </aside>

      <main className="role-main">
        <div className="role-content">
          <div className="role-eyebrow">SECURE WORKSPACE ACCESS</div>

          <h1>Select your workspace</h1>

          <p className="role-intro">
            Choose the workspace appropriate for your responsibilities.
            Different roles provide access to different policy intelligence
            capabilities.
          </p>

          <div className="role-cards">
            <button
              className="role-card"
              onClick={() => navigate("/dashboard")}
            >
              <div className="role-card-top">
                <div className="role-icon analyst">A</div>
                <span className="role-arrow">→</span>
              </div>

              <div className="role-card-label">STANDARD ACCESS</div>

              <h2>Policy Analyst</h2>

              <p>
                Investigate policy changes, compare versions, trace
                dependencies, and review evidence-grounded impact analysis.
              </p>

              <div className="role-permissions">
                <span>Policy comparison</span>
                <span>Impact analysis</span>
                <span>Evidence review</span>
              </div>
            </button>

            <button
              className="role-card"
              onClick={() => navigate("/admin")}
            >
              <div className="role-card-top">
                <div className="role-icon admin">M</div>
                <span className="role-arrow">→</span>
              </div>

              <div className="role-card-label">ELEVATED ACCESS</div>

              <h2>Administrator</h2>

              <p>
                Manage policy sources, versions, relationships, users,
                analysis scenarios, and system readiness.
              </p>

              <div className="role-permissions">
                <span>Policy management</span>
                <span>Relationship management</span>
                <span>System monitoring</span>
              </div>
            </button>
          </div>

          <div className="role-security">
            <div>
              <strong>Evidence-grounded</strong>
              <span>Analysis backed by source material</span>
            </div>

            <div>
              <strong>Traceable</strong>
              <span>Follow relationships and impact paths</span>
            </div>

            <div>
              <strong>Explainable</strong>
              <span>Understand why an impact was identified</span>
            </div>
          </div>

          <button
            className="role-back"
            onClick={() => navigate("/")}
          >
            ← Back to PolicyLens
          </button>
        </div>
      </main>
    </div>
  );
}