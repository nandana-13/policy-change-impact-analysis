import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api/api";
import "./AdminDashboard.css";
/* =========================================================
   POLICYLENS ADMIN DASHBOARD
   ========================================================= */
export default function AdminDashboard() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState("overview");
  const [policies, setPolicies] = useState([]);
  const [regulatoryChanges, setRegulatoryChanges] = useState([]);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [versions, setVersions] = useState([]);
  const [dependencies, setDependencies] = useState([]);
  const [documents, setDocuments] = useState({});
  const [documentModal, setDocumentModal] = useState(null);
  const [documentLoading, setDocumentLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState("checking");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showPolicyForm, setShowPolicyForm] = useState(false);
  const [showVersionForm, setShowVersionForm] = useState(false);
  /*
   * This ref points to the actual Version History /
   * Policy Documents section.
   *
   * When the user clicks "View" on a policy,
   * we scroll here.
   */
  const versionHistoryRef = useRef(null);
  /* =========================================================
     LOAD POLICIES
     ========================================================= */
  const loadPolicies = async () => {
    try {
      setLoading(true);
      const response = await api.get("/policies");
      const policyList = Array.isArray(response.data) ? response.data : [];

      // Use real version records when the policy list does not include version_count.
      const policiesWithVersionCounts = await Promise.all(
        policyList.map(async (policy) => {
          if (Number.isFinite(Number(policy.version_count)) && policy.version_count !== null && policy.version_count !== "") {
            return { ...policy, version_count: Number(policy.version_count) };
          }

          try {
            const versionResponse = await api.get(`/policies/${policy.policy_id}/versions`);
            const policyVersions = Array.isArray(versionResponse.data) ? versionResponse.data : [];
            return { ...policy, version_count: policyVersions.length };
          } catch (versionError) {
            console.warn(`Could not load version count for ${policy.policy_id}:`, versionError);
            return { ...policy, version_count: null };
          }
        })
      );

      setPolicies(policiesWithVersionCounts);
    } catch (err) {
      console.error("Failed to load policies:", err);
      setError(
        err.response?.data?.detail ||
          "Failed to load policies."
      );
    } finally {
      setLoading(false);
    }
  };

  const checkSystemHealth = async () => {
    try {
      await api.get("/health");
      setSystemStatus("online");
    } catch (err) {
      console.warn("PolicyLens health check failed:", err);
      setSystemStatus("offline");
    }
  };
  /* =========================================================
     LOAD REGULATORY CHANGES
     ========================================================= */
  const loadRegulatoryChanges = async () => {
    try {
      const response = await api.get(
        "/regulatory-changes"
      );
      setRegulatoryChanges(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (err) {
      console.error(
        "Failed to load regulatory changes:",
        err
      );
    }
  };
  /* =========================================================
     LOAD DOCUMENTS
     ========================================================= */
  const loadDocumentsForVersions = async (
    policyId,
    versionList
  ) => {
    const nextDocuments = {};
    await Promise.all(
      versionList.map(async (version) => {
        try {
          const response = await api.get(
            `/policies/${policyId}/versions/${version.version_number}/document`
          );
          nextDocuments[
            version.version_number
          ] = response.data;
        } catch (err) {
          if (err.response?.status !== 404) {
            console.error(
              `Failed to load document for ${policyId} V${version.version_number}:`,
              err
            );
          }
          nextDocuments[
            version.version_number
          ] = null;
        }
      })
    );
    setDocuments(nextDocuments);
  };
  /* =========================================================
     SCROLL TO VERSION HISTORY
     ========================================================= */
  const scrollToVersionHistory = () => {
    /*
     * Small delay allows React to finish rendering the
     * selected policy and its versions before scrolling.
     */
    window.setTimeout(() => {
      if (versionHistoryRef.current) {
        versionHistoryRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }, 150);
  };
  /* =========================================================
     LOAD POLICY DATA
     ========================================================= */
  const loadPolicyData = async (
    policy,
    shouldScroll = false
  ) => {
    if (!policy?.policy_id) {
      return;
    }
    setSelectedPolicy(policy);
    setVersions([]);
    setDocuments({});
    setDependencies([]);
    setError("");
    try {
      const response = await api.get(
        `/policies/${policy.policy_id}/versions`
      );
      const loadedVersions =
        Array.isArray(response.data)
          ? response.data
          : [];
      setVersions(loadedVersions);
      await loadDocumentsForVersions(
        policy.policy_id,
        loadedVersions
      );
    } catch (err) {
      console.error(
        "Failed to load policy versions:",
        err
      );
      setVersions([]);
      setError(
        "Policy selected, but versions could not be loaded."
      );
    }
    try {
      const response = await api.get(
        `/policies/${policy.policy_id}/dependencies`
      );
      setDependencies(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (err) {
      console.error(
        "Failed to load dependencies:",
        err
      );
      setDependencies([]);
    }
    /*
     * IMPORTANT:
     * Scroll AFTER policy/version data has been loaded.
     */
    if (shouldScroll) {
      scrollToVersionHistory();
    }
  };
  /* =========================================================
     SELECT POLICY FROM POLICIES
     ========================================================= */
  const selectPolicyFromPolicies = async (policy) => {
    setActiveSection("policies");
    await loadPolicyData(policy, true);
  };
  /* =========================================================
     SELECT POLICY FROM VERSIONS
     ========================================================= */
  const selectPolicyFromVersions = async (policy) => {
    await loadPolicyData(policy, false);
  };
  /* =========================================================
     SELECT POLICY FROM RELATIONSHIPS
     ========================================================= */
  const selectPolicyFromRelationships = async (policy) => {
    await loadPolicyData(policy, false);
  };
  /* =========================================================
     DOCUMENT UPLOAD
     ========================================================= */
  const uploadDocument = async (
    policyId,
    versionNumber,
    file
  ) => {
    if (!file) {
      setError("Select a document first.");
      return;
    }
    try {
      setDocumentLoading(true);
      setError("");
      setMessage("");
      const formData = new FormData();
      formData.append("file", file);
      let response;
      let replacement = false;
      try {
        response = await api.post(
          `/policies/${policyId}/versions/${versionNumber}/document`,
          formData
        );
      } catch (postError) {
        /*
         * If the backend says a document already exists,
         * automatically use PUT so the user can still
         * complete the upload.
         */
        if (postError.response?.status === 409) {
          response = await api.put(
            `/policies/${policyId}/versions/${versionNumber}/document`,
            formData
          );
          replacement = true;
        } else {
          throw postError;
        }
      }
      setDocuments((current) => ({
        ...current,
        [versionNumber]: response.data,
      }));
      setDocumentModal(null);
      setMessage(
        replacement
          ? `Document replaced successfully for V${versionNumber}.`
          : `Document uploaded successfully for V${versionNumber}.`
      );
      await refreshPolicyDocuments(policyId);
    } catch (err) {
      console.error(
        "Failed to upload document:",
        err
      );
      setError(
        err.response?.data?.detail ||
          "Failed to upload policy document."
      );
    } finally {
      setDocumentLoading(false);
    }
  };
  /* =========================================================
     REPLACE DOCUMENT
     ========================================================= */
  const replaceDocument = async (
    policyId,
    versionNumber,
    file
  ) => {
    if (!file) {
      setError("Select a document first.");
      return;
    }
    try {
      setDocumentLoading(true);
      setError("");
      setMessage("");
      const formData = new FormData();
      formData.append("file", file);
      const response = await api.put(
        `/policies/${policyId}/versions/${versionNumber}/document`,
        formData
      );
      setDocuments((current) => ({
        ...current,
        [versionNumber]: response.data,
      }));
      setDocumentModal(null);
      setMessage(
        `Document replaced successfully for V${versionNumber}.`
      );
      await refreshPolicyDocuments(policyId);
    } catch (err) {
      console.error(
        "Failed to replace document:",
        err
      );
      setError(
        err.response?.data?.detail ||
          "Failed to replace policy document."
      );
    } finally {
      setDocumentLoading(false);
    }
  };
  /* =========================================================
     REFRESH CURRENT POLICY DOCUMENTS
     ========================================================= */
  const refreshPolicyDocuments = async (policyId) => {
    try {
      const response = await api.get(
        `/policies/${policyId}/versions`
      );
      const loadedVersions =
        Array.isArray(response.data)
          ? response.data
          : [];
      setVersions(loadedVersions);
      await loadDocumentsForVersions(
        policyId,
        loadedVersions
      );
    } catch (err) {
      console.error(
        "Failed to refresh policy data:",
        err
      );
    }
  };
  /* =========================================================
     VIEW DOCUMENT
     ========================================================= */
  const viewDocument = (
    policyId,
    versionNumber
  ) => {
    const baseURL =
      api.defaults.baseURL ||
      "http://127.0.0.1:8001/api";
    const documentURL =
      `${baseURL}/policies/${policyId}/versions/${versionNumber}/document/file`;
    window.open(
      documentURL,
      "_blank",
      "noopener,noreferrer"
    );
  };
  /* =========================================================
     OPEN DOCUMENT MODAL
     ========================================================= */
  const openDocumentModal = (
    policyId,
    versionNumber,
    mode
  ) => {
    setError("");
    setMessage("");
    setDocumentModal({
      policyId,
      versionNumber,
      mode,
    });
  };
  /* =========================================================
     INITIAL LOAD
     ========================================================= */
  useEffect(() => {
    loadPolicies();
    loadRegulatoryChanges();
    checkSystemHealth();

    const healthInterval = window.setInterval(checkSystemHealth, 60000);
    return () => window.clearInterval(healthInterval);
  }, []);
  /* =========================================================
     SECTION NAVIGATION
     ========================================================= */
  const handleSectionChange = (section) => {
    setActiveSection(section);
    setMessage("");
    setError("");
    if (section === "overview") {
      setSelectedPolicy(null);
      setVersions([]);
      setDocuments({});
      setDependencies([]);
      loadPolicies();
      loadRegulatoryChanges();
    }
    if (section === "policies") {
      setSelectedPolicy(null);
      setVersions([]);
      setDocuments({});
      setDependencies([]);
      loadPolicies();
    }
    if (section === "versions") {
      setSelectedPolicy(null);
      setVersions([]);
      setDocuments({});
      setDependencies([]);
      loadPolicies();
    }
    if (section === "relationships") {
      setSelectedPolicy(null);
      setVersions([]);
      setDocuments({});
      setDependencies([]);
      loadPolicies();
    }
  };
  /* =========================================================
     CREATE POLICY
     ========================================================= */
  const createPolicy = async (formData) => {
    try {
      setError("");
      setMessage("");
      await api.post(
        "/policies",
        formData
      );
      setMessage(
        "Policy created successfully."
      );
      setShowPolicyForm(false);
      await loadPolicies();
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Failed to create policy."
      );
    }
  };
  /* =========================================================
     UPDATE POLICY
     ========================================================= */
  const updatePolicy = async (
    policyId,
    formData
  ) => {
    try {
      setError("");
      setMessage("");
      await api.put(
        `/policies/${policyId}`,
        formData
      );
      setMessage(
        "Policy updated successfully."
      );
      await loadPolicies();
      if (
        selectedPolicy?.policy_id ===
        policyId
      ) {
        setSelectedPolicy((current) => ({
          ...current,
          ...formData,
        }));
      }
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Failed to update policy."
      );
    }
  };
  /* =========================================================
     CREATE VERSION
     ========================================================= */
  const createVersion = async (formData) => {
    if (!selectedPolicy) {
      setError("Select a policy first.");
      return;
    }
    try {
      setError("");
      setMessage("");
      await api.post(
        `/policies/${selectedPolicy.policy_id}/versions`,
        formData
      );
      setMessage(
        "Policy version created successfully."
      );
      setShowVersionForm(false);
      await loadPolicyData(
        selectedPolicy,
        false
      );
      scrollToVersionHistory();
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Failed to create policy version."
      );
    }
  };
  /* =========================================================
     SUMMARY
     ========================================================= */
  const totalPolicies =
    policies.length;
  const knownVersionCounts = policies.filter(
    (policy) => Number.isFinite(Number(policy.version_count)) && policy.version_count !== null && policy.version_count !== ""
  );

  const totalVersions = knownVersionCounts.reduce(
    (total, policy) => total + Number(policy.version_count),
    0
  );
  const activePolicies =
    policies.filter(
      (policy) =>
        policy.status === "active" ||
        policy.is_active === true
    ).length;
  /* =========================================================
     RENDER
     ========================================================= */
  return (
    <div className="admin-dashboard">
      {/* ===================================================
          SIDEBAR
          =================================================== */}
      <aside className="admin-sidebar">
        <div className="admin-sidebar-content">
          <div className="admin-brand">
            <div className="admin-brand-mark">
              PL
            </div>
            <div>
              <h2>PolicyLens</h2>
              <p>Admin Workspace</p>
            </div>
          </div>
          <div className="admin-divider" />
          <div className="admin-section-label">
            WORKSPACE
          </div>
          <nav className="admin-nav">
            <button
              type="button"
              className={`admin-nav-item ${
                activeSection === "overview"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleSectionChange("overview")
              }
            >
              <span>⌂</span>
              Overview
            </button>
            <button
              type="button"
              className={`admin-nav-item ${
                activeSection === "policies"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleSectionChange("policies")
              }
            >
              <span>▣</span>
              Policies
            </button>
            <button
              type="button"
              className={`admin-nav-item ${
                activeSection === "versions"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleSectionChange("versions")
              }
            >
              <span>◫</span>
              Versions
            </button>
            <button
              type="button"
              className={`admin-nav-item ${
                activeSection ===
                "relationships"
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                handleSectionChange(
                  "relationships"
                )
              }
            >
              <span>⌁</span>
              Relationships
            </button>
            <button
              type="button"
              className="admin-nav-item"
              onClick={() => {
                setMessage(
                  "Analysis Scenarios will be implemented in a later phase."
                );
                setError("");
              }}
            >
              <span>◇</span>
              Analysis Scenarios
            </button>
          </nav>
          <div className="admin-section-label admin-management-label">
            MANAGEMENT
          </div>
          <nav className="admin-nav">
            <button
              type="button"
              className="admin-nav-item"
              onClick={() => {
                setMessage(
                  "User management will be implemented later."
                );
                setError("");
              }}
            >
              <span>◎</span>
              Users
            </button>
            <button
              type="button"
              className="admin-nav-item"
              onClick={() => {
                setMessage(
                  "System settings will be implemented later."
                );
                setError("");
              }}
            >
              <span>⚙</span>
              Settings
            </button>
          </nav>
        </div>
        <div className="admin-sidebar-footer">
          <button
            type="button"
            className="admin-back-button"
            onClick={() =>
              navigate("/")
            }
          >
            ← Back to Application
          </button>
        </div>
      </aside>
      {/* ===================================================
          MAIN
          =================================================== */}
      <main className="admin-main">
        <header className="admin-header">
          <div>
            <div className="admin-eyebrow">
              POLICY MANAGEMENT
            </div>
            <h1>
              {activeSection ===
                "overview" &&
                "Admin Overview"}
              {activeSection ===
                "policies" &&
                "Policy Management"}
              {activeSection ===
                "versions" &&
                "Policy Versions"}
              {activeSection ===
                "relationships" &&
                "Policy Relationships"}
            </h1>
            <p>
              Manage policies, versions,
              documents and relationships.
            </p>
          </div>
          <div className={`admin-header-status ${systemStatus}`} role="status" aria-live="polite">
            <span className="admin-status-dot" />
            {systemStatus === "checking"
              ? "Checking system..."
              : systemStatus === "online"
              ? "System Online"
              : "System Unavailable"}
          </div>
        </header>
        {/* =================================================
            MESSAGES
            ================================================= */}
        {message && (
          <div className="admin-alert admin-alert-success">
            <span>✓</span>
            {message}
          </div>
        )}
        {error && (
          <div className="admin-alert admin-alert-error">
            <span>!</span>
            {error}
          </div>
        )}
        {/* =================================================
            OVERVIEW
            ================================================= */}
        {activeSection === "overview" && (
          <OverviewSection
            policies={policies}
            loading={loading}
            totalPolicies={totalPolicies}
            totalVersions={totalVersions}
            activePolicies={activePolicies}
            regulatoryChanges={
              regulatoryChanges
            }
            onAdd={() => {
              setError("");
              setMessage("");
              setShowPolicyForm(true);
            }}
            onSelectPolicy={
              selectPolicyFromPolicies
            }
            onViewAll={() =>
              handleSectionChange(
                "policies"
              )
            }
          />
        )}
        {/* =================================================
            POLICIES
            ================================================= */}
        {activeSection === "policies" && (
          <PolicySection
            policies={policies}
            loading={loading}
            selectedPolicy={selectedPolicy}
            versions={versions}
            dependencies={dependencies}
            documents={documents}
            documentLoading={
              documentLoading
            }
            versionHistoryRef={
              versionHistoryRef
            }
            onSelectPolicy={
              selectPolicyFromPolicies
            }
            onOpenDocument={
              openDocumentModal
            }
            onViewDocument={
              viewDocument
            }
            onAdd={() => {
              setError("");
              setMessage("");
              setShowPolicyForm(true);
            }}
            onUpdate={updatePolicy}
            onAddVersion={() => {
              setError("");
              setMessage("");
              setShowVersionForm(true);
            }}
            onCloseDetails={() => {
              setSelectedPolicy(null);
              setVersions([]);
              setDocuments({});
              setDependencies([]);
            }}
          />
        )}
        {/* =================================================
            VERSIONS
            ================================================= */}
        {activeSection === "versions" && (
          <VersionSection
            policies={policies}
            selectedPolicy={selectedPolicy}
            versions={versions}
            documents={documents}
            documentLoading={
              documentLoading
            }
            onSelectPolicy={
              selectPolicyFromVersions
            }
            onOpenDocument={
              openDocumentModal
            }
            onViewDocument={
              viewDocument
            }
          />
        )}
        {/* =================================================
            RELATIONSHIPS
            ================================================= */}
        {activeSection ===
          "relationships" && (
          <RelationshipOverview
            policies={policies}
            selectedPolicy={
              selectedPolicy
            }
            dependencies={
              dependencies
            }
            onSelectPolicy={
              selectPolicyFromRelationships
            }
          />
        )}
      </main>
      {/* ===================================================
          ADD POLICY
          =================================================== */}
      {showPolicyForm && (
        <PolicyForm
          onClose={() =>
            setShowPolicyForm(false)
          }
          onSubmit={createPolicy}
        />
      )}
      {/* ===================================================
          ADD VERSION
          =================================================== */}
      {showVersionForm &&
        selectedPolicy && (
          <VersionForm
            policy={selectedPolicy}
            onClose={() =>
              setShowVersionForm(false)
            }
            onSubmit={createVersion}
          />
        )}
      {/* ===================================================
          DOCUMENT MODAL
          =================================================== */}
      {documentModal && (
        <DocumentModal
          modal={documentModal}
          loading={documentLoading}
          onClose={() =>
            setDocumentModal(null)
          }
          onSubmit={(file) => {
            if (
              documentModal.mode ===
              "replace"
            ) {
              replaceDocument(
                documentModal.policyId,
                documentModal.versionNumber,
                file
              );
            } else {
              uploadDocument(
                documentModal.policyId,
                documentModal.versionNumber,
                file
              );
            }
          }}
        />
      )}
    </div>
  );
}
/* ===========================================================
   OVERVIEW SECTION
   =========================================================== */
function OverviewSection({
  policies,
  loading,
  totalPolicies,
  totalVersions,
  versionCountsComplete,
  activePolicies,
  regulatoryChanges,
  onAdd,
  onSelectPolicy,
  onViewAll,
}) {
  return (
    <section className="admin-content-section">
      <div className="admin-page-actions">
        <div>
          <h2>Workspace Overview</h2>
          <p>
            Manage the PolicyLens
            policy repository.
          </p>
        </div>
        <button
          type="button"
          className="admin-primary-button"
          onClick={onAdd}
        >
          + Add Policy
        </button>
      </div>
      <div className="admin-stat-grid">
        <StatCard
          label="TOTAL POLICIES"
          value={totalPolicies}
          caption="Policy records"
        />
        <StatCard
          label="POLICY VERSIONS"
          value={versionCountsComplete ? totalVersions : `${totalVersions}+`}
          caption={versionCountsComplete ? "Version records" : "Known versions; some counts unavailable"}
        />
        <StatCard
          label="ACTIVE POLICIES"
          value={activePolicies}
          caption="Currently active"
        />
        <StatCard
          label="REGULATORY CHANGES"
          value={regulatoryChanges.length}
          caption="Tracked changes"
        />
      </div>
      <div className="admin-card">
        <div className="admin-card-header">
          <div>
            <h3>Recent Policies</h3>
            <p>
              Select a policy to view
              its versions and
              relationships.
            </p>
          </div>
          <button
            type="button"
            className="admin-secondary-button"
            onClick={onViewAll}
          >
            View All
          </button>
        </div>
        <PolicyTable
          policies={policies.slice(0, 8)}
          loading={loading}
          onSelectPolicy={
            onSelectPolicy
          }
        />
      </div>
      <div className="admin-card">
        <div className="admin-card-header">
          <div>
            <h3>Tracked Regulatory Changes</h3>
            <p>Recently registered changes available to the PolicyLens workflow.</p>
          </div>
          <span className="admin-regulatory-count">{regulatoryChanges.length} total</span>
        </div>
        {regulatoryChanges.length === 0 ? (
          <div className="admin-empty-state">No regulatory changes were returned by the backend.</div>
        ) : (
          <div className="admin-regulatory-list">
            {regulatoryChanges.slice(0, 5).map((change, index) => {
              const changeId = change.regulatory_change_id || change.change_id || change.id || `change-${index + 1}`;
              const title = change.title || change.change_title || change.name || change.summary || change.description || changeId;
              const source = change.act_name || change.source || change.regulation || change.legal_source;
              const effectiveDate = change.effective_date || change.effective_from || change.published_date || change.date;
              const status = change.status || "Tracked";
              return (
                <div className="admin-regulatory-item" key={changeId}>
                  <div className="admin-regulatory-item-main">
                    <span className="admin-regulatory-id">{changeId}</span>
                    <strong>{title}</strong>
                    {source && <span className="admin-regulatory-source">{source}</span>}
                  </div>
                  <div className="admin-regulatory-item-meta">
                    {effectiveDate && <span>{effectiveDate}</span>}
                    <span className="admin-regulatory-status">{status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
/* ===========================================================
   STAT CARD
   =========================================================== */
function StatCard({
  label,
  value,
  caption,
}) {
  return (
    <div className="admin-stat-card">
      <span className="admin-stat-label">
        {label}
      </span>
      <strong>{value}</strong>
      <span className="admin-stat-caption">
        {caption}
      </span>
    </div>
  );
}
/* ===========================================================
   POLICY TABLE
   =========================================================== */
function PolicyTable({
  policies,
  loading,
  onSelectPolicy,
}) {
  if (loading) {
    return (
      <div className="admin-empty-state">
        Loading policies...
      </div>
    );
  }
  if (!policies.length) {
    return (
      <div className="admin-empty-state">
        No policies found.
      </div>
    );
  }
  return (
    <div className="admin-table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>POLICY ID</th>
            <th>POLICY NAME</th>
            <th>CATEGORY</th>
            <th>DEPARTMENT</th>
            <th>STATUS</th>
            <th>ACTION</th>
          </tr>
        </thead>
        <tbody>
          {policies.map((policy) => (
            <tr
              key={policy.policy_id}
            >
              <td>
                {policy.policy_id}
              </td>
              <td>
                <strong>
                  {policy.policy_name}
                </strong>
              </td>
              <td>
                {policy.category || "—"}
              </td>
              <td>
                {policy.department || "—"}
              </td>
              <td>
                <span
                  className={`admin-badge ${
                    String(policy.status || (policy.is_active === true ? "active" : policy.is_active === false ? "inactive" : "unknown")).toLowerCase() === "active"
                      ? "active"
                      : String(policy.status || (policy.is_active === true ? "active" : policy.is_active === false ? "inactive" : "unknown")).toLowerCase() === "inactive"
                      ? "inactive"
                      : "unknown"
                  }`}
                >
                  {policy.status || (policy.is_active === true ? "active" : policy.is_active === false ? "inactive" : "unknown")}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  className="admin-table-button view-policy-button"
                  onClick={() =>
                    onSelectPolicy(
                      policy
                    )
                  }
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
/* ===========================================================
   POLICY SECTION
   =========================================================== */
function PolicySection({
  policies,
  loading,
  selectedPolicy,
  versions,
  dependencies,
  documents,
  documentLoading,
  versionHistoryRef,
  onSelectPolicy,
  onOpenDocument,
  onViewDocument,
  onAdd,
  onUpdate,
  onAddVersion,
  onCloseDetails,
}) {
  return (
    <section className="admin-content-section">
      <div className="admin-page-actions">
        <div>
          <h2>Policies</h2>
          <p>
            Manage policies and
            their version history.
          </p>
        </div>
        <button
          type="button"
          className="admin-primary-button"
          onClick={onAdd}
        >
          + Add Policy
        </button>
      </div>
      <div className="admin-card">
        <div className="admin-card-header">
          <div>
            <h3>Policy Repository</h3>
            <p>
              Select any policy to
              manage its versions
              and documents.
            </p>
          </div>
        </div>
        <PolicyTable
          policies={policies}
          loading={loading}
          onSelectPolicy={
            onSelectPolicy
          }
        />
      </div>
      {selectedPolicy && (
        <div className="admin-policy-details">
          <div className="admin-detail-header">
            <div>
              <div className="admin-eyebrow">
                SELECTED POLICY
              </div>
              <h2>
                {selectedPolicy.policy_name}
              </h2>
              <p>
                {selectedPolicy.policy_id}
              </p>
            </div>
            <div className="admin-detail-actions">
              <button
                type="button"
                className="admin-secondary-button"
                onClick={onCloseDetails}
              >
                Close
              </button>
              <button
                type="button"
                className="admin-primary-button"
                onClick={onAddVersion}
              >
                + Add Version
              </button>
            </div>
          </div>
          <div className="admin-detail-grid">
            <DetailCard
              label="POLICY ID"
              value={
                selectedPolicy.policy_id
              }
            />
            <DetailCard
              label="CATEGORY"
              value={
                selectedPolicy.category ||
                "—"
              }
            />
            <DetailCard
              label="DEPARTMENT"
              value={
                selectedPolicy.department ||
                "—"
              }
            />
            <DetailCard
              label="STATUS"
              value={
                selectedPolicy.status ||
                "—"
              }
            />
          </div>
          {selectedPolicy.description && (
            <div className="admin-detail-section">
              <span className="admin-detail-label">
                DESCRIPTION
              </span>
              <h3>
                Policy Description
              </h3>
              <p className="admin-detail-description">
                {selectedPolicy.description}
              </p>
            </div>
          )}
          {/* =================================================
              VERSION HISTORY / DOCUMENTS
              THIS IS THE SECTION THE POLICY "VIEW" BUTTON
              SCROLLS TO.
              ================================================= */}
          <div
            ref={versionHistoryRef}
            className="admin-detail-section admin-version-history-section"
          >
            <div className="admin-detail-section-header">
              <div>
                <span className="admin-detail-label">
                  VERSION HISTORY
                </span>
                <h3>
                  Policy Documents
                </h3>
                <p>
                  Manage documents attached
                  to each policy version.
                </p>
              </div>
              <button
                type="button"
                className="admin-primary-button"
                onClick={onAddVersion}
              >
                + Add Version
              </button>
            </div>
            <VersionDocumentTable
              policyId={
                selectedPolicy.policy_id
              }
              versions={versions}
              documents={documents}
              documentLoading={
                documentLoading
              }
              onOpenDocument={
                onOpenDocument
              }
              onViewDocument={
                onViewDocument
              }
            />
          </div>
          {/* =================================================
              RELATIONSHIPS
              ================================================= */}
          <div className="admin-detail-section">
            <div className="admin-detail-section-header">
              <div>
                <span className="admin-detail-label">
                  RELATIONSHIPS
                </span>
                <h3>
                  Policy Relationships
                </h3>
                <p>
                  Existing policy dependencies
                  are displayed here.
                </p>
              </div>
            </div>
            <RelationshipTable
              dependencies={dependencies}
            />
          </div>
        </div>
      )}
    </section>
  );
}
/* ===========================================================
   VERSION DOCUMENT TABLE
   FINAL DOCUMENT BEHAVIOR:
   NO DOCUMENT:
       Upload
   DOCUMENT EXISTS:
       View
       Replace
   =========================================================== */
function VersionDocumentTable({
  policyId,
  versions,
  documents,
  documentLoading,
  onOpenDocument,
  onViewDocument,
}) {
  if (!versions.length) {
    return (
      <div className="admin-empty-state">
        No versions found.
      </div>
    );
  }
  return (
    <div className="admin-table-wrapper admin-version-wrapper">
      <table className="admin-table admin-version-table">
        <thead>
          <tr>
            <th>VERSION ID</th>
            <th>VERSION</th>
            <th>EFFECTIVE DATE</th>
            <th>STATUS</th>
            <th>CHANGE</th>
            <th>DOCUMENT</th>
            <th>ACTION</th>
          </tr>
        </thead>
        <tbody>
          {versions.map((version) => {
            const document =
              documents[
                version.version_number
              ];
            return (
              <tr
                key={
                  version.policy_version_id
                }
              >
                <td>
                  {
                    version.policy_version_id
                  }
                </td>
                <td>
                  V{version.version_number}
                </td>
                <td>
                  {version.effective_date}
                </td>
                <td>
                  <span className="admin-badge active">
                    {version.status}
                  </span>
                </td>
                <td className="admin-change-cell">
                  {
                    version.change_description ||
                    "—"
                  }
                </td>
                {/* ===============================
                    DOCUMENT STATUS
                    =============================== */}
                <td className="admin-document-cell">
                  {document ? (
                    <div className="admin-document-info">
                      <span className="admin-document-status uploaded">
                        Document Available
                      </span>
                      <span
                        className="admin-document-name"
                        title={
                          document.file_name
                        }
                      >
                        {document.file_name}
                      </span>
                    </div>
                  ) : (
                    <span className="admin-document-status missing">
                      No Document
                    </span>
                  )}
                </td>
                {/* ===============================
                    FINAL DOCUMENT ACTIONS
                    =============================== */}
                <td className="admin-action-cell">
                  <div className="admin-document-actions">
                    {document ? (
                      <>
                        <button
                          type="button"
                          className="admin-table-button"
                          disabled={
                            documentLoading
                          }
                          onClick={() =>
                            onViewDocument(
                              policyId,
                              version.version_number
                            )
                          }
                        >
                          View
                        </button>
                        <button
                          type="button"
                          className="admin-table-button replace-button"
                          disabled={
                            documentLoading
                          }
                          onClick={() =>
                            onOpenDocument(
                              policyId,
                              version.version_number,
                              "replace"
                            )
                          }
                        >
                          Replace
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="admin-table-button upload-button"
                        disabled={
                          documentLoading
                        }
                        onClick={() =>
                          onOpenDocument(
                            policyId,
                            version.version_number,
                            "upload"
                          )
                        }
                      >
                        Upload
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
/* ===========================================================
   VERSION SECTION
   =========================================================== */
function VersionSection({
  policies,
  selectedPolicy,
  versions,
  documents,
  documentLoading,
  onSelectPolicy,
  onOpenDocument,
  onViewDocument,
}) {
  const [policyId, setPolicyId] =
    useState(
      selectedPolicy?.policy_id || ""
    );
  useEffect(() => {
    setPolicyId(
      selectedPolicy?.policy_id || ""
    );
  }, [selectedPolicy]);
  const currentPolicy =
    policies.find(
      (policy) =>
        policy.policy_id === policyId
    );
  const currentVersions =
    selectedPolicy?.policy_id ===
    policyId
      ? versions
      : [];
  return (
    <section className="admin-content-section">
      <div className="admin-page-actions">
        <div>
          <h2>Policy Versions</h2>
          <p>
            Select a policy to inspect
            its complete version history.
          </p>
        </div>
      </div>
      <div className="admin-card">
        <div className="admin-form-field">
          <label>
            Select Policy
          </label>
          <select
            value={policyId}
            onChange={(event) => {
              const value =
                event.target.value;
              setPolicyId(value);
              const policy =
                policies.find(
                  (item) =>
                    item.policy_id ===
                    value
                );
              if (policy) {
                onSelectPolicy(policy);
              }
            }}
          >
            <option value="">
              Select a policy
            </option>
            {policies.map((policy) => (
              <option
                key={policy.policy_id}
                value={policy.policy_id}
              >
                {policy.policy_id} —{" "}
                {policy.policy_name}
              </option>
            ))}
          </select>
        </div>
      </div>
      {currentPolicy && (
        <div className="admin-card">
          <div className="admin-card-header">
            <div>
              <h3>
                {currentPolicy.policy_name}
              </h3>
              <p>
                {currentPolicy.policy_id}
              </p>
            </div>
          </div>
          <VersionDocumentTable
            policyId={policyId}
            versions={currentVersions}
            documents={documents}
            documentLoading={
              documentLoading
            }
            onOpenDocument={
              onOpenDocument
            }
            onViewDocument={
              onViewDocument
            }
          />
        </div>
      )}
    </section>
  );
}
/* ===========================================================
   RELATIONSHIP OVERVIEW
   =========================================================== */
function RelationshipOverview({
  policies,
  selectedPolicy,
  dependencies,
  onSelectPolicy,
}) {
  return (
    <section className="admin-content-section">
      <div className="admin-page-actions">
        <div>
          <h2>
            Policy Relationships
          </h2>
          <p>
            Explore dependencies
            between policies.
          </p>
        </div>
      </div>
      <div className="admin-card">
        <div className="admin-form-field">
          <label>
            Select Policy
          </label>
          <select
            value={
              selectedPolicy?.policy_id ||
              ""
            }
            onChange={(event) => {
              const policy =
                policies.find(
                  (item) =>
                    item.policy_id ===
                    event.target.value
                );
              if (policy) {
                onSelectPolicy(policy);
              }
            }}
          >
            <option value="">
              Select a policy
            </option>
            {policies.map((policy) => (
              <option
                key={policy.policy_id}
                value={policy.policy_id}
              >
                {policy.policy_id} —{" "}
                {policy.policy_name}
              </option>
            ))}
          </select>
        </div>
      </div>
      {selectedPolicy && (
        <div className="admin-card">
          <div className="admin-card-header">
            <div>
              <h3>
                {selectedPolicy.policy_name}
              </h3>
              <p>
                {selectedPolicy.policy_id}
              </p>
            </div>
          </div>
          <RelationshipTable
            dependencies={dependencies}
          />
        </div>
      )}
    </section>
  );
}
/* ===========================================================
   RELATIONSHIP TABLE
   =========================================================== */
function RelationshipTable({
  dependencies,
}) {
  if (!dependencies.length) {
    return (
      <div className="admin-empty-state">
        No relationships found.
      </div>
    );
  }
  return (
    <div className="admin-table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>RELATIONSHIP ID</th>
            <th>TARGET POLICY</th>
            <th>RELATIONSHIP TYPE</th>
          </tr>
        </thead>
        <tbody>
          {dependencies.map(
            (dependency, index) => (
              <tr
                key={
                  dependency.relationship_id ||
                  index
                }
              >
                <td>
                  {
                    dependency.relationship_id ||
                    "—"
                  }
                </td>
                <td>
                  {
                    dependency.target_policy_id ||
                    dependency.related_policy_id ||
                    "—"
                  }
                </td>
                <td>
                  {
                    dependency.relationship_type ||
                    "—"
                  }
                </td>
              </tr>
            )
          )}
        </tbody>
      </table>
    </div>
  );
}
/* ===========================================================
   DETAIL CARD
   =========================================================== */
function DetailCard({
  label,
  value,
}) {
  return (
    <div className="admin-detail-card">
      <span className="admin-detail-label">
        {label}
      </span>
      <strong>{value}</strong>
    </div>
  );
}
/* ===========================================================
   DOCUMENT MODAL
   =========================================================== */
function DocumentModal({
  modal,
  loading,
  onClose,
  onSubmit,
}) {
  const [file, setFile] =
    useState(null);
  const mode =
    modal?.mode === "replace"
      ? "replace"
      : "upload";
  return (
    <div className="admin-modal-overlay">
      <div className="admin-document-modal">
        <div className="admin-modal-header">
          <div>
            <span className="admin-detail-label">
              POLICY DOCUMENT
            </span>
            <h2>
              {mode === "replace"
                ? "Replace Document"
                : "Upload Document"}
            </h2>
            <p>
              {modal.policyId} · V
              {modal.versionNumber}
            </p>
          </div>
          <button
            type="button"
            className="admin-modal-close"
            onClick={onClose}
            disabled={loading}
          >
            ×
          </button>
        </div>
        <div className="admin-document-upload-box">
          <div className="admin-upload-icon">
            ↑
          </div>
          <h3>
            Choose policy document
          </h3>
          <p>
            Supported formats: PDF,
            TXT, Markdown
          </p>
          <input
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            onChange={(event) => {
              setFile(
                event.target.files?.[0] ||
                null
              );
            }}
          />
          {file && (
            <div className="admin-selected-file">
              <strong>
                Selected file
              </strong>
              <span>
                {file.name}
              </span>
              <small>
                {(
                  file.size / 1024
                ).toFixed(1)} KB
              </small>
            </div>
          )}
        </div>
        <div className="admin-modal-actions">
          <button
            type="button"
            className="admin-secondary-button"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="admin-primary-button"
            disabled={
              loading || !file
            }
            onClick={() =>
              onSubmit(file)
            }
          >
            {loading
              ? "Saving..."
              : mode === "replace"
              ? "Replace Document"
              : "Upload Document"}
          </button>
        </div>
      </div>
    </div>
  );
}
/* ===========================================================
   POLICY FORM
   =========================================================== */
function PolicyForm({
  onClose,
  onSubmit,
}) {
  const [form, setForm] =
    useState({
      policy_id: "",
      policy_name: "",
      category: "",
      department: "",
      description: "",
    });
  const updateField = (event) => {
    const {
      name,
      value,
    } = event.target;
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };
  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal">
        <div className="admin-modal-header">
          <div>
            <span className="admin-detail-label">
              POLICY MANAGEMENT
            </span>
            <h2>
              Add Policy
            </h2>
          </div>
          <button
            type="button"
            className="admin-modal-close"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        <div className="admin-form-grid">
          <FormField
            label="Policy ID"
            name="policy_id"
            value={form.policy_id}
            onChange={updateField}
            placeholder="POL-021"
          />
          <FormField
            label="Policy Name"
            name="policy_name"
            value={form.policy_name}
            onChange={updateField}
            placeholder="Policy name"
          />
          <FormField
            label="Category"
            name="category"
            value={form.category}
            onChange={updateField}
            placeholder="Human Resources"
          />
          <FormField
            label="Department"
            name="department"
            value={form.department}
            onChange={updateField}
            placeholder="Human Resources"
          />
          <div className="admin-form-field full">
            <label>
              Description
            </label>
            <textarea
              name="description"
              value={form.description}
              onChange={updateField}
              rows="5"
              placeholder="Describe the purpose of the policy."
            />
          </div>
        </div>
        <div className="admin-modal-actions">
          <button
            type="button"
            className="admin-secondary-button"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="admin-primary-button"
            onClick={() =>
              onSubmit(form)
            }
          >
            Create Policy
          </button>
        </div>
      </div>
    </div>
  );
}
/* ===========================================================
   FORM FIELD
   =========================================================== */
function FormField({
  label,
  name,
  value,
  onChange,
  placeholder,
}) {
  return (
    <div className="admin-form-field">
      <label>
        {label}
      </label>
      <input
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
      />
    </div>
  );
}
/* ===========================================================
   VERSION FORM
   =========================================================== */
function VersionForm({
  policy,
  onClose,
  onSubmit,
}) {
  const [form, setForm] =
    useState({
      policy_version_id: "",
      version_number: "",
      effective_date: "",
      change_description: "",
    });
  const updateField = (event) => {
    const {
      name,
      value,
    } = event.target;
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  };
  return (
    <div className="admin-modal-overlay">
      <div className="admin-modal">
        <div className="admin-modal-header">
          <div>
            <span className="admin-detail-label">
              ADD VERSION
            </span>
            <h2>
              New Policy Version
            </h2>
            <p>
              {policy.policy_id} —{" "}
              {policy.policy_name}
            </p>
          </div>
          <button
            type="button"
            className="admin-modal-close"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        <div className="admin-form-grid">
          <FormField
            label="Policy Version ID"
            name="policy_version_id"
            value={
              form.policy_version_id
            }
            onChange={updateField}
            placeholder="POL-021-V1"
          />
          <div className="admin-form-field">
            <label>
              Version Number
            </label>
            <input
              name="version_number"
              type="number"
              min="1"
              value={
                form.version_number
              }
              onChange={updateField}
              placeholder="1"
            />
          </div>
          <div className="admin-form-field">
            <label>
              Effective Date
            </label>
            <input
              name="effective_date"
              type="date"
              value={
                form.effective_date
              }
              onChange={updateField}
            />
          </div>
          <div className="admin-form-field full">
            <label>
              Change Description
            </label>
            <textarea
              name="change_description"
              value={
                form.change_description
              }
              onChange={updateField}
              rows="5"
              placeholder="Describe what changed in this version."
            />
          </div>
        </div>
        <div className="admin-modal-actions">
          <button
            type="button"
            className="admin-secondary-button"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="admin-primary-button"
            onClick={() =>
              onSubmit({
                ...form,
                version_number:
                  Number(
                    form.version_number
                  ),
              })
            }
          >
            Create Version
          </button>
        </div>
      </div>
    </div>
  );
}