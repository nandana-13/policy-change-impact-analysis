import { useEffect, useMemo, useState } from "react";

import { useNavigate } from "react-router-dom";

import api from "../../api/api";

import "./PolicyDashboard.css";

function PolicyDashboard() {

  const navigate = useNavigate();

  // ============================================================

  // STATE

  // ============================================================

  const [activeSection, setActiveSection] =

    useState("dashboard");

  const [backendStatus, setBackendStatus] =

    useState("Checking...");

  const [policies, setPolicies] = useState([]);

  const [selectedPolicyId, setSelectedPolicyId] =

    useState("");

  const [versions, setVersions] = useState([]);

  const [selectedOldVersion, setSelectedOldVersion] =

    useState("");

  const [selectedNewVersion, setSelectedNewVersion] =

    useState("");

  const [dependencies, setDependencies] =

    useState([]);

  const [loading, setLoading] = useState(false);

  const [loadingVersions, setLoadingVersions] =

    useState(false);

  const [loadingDependencies, setLoadingDependencies] =

    useState(false);

  const [error, setError] = useState("");

  const [changeResult, setChangeResult] = useState(null);

  const [loadingChanges, setLoadingChanges] = useState(false);

  const [documentStatus, setDocumentStatus] = useState({

    old: null,

    new: null,

  });

  // Evidence for the selected policy and dependent policies
  const [evidenceResult, setEvidenceResult] = useState(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [evidenceError, setEvidenceError] = useState("");

  // ============================================================

  // BACKEND HEALTH

  // ============================================================

  useEffect(() => {

    api

      .get("/health")

      .then((response) => {

        setBackendStatus(

          response.data.status || "Online"

        );

      })

      .catch((err) => {

        console.error(

          "Backend connection failed:",

          err

        );

        setBackendStatus("Offline");

      });

  }, []);

  // ============================================================

  // LOAD POLICIES

  // ============================================================

  useEffect(() => {

    loadPolicies();

  }, []);

  const loadPolicies = async () => {

    try {

      setLoading(true);

      setError("");

      const response = await api.get("/policies");

      const data = Array.isArray(response.data)

        ? response.data

        : [];

      setPolicies(data);

      if (data.length > 0) {

        setSelectedPolicyId(

          data[0].policy_id

        );

      }

    } catch (err) {

      console.error(

        "Failed to load policies:",

        err

      );

      setError(

        err.response?.data?.detail ||

          "Failed to load policies."

      );

    } finally {

      setLoading(false);

    }

  };

  // ============================================================

  // FIND LATEST POLICY UPDATE

  //

  // We only display ONE latest policy update on the dashboard.

  //

  // Priority:

  // created_at

  // updated_at

  // policy_id fallback

  // ============================================================

  const latestPolicy = useMemo(() => {

    if (!policies.length) {

      return null;

    }

    const sorted = [...policies].sort(

      (a, b) => {

        const dateA = new Date(

          a.created_at ||

            a.updated_at ||

            0

        ).getTime();

        const dateB = new Date(

          b.created_at ||

            b.updated_at ||

            0

        ).getTime();

        if (

          !Number.isNaN(dateA) &&

          !Number.isNaN(dateB) &&

          dateA !== dateB

        ) {

          return dateB - dateA;

        }

        return String(

          b.policy_id || ""

        ).localeCompare(

          String(a.policy_id || "")

        );

      }

    );

    return sorted[0];

  }, [policies]);

  // ============================================================

  // LOAD VERSIONS

  // ============================================================

  useEffect(() => {

    if (!selectedPolicyId) {

      setVersions([]);

      setSelectedOldVersion("");

      setSelectedNewVersion("");

      return;

    }

    loadVersions(selectedPolicyId);

  }, [selectedPolicyId]);

  const loadVersions = async (policyId) => {

    try {

      setLoadingVersions(true);

      setError("");

      const response = await api.get(

        `/policies/${policyId}/versions`

      );

      const data = Array.isArray(response.data)

        ? [...response.data]

        : [];

      data.sort(

        (a, b) =>

          Number(

            a.version_number || 0

          ) -

          Number(

            b.version_number || 0

          )

      );

      setVersions(data);

      if (data.length >= 2) {

        setSelectedOldVersion(

          String(

            data[data.length - 2]

              .version_number

          )

        );

        setSelectedNewVersion(

          String(

            data[data.length - 1]

              .version_number

          )

        );

      } else if (data.length === 1) {

        setSelectedOldVersion("");

        setSelectedNewVersion(

          String(

            data[0].version_number

          )

        );

      } else {

        setSelectedOldVersion("");

        setSelectedNewVersion("");

      }

    } catch (err) {

      console.error(

        "Failed to load versions:",

        err

      );

      setVersions([]);

      setSelectedOldVersion("");

      setSelectedNewVersion("");

      setError(

        err.response?.data?.detail ||

          "Failed to load policy versions."

      );

    } finally {

      setLoadingVersions(false);

    }

  };

  // ============================================================

  // LOAD DEPENDENCIES

  // ============================================================

  useEffect(() => {

    if (!selectedPolicyId) {

      setDependencies([]);

      return;

    }

    loadDependencies(

      selectedPolicyId

    );

  }, [selectedPolicyId]);

  const loadDependencies = async (

    policyId

  ) => {

    try {

      setLoadingDependencies(true);

      const response = await api.get(

        `/policies/${policyId}/dependencies`

      );

      const data = Array.isArray(

        response.data

      )

        ? response.data

        : [];

      setDependencies(data);

    } catch (err) {

      console.error(

        "Failed to load dependencies:",

        err

      );

      setDependencies([]);

    } finally {

      setLoadingDependencies(false);

    }

  };

  // ============================================================

  // CHANGE ENGINE

  // ============================================================

  useEffect(() => {

    setChangeResult(null);

    if (

      !selectedPolicyId ||

      !selectedOldVersion ||

      !selectedNewVersion

    ) {

      setLoadingChanges(false);

      return;

    }

    const oldNumber =

      Number(selectedOldVersion);

    const newNumber =

      Number(selectedNewVersion);

    if (oldNumber >= newNumber) {

      setLoadingChanges(false);

      setError(

        "Previous version must be earlier than the new version."

      );

      return;

    }

    const compareVersions = async () => {

      try {

        setLoadingChanges(true);

        setError("");

        const response = await api.get(

          `/change-engine/policies/${selectedPolicyId}/compare`,

          {

            params: {

              old_version: oldNumber,

              new_version: newNumber,

            },

          }

        );

        setChangeResult(response.data);

      } catch (err) {

        console.error(

          "Change Engine comparison failed:",

          err

        );

        setChangeResult(null);

        setError(

          err.response?.data?.detail ||

            "Failed to compare the selected policy versions."

        );

      } finally {

        setLoadingChanges(false);

      }

    };

    compareVersions();

  }, [

    selectedPolicyId,

    selectedOldVersion,

    selectedNewVersion,

  ]);

  // ============================================================

  // LOAD DOCUMENT STATUS

  // ============================================================

  useEffect(() => {

    if (

      !selectedPolicyId ||

      !selectedOldVersion ||

      !selectedNewVersion

    ) {

      setDocumentStatus({

        old: null,

        new: null,

      });

      return;

    }

    const loadDocumentStatus = async () => {

      const result = {

        old: null,

        new: null,

      };

      try {

        const response = await api.get(

          `/policies/${selectedPolicyId}/versions/${selectedOldVersion}/document`

        );

        result.old = response.data;

      } catch (err) {

        result.old = null;

      }

      try {

        const response = await api.get(

          `/policies/${selectedPolicyId}/versions/${selectedNewVersion}/document`

        );

        result.new = response.data;

      } catch (err) {

        result.new = null;

      }

      setDocumentStatus(result);

    };

    loadDocumentStatus();

  }, [

    selectedPolicyId,

    selectedOldVersion,

    selectedNewVersion,

  ]);

  // ============================================================

  // VIEW POLICY DOCUMENT

  // ============================================================

  const viewPolicyDocument = (

    versionNumber

  ) => {

    if (

      !selectedPolicyId ||

      !versionNumber

    ) {

      return;

    }

    const baseURL =

      api.defaults.baseURL || "";

    const documentUrl =

      `${baseURL}/policies/${selectedPolicyId}` +

      `/versions/${versionNumber}/document/file`;

    window.open(

      documentUrl,

      "_blank",

      "noopener,noreferrer"

    );

  };

  // ============================================================

  // SELECTED POLICY

  // ============================================================

  const selectedPolicy = useMemo(() => {

    return policies.find(

      (policy) =>

        policy.policy_id ===

        selectedPolicyId

    );

  }, [

    policies,

    selectedPolicyId,

  ]);

  const oldVersion = useMemo(() => {

    return versions.find(

      (version) =>

        String(

          version.version_number

        ) ===

        String(

          selectedOldVersion

        )

    );

  }, [

    versions,

    selectedOldVersion,

  ]);

  const newVersion = useMemo(() => {

    return versions.find(

      (version) =>

        String(

          version.version_number

        ) ===

        String(

          selectedNewVersion

        )

    );

  }, [

    versions,

    selectedNewVersion,

  ]);

  // ============================================================

  // HELPERS

  // ============================================================

  const getPolicyName = (

    policy

  ) => {

    if (!policy) {

      return "Unknown Policy";

    }

    return (

      policy.policy_name ||

      policy.name ||

      policy.title ||

      policy.policy_id

    );

  };

  const getPolicyDescription = (

    policy

  ) => {

    if (!policy) {

      return "";

    }

    return (

      policy.description ||

      policy.policy_description ||

      ""

    );

  };

  const getVersionLabel = (

    version

  ) => {

    if (!version) {

      return "—";

    }

    return `V${version.version_number}`;

  };

  const getEffectiveDate = (

    version

  ) => {

    if (!version) {

      return "—";

    }

    return (

      version.effective_date ||

      version.effective_from ||

      "—"

    );

  };

  const getTargetPolicyId = (

    dependency

  ) => {

    return (

      dependency.target_policy_id ||

      dependency.dependent_policy_id ||

      dependency.policy_id ||

      ""

    );

  };

  const getTargetPolicy = (

    dependency

  ) => {

    const targetId =

      getTargetPolicyId(

        dependency

      );

    return policies.find(

      (policy) =>

        policy.policy_id ===

        targetId

    );

  };

  const formatDate = (

    value

  ) => {

    if (!value) {

      return "Recently";

    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {

      return "Recently";

    }

    return date.toLocaleDateString(

      "en-IN",

      {

        day: "2-digit",

        month: "short",

        year: "numeric",

      }

    );

  };

  // ============================================================

  // NAVIGATION

  // ============================================================

  const changeSection = (

    section

  ) => {

    setActiveSection(section);

    setError("");

  };

  // ============================================================

  // LATEST POLICY ALERT

  // ============================================================

  const openLatestPolicy = () => {

    if (!latestPolicy) {

      return;

    }

    setSelectedPolicyId(

      latestPolicy.policy_id

    );

    setActiveSection(

      "changes"

    );

  };

  // ============================================================

  // DASHBOARD

  // ============================================================

  const renderDashboard = () => {

    return (

      <>

        <PageHeader

          title="Analyst Dashboard"

          subtitle="Monitor the latest policy updates and analyze their downstream impact."

          backendStatus={

            backendStatus

          }

        />

        {/* ======================================================

            LATEST POLICY ALERT

        ====================================================== */}

        {latestPolicy && (

          <section className="latest-policy-alert">

            <div className="latest-policy-icon">

              🔔

            </div>

            <div className="latest-policy-content">

              <span className="latest-policy-label">

                LATEST POLICY UPDATE

              </span>

              <h2>

                {getPolicyName(

                  latestPolicy

                )}

              </h2>

              <p>

                {latestPolicy.policy_id}

                {latestPolicy.created_at

                  ? ` · Added ${formatDate(

                      latestPolicy.created_at

                    )}`

                  : latestPolicy.updated_at

                  ? ` · Updated ${formatDate(

                      latestPolicy.updated_at

                    )}`

                  : " · Latest policy update"}

              </p>

            </div>

            <button

              className="latest-policy-button"

              onClick={

                openLatestPolicy

              }

            >

              View Policy Changes →

            </button>

          </section>

        )}

        {/* ======================================================

            SUMMARY

        ====================================================== */}

        <section className="dashboard-summary">

          <SummaryCard

            label="TOTAL POLICIES"

            value={

              policies.length

            }

            detail="Policies available"

          />

          <SummaryCard

            label="SELECTED VERSIONS"

            value={

              oldVersion &&

              newVersion

                ? `${getVersionLabel(

                    oldVersion

                  )} → ${getVersionLabel(

                    newVersion

                  )}`

                : "—"

            }

            detail={

              selectedPolicy

                ? getPolicyName(

                    selectedPolicy

                  )

                : "Select a policy"

            }

          />

          <SummaryCard

            label="DEPENDENCIES"

            value={

              dependencies.length

            }

            detail="Current policy relationships"

          />

          <SummaryCard

            label="LATEST UPDATE"

            value={

              latestPolicy

                ? "1"

                : "—"

            }

            detail="Latest policy update"

          />

        </section>

        {/* ======================================================

            MAIN DASHBOARD GRID

        ====================================================== */}

        <section className="dashboard-grid">

          {/* RECENT POLICY */}

          <div className="dashboard-card">

            <CardHeading

              kicker="LATEST ACTIVITY"

              title="Latest Policy Update"

              meta={

                latestPolicy

                  ? latestPolicy.policy_id

                  : "None"

              }

            />

            {latestPolicy ? (

              <div className="latest-dashboard-policy">

                <div>

                  <span className="policy-code">

                    {latestPolicy.policy_id}

                  </span>

                  <h3>

                    {getPolicyName(

                      latestPolicy

                    )}

                  </h3>

                  <p>

                    {getPolicyDescription(

                      latestPolicy

                    ) ||

                      "A new policy or policy update is available for analyst review."}

                  </p>

                </div>

                <button

                  className="primary-button"

                  onClick={

                    openLatestPolicy

                  }

                >

                  Review →

                </button>

              </div>

            ) : (

              <EmptyState text="No policy updates available." />

            )}

          </div>

          {/* CURRENT WORKSPACE */}

          <div className="dashboard-card">

            <CardHeading

              kicker="ANALYST WORKSPACE"

              title="Policy Change Analysis"

              meta="Version comparison"

            />

            <div className="analysis-start">

              <span className="analysis-start-label">

                POLICY CHANGE

              </span>

              <h3>

                Compare two policy versions

              </h3>

              <p>

                Select a policy, choose its

                previous and new versions,

                and review the changes.

              </p>

              <button

                className="primary-button"

                onClick={() =>

                  changeSection(

                    "changes"

                  )

                }

              >

                Open Analysis

              </button>

            </div>

          </div>

        </section>

        {/* ======================================================

            DEPENDENCY SUMMARY

        ====================================================== */}

        <section className="dashboard-card">

          <CardHeading

            kicker="DEPENDENCY OVERVIEW"

            title="Current Policy Dependencies"

            meta={

              loadingDependencies

                ? "Loading..."

                : `${dependencies.length} relationships`

            }

          />

          {dependencies.length === 0 ? (

            <EmptyState text="Select a policy in Policy Changes or Dependencies to review its relationships." />

          ) : (

            <div className="dependency-preview">

              {dependencies

                .slice(0, 5)

                .map(

                  (

                    dependency,

                    index

                  ) => {

                    const targetPolicy =

                      getTargetPolicy(

                        dependency

                      );

                    return (

                      <div

                        className="dependency-preview-row"

                        key={`${getTargetPolicyId(

                          dependency

                        )}-${index}`}

                      >

                        <div>

                          <strong>

                            {targetPolicy

                              ? getPolicyName(

                                  targetPolicy

                                )

                              : getTargetPolicyId(

                                  dependency

                                )}

                          </strong>

                          <span>

                            {getTargetPolicyId(

                              dependency

                            )}

                          </span>

                        </div>

                        <span className="relationship-badge">

                          {dependency.relationship_type ||

                            dependency.relation_type ||

                            dependency.type ||

                            "DEPENDENCY"}

                        </span>

                      </div>

                    );

                  }

                )}

            </div>

          )}

        </section>

      </>

    );

  };

  // ============================================================

  // POLICY CHANGES

  // ============================================================

  const renderPolicyChanges = () => {

    const comparison =

      changeResult?.comparison;

    const summary =

      changeResult?.summary;

    const changes = Array.isArray(

      changeResult?.changes

    )

      ? changeResult.changes

      : [];

    const addedChanges =

      changes.filter(

        (change) =>

          change.change_type ===

          "added"

      );

    const removedChanges =

      changes.filter(

        (change) =>

          change.change_type ===

          "removed"

      );

    const modifiedChanges =

      changes.filter(

        (change) =>

          change.change_type ===

          "modified"

      );

    const unchangedChanges =

      changes.filter(

        (change) =>

          change.change_type ===

          "unchanged"

      );

    const renderChangeGroup = (

      title,

      items,

      changeType

    ) => {

      if (!items.length) {

        return null;

      }

      return (

        <div className="change-engine-placeholder">

          <div className="change-engine-icon">

            {changeType === "added"

              ? "+"

              : changeType === "removed"

              ? "−"

              : changeType === "modified"

              ? "\~"

              : "="}

          </div>

          <div>

            <strong>

              {title} ({items.length})

            </strong>

            <div className="change-types">

              {items.map(

                (change, index) => (

                  <div

                    key={`${change.section}-${change.change_type}-${index}`}

                    style={{

                      marginTop: "12px",

                      padding: "12px",

                      border:

                        "1px solid rgba(255,255,255,0.08)",

                      borderRadius: "8px",

                    }}

                  >

                    <strong>

                      {change.section ||

                        "Unnamed Section"}

                    </strong>

                    {change.similarity !==

                      undefined &&

                      change.similarity !==

                        null && (

                        <div>

                          Similarity:{" "}

                          {(

                            Number(

                              change.similarity

                            ) * 100

                          ).toFixed(2)}

                          %

                        </div>

                      )}

                    {change.old_text && (

                      <div

                        style={{

                          marginTop: "8px",

                        }}

                      >

                        <small>

                          Previous version

                        </small>

                        <p

                          style={{

                            whiteSpace:

                              "pre-wrap",

                            margin:

                              "4px 0 0",

                          }}

                        >

                          {change.old_text}

                        </p>

                      </div>

                    )}

                    {change.new_text && (

                      <div

                        style={{

                          marginTop: "8px",

                        }}

                      >

                        <small>

                          New version

                        </small>

                        <p

                          style={{

                            whiteSpace:

                              "pre-wrap",

                            margin:

                              "4px 0 0",

                          }}

                        >

                          {change.new_text}

                        </p>

                      </div>

                    )}

                  </div>

                )

              )}

            </div>

          </div>

        </div>

      );

    };

    return (

      <>

        <PageHeader

          title="Policy Changes"

          subtitle="Select a policy and compare its previous and new versions."

          backendStatus={

            backendStatus

          }

        />

        <section className="dashboard-card">

          <CardHeading

            kicker="VERSION COMPARISON"

            title="Select Policy Versions"

            meta="Change Engine"

          />

          <div className="change-selector">

            <div className="selector-field">

              <label>

                POLICY

              </label>

              <select

                value={

                  selectedPolicyId

                }

                onChange={(event) =>

                  setSelectedPolicyId(

                    event.target

                      .value

                  )

                }

              >

                <option value="">

                  Select policy

                </option>

                {policies.map(

                  (policy) => (

                    <option

                      key={

                        policy.policy_id

                      }

                      value={

                        policy.policy_id

                      }

                    >

                      {policy.policy_id}{" "}

                      ·{" "}

                      {getPolicyName(

                        policy

                      )}

                    </option>

                  )

                )}

              </select>

            </div>

            <div className="selector-field">

              <label>

                PREVIOUS VERSION

              </label>

              <select

                value={

                  selectedOldVersion

                }

                onChange={(event) =>

                  setSelectedOldVersion(

                    event.target

                      .value

                  )

                }

                disabled={

                  loadingVersions ||

                  versions.length ===

                    0

                }

              >

                <option value="">

                  Select previous version

                </option>

                {versions.map(

                  (version) => (

                    <option

                      key={`old-${version.version_number}`}

                      value={

                        version.version_number

                      }

                    >

                      V

                      {

                        version.version_number

                      }

                    </option>

                  )

                )}

              </select>

            </div>

            <div className="version-arrow">

              →

            </div>

            <div className="selector-field">

              <label>

                NEW VERSION

              </label>

              <select

                value={

                  selectedNewVersion

                }

                onChange={(event) =>

                  setSelectedNewVersion(

                    event.target

                      .value

                  )

                }

                disabled={

                  loadingVersions ||

                  versions.length ===

                    0

                }

              >

                <option value="">

                  Select new version

                </option>

                {versions.map(

                  (version) => (

                    <option

                      key={`new-${version.version_number}`}

                      value={

                        version.version_number

                      }

                    >

                      V

                      {

                        version.version_number

                      }

                    </option>

                  )

                )}

              </select>

            </div>

          </div>

          {selectedPolicy && (

            <div className="selected-policy-strip">

              <div>

                <span>

                  SELECTED POLICY

                </span>

                <strong>

                  {getPolicyName(

                    selectedPolicy

                  )}

                </strong>

              </div>

              <div>

                <span>

                  COMPARISON

                </span>

                <strong>

                  {getVersionLabel(

                    oldVersion

                  )}

                  {" → "}

                  {getVersionLabel(

                    newVersion

                  )}

                </strong>

              </div>

            </div>

          )}

        </section>

        {error && (

          <section className="dashboard-card">

            <div className="empty-analysis">

              {error}

            </div>

          </section>

        )}

        {/* ======================================================

            DOCUMENT VIEWER

        ====================================================== */}

        {oldVersion &&

          newVersion && (

            <section className="dashboard-card">

              <CardHeading

                kicker="DOCUMENTS"

                title="Policy Documents"

                meta="Uploaded versions"

              />

              <div className="version-summary-grid">

                <div className="version-summary old">

                  <span>

                    PREVIOUS VERSION

                  </span>

                  <strong>

                    {getVersionLabel(

                      oldVersion

                    )}

                  </strong>

                  <small>

                    Effective:{" "}

                    {getEffectiveDate(

                      oldVersion

                    )}

                  </small>

                  {documentStatus.old ? (

                    <button

                      className="primary-button"

                      onClick={() =>

                        viewPolicyDocument(

                          oldVersion.version_number

                        )

                      }

                      style={{

                        marginTop: "12px",

                      }}

                    >

                      View Document

                    </button>

                  ) : (

                    <small

                      style={{

                        marginTop: "12px",

                      }}

                    >

                      Document not uploaded

                    </small>

                  )}

                </div>

                <div className="version-summary new">

                  <span>

                    NEW VERSION

                  </span>

                  <strong>

                    {getVersionLabel(

                      newVersion

                    )}

                  </strong>

                  <small>

                    Effective:{" "}

                    {getEffectiveDate(

                      newVersion

                    )}

                  </small>

                  {documentStatus.new ? (

                    <button

                      className="primary-button"

                      onClick={() =>

                        viewPolicyDocument(

                          newVersion.version_number

                        )

                      }

                      style={{

                        marginTop: "12px",

                      }}

                    >

                      View Document

                    </button>

                  ) : (

                    <small

                      style={{

                        marginTop: "12px",

                      }}

                    >

                      Document not uploaded

                    </small>

                  )}

                </div>

              </div>

            </section>

          )}

        {/* ======================================================

            CHANGE RESULTS

        ====================================================== */}

        <section className="dashboard-card">

          <CardHeading

            kicker="CHANGE DETECTION"

            title="Changes Between Versions"

            meta={

              oldVersion &&

              newVersion

                ? `${getVersionLabel(

                    oldVersion

                  )} → ${getVersionLabel(

                    newVersion

                  )}`

                : "Select two versions"

            }

          />

          {!oldVersion ||

          !newVersion ? (

            <EmptyState text="Select a previous version and a new version to view the detected changes." />

          ) : loadingChanges ? (

            <EmptyState text="Change Engine is comparing the selected policy versions..." />

          ) : !changeResult ? (

            <EmptyState text="No comparison result is available for the selected versions." />

          ) : (

            <div className="change-result">

              {/* VERSION INFORMATION */}

              <div className="version-summary-grid">

                <div className="version-summary old">

                  <span>

                    PREVIOUS VERSION

                  </span>

                  <strong>

                    {comparison?.old_version

                      ? `V${comparison.old_version.version_number}`

                      : getVersionLabel(

                          oldVersion

                        )}

                  </strong>

                  <small>

                    Effective:{" "}

                    {comparison?.old_version

                      ?.effective_date ||

                      getEffectiveDate(

                        oldVersion

                      )}

                  </small>

                  <small>

                    Document:{" "}

                    {comparison?.old_version

                      ?.file_name ||

                      documentStatus.old

                        ?.file_name ||

                      "Not available"}

                  </small>

                </div>

                <div className="version-summary new">

                  <span>

                    NEW VERSION

                  </span>

                  <strong>

                    {comparison?.new_version

                      ? `V${comparison.new_version.version_number}`

                      : getVersionLabel(

                          newVersion

                        )}

                  </strong>

                  <small>

                    Effective:{" "}

                    {comparison?.new_version

                      ?.effective_date ||

                      getEffectiveDate(

                        newVersion

                      )}

                  </small>

                  <small>

                    Document:{" "}

                    {comparison?.new_version

                      ?.file_name ||

                      documentStatus.new

                        ?.file_name ||

                      "Not available"}

                  </small>

                </div>

              </div>

              {/* CHANGE SUMMARY */}

              {summary && (

                <div className="version-summary-grid">

                  <div className="version-summary">

                    <span>

                      TOTAL SECTIONS

                    </span>

                    <strong>

                      {summary.total_sections}

                    </strong>

                    <small>

                      Sections compared

                    </small>

                  </div>

                  <div className="version-summary">

                    <span>

                      CHANGED SECTIONS

                    </span>

                    <strong>

                      {summary.changed_sections}

                    </strong>

                    <small>

                      {

                        summary.change_percentage

                      }% changed

                    </small>

                  </div>

                  <div className="version-summary">

                    <span>

                      MODIFIED

                    </span>

                    <strong>

                      {summary.modified}

                    </strong>

                    <small>

                      Modified sections

                    </small>

                  </div>

                  <div className="version-summary">

                    <span>

                      UNCHANGED

                    </span>

                    <strong>

                      {summary.unchanged}

                    </strong>

                    <small>

                      Unchanged sections

                    </small>

                  </div>

                </div>

              )}

              {/* ADDED */}

              {renderChangeGroup(

                "Added Sections",

                addedChanges,

                "added"

              )}

              {/* REMOVED */}

              {renderChangeGroup(

                "Removed Sections",

                removedChanges,

                "removed"

              )}

              {/* MODIFIED */}

              {renderChangeGroup(

                "Modified Sections",

                modifiedChanges,

                "modified"

              )}

              {/* UNCHANGED */}

              {renderChangeGroup(

                "Unchanged Sections",

                unchangedChanges,

                "unchanged"

              )}

            </div>

          )}

        </section>

      </>

    );

  };

  // ============================================================

  // DEPENDENCIES

  // ============================================================

  const renderDependencies = () => {

    return (

      <>

        <PageHeader

          title="Dependencies"

          subtitle="Review policies that depend on the selected policy."

          backendStatus={

            backendStatus

          }

        />

        <section className="dashboard-card">

          <CardHeading

            kicker="POLICY RELATIONSHIPS"

            title="Dependency Analysis"

            meta={

              loadingDependencies

                ? "Loading..."

                : `${dependencies.length} relationships`

            }

          />

          <div className="dependency-selector">

            <div className="selector-field">

              <label>

                POLICY

              </label>

              <select

                value={

                  selectedPolicyId

                }

                onChange={(event) =>

                  setSelectedPolicyId(

                    event.target

                      .value

                  )

                }

              >

                <option value="">

                  Select policy

                </option>

                {policies.map(

                  (policy) => (

                    <option

                      key={

                        policy.policy_id

                      }

                      value={

                        policy.policy_id

                      }

                    >

                      {

                        policy.policy_id

                      }

                      {" · "}

                      {getPolicyName(

                        policy

                      )}

                    </option>

                  )

                )}

              </select>

            </div>

          </div>

          {dependencies.length ===

          0 ? (

            <EmptyState

              text={

                selectedPolicyId

                  ? "No dependency relationships are currently recorded for this policy."

                  : "Select a policy to view its dependencies."

              }

            />

          ) : (

            <div className="dependency-table">

              <div className="dependency-table-header">

                <span>

                  SOURCE POLICY

                </span>

                <span>

                  RELATIONSHIP

                </span>

                <span>

                  DEPENDENT POLICY

                </span>

                <span>

                  STATUS

                </span>

              </div>

              {dependencies.map(

                (

                  dependency,

                  index

                ) => {

                  const targetPolicy =

                    getTargetPolicy(

                      dependency

                    );

                  return (

                    <div

                      className="dependency-table-row"

                      key={`${getTargetPolicyId(

                        dependency

                      )}-${index}`}

                    >

                      <div>

                        <strong>

                          {selectedPolicy

                            ? getPolicyName(

                                selectedPolicy

                              )

                            : selectedPolicyId}

                        </strong>

                        <small>

                          {

                            selectedPolicyId

                          }

                        </small>

                      </div>

                      <span>

                        {dependency.relationship_type ||

                          dependency.relation_type ||

                          dependency.type ||

                          "DEPENDENCY"}

                      </span>

                      <div>

                        <strong>

                          {targetPolicy

                            ? getPolicyName(

                                targetPolicy

                              )

                            : getTargetPolicyId(

                                dependency

                              )}

                        </strong>

                        <small>

                          {getTargetPolicyId(

                            dependency

                          )}

                        </small>

                      </div>

                      <span className="status-pill">

                        REVIEW

                      </span>

                    </div>

                  );

                }

              )}

            </div>

          )}

        </section>

      </>

    );

  };

  // ============================================================
  // ============================================================
  // EVIDENCE FOR SELECTED POLICY AND DEPENDENT POLICIES
  // ============================================================

  const loadPolicyEvidence = async () => {
    if (!selectedPolicyId) {
      setEvidenceResult(null);
      setEvidenceError("Select a policy in Policy Changes or Dependencies first.");
      return;
    }

    try {
      setLoadingEvidence(true);
      setEvidenceError("");

      const dependencyResponse = await api.get(
        `/policies/${encodeURIComponent(selectedPolicyId)}/dependencies`
      );
      const dependentPolicies = Array.isArray(dependencyResponse.data)
        ? dependencyResponse.data
        : [];

      const dependentIds = dependentPolicies
        .map((dependency) =>
          dependency.target_policy_id ||
          dependency.dependent_policy_id ||
          dependency.policy_id ||
          ""
        )
        .filter(Boolean);

      const uniqueIds = [...new Set([selectedPolicyId, ...dependentIds])];

      // Use the existing policy-version and Change Engine endpoints to obtain actual
      // old/new text for the selected policy and each dependent policy.
      const policyEvidence = await Promise.all(
        uniqueIds.map(async (policyId) => {
          const policy = policies.find((item) => item.policy_id === policyId);
          const isSelected = policyId === selectedPolicyId;
          const relationships = dependentPolicies.filter((dependency) =>
            (dependency.target_policy_id ||
              dependency.dependent_policy_id ||
              dependency.policy_id ||
              "") === policyId
          );

          try {
            const versionsResponse = await api.get(
              `/policies/${encodeURIComponent(policyId)}/versions`
            );
            const policyVersions = Array.isArray(versionsResponse.data)
              ? [...versionsResponse.data].sort(
                  (a, b) =>
                    Number(a.version_number || 0) -
                    Number(b.version_number || 0)
                )
              : [];

            let oldVersionForPolicy = null;
            let newVersionForPolicy = null;
            let changedSections = [];

            if (isSelected && changeResult) {
              oldVersionForPolicy =
                changeResult.comparison?.old_version || oldVersion || null;
              newVersionForPolicy =
                changeResult.comparison?.new_version || newVersion || null;
              changedSections = Array.isArray(changeResult.changes)
                ? changeResult.changes.filter(
                    (change) => change.change_type !== "unchanged"
                  )
                : [];
            } else if (policyVersions.length >= 2) {
              const previous = policyVersions[policyVersions.length - 2];
              const latest = policyVersions[policyVersions.length - 1];

              const comparisonResponse = await api.get(
                `/change-engine/policies/${encodeURIComponent(policyId)}/compare`,
                {
                  params: {
                    old_version: Number(previous.version_number),
                    new_version: Number(latest.version_number),
                  },
                }
              );

              oldVersionForPolicy =
                comparisonResponse.data?.comparison?.old_version || previous;
              newVersionForPolicy =
                comparisonResponse.data?.comparison?.new_version || latest;
              changedSections = Array.isArray(comparisonResponse.data?.changes)
                ? comparisonResponse.data.changes.filter(
                    (change) => change.change_type !== "unchanged"
                  )
                : [];
            } else if (policyVersions.length === 1) {
              newVersionForPolicy = policyVersions[0];
            }

            return {
              policy_id: policyId,
              policy_name: policy ? getPolicyName(policy) : policyId,
              is_selected_policy: isSelected,
              relationships,
              old_version: oldVersionForPolicy,
              new_version: newVersionForPolicy,
              changed_sections: changedSections,
              evidence_status:
                policyVersions.length >= 2 || (isSelected && changeResult)
                  ? "loaded"
                  : "insufficient_versions",
            };
          } catch (policyError) {
            console.warn(`Could not load evidence for ${policyId}:`, policyError);
            return {
              policy_id: policyId,
              policy_name: policy ? getPolicyName(policy) : policyId,
              is_selected_policy: isSelected,
              relationships,
              old_version: null,
              new_version: null,
              changed_sections: [],
              evidence_status: "unavailable",
            };
          }
        })
      );

      const selectedEvidence = policyEvidence.find(
        (item) => item.policy_id === selectedPolicyId
      );

      setEvidenceResult({
        selected_policy_id: selectedPolicyId,
        selected_policy_name: getPolicyName(
          policies.find((item) => item.policy_id === selectedPolicyId)
        ),
        old_version: selectedEvidence?.old_version || oldVersion || null,
        new_version: selectedEvidence?.new_version || newVersion || null,
        changed_sections: selectedEvidence?.changed_sections || [],
        dependent_policy_ids: dependentIds,
        dependency_relationships: dependentPolicies,
        policies: policyEvidence,
      });
    } catch (err) {
      console.error("Failed to load policy evidence:", err);
      setEvidenceResult(null);
      setEvidenceError(
        err.response?.data?.detail ||
          "Could not load evidence for the selected policy and its dependencies."
      );
    } finally {
      setLoadingEvidence(false);
    }
  };

  const formatScore = (value) => {
    const score = Number(value);
    return Number.isFinite(score) ? `${(score * 100).toFixed(1)}%` : "—";
  };

  useEffect(() => {
    if (activeSection === "evidence" && selectedPolicyId) {
      loadPolicyEvidence();
    }
    // Refresh when the selected policy or version comparison changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSection, selectedPolicyId, selectedOldVersion, selectedNewVersion, changeResult]);

  // EVIDENCE

  // ============================================================

  const renderEvidence = () => {
    const result = evidenceResult;
    const relationships = Array.isArray(result?.dependency_relationships)
      ? result.dependency_relationships
      : [];
    const relatedPolicies = Array.isArray(result?.policies)
      ? result.policies
      : [];

    const getRelationshipType = (relationship) =>
      relationship.relationship_type ||
      relationship.relation_type ||
      relationship.type ||
      "Dependency";

    const getRelationshipReason = (relationship) =>
      relationship.description ||
      relationship.reason ||
      relationship.rationale ||
      relationship.relationship_description ||
      "";

    const getTargetPolicyId = (relationship) =>
      relationship.target_policy_id ||
      relationship.dependent_policy_id ||
      relationship.policy_id ||
      "";

    return (
      <>
        <PageHeader
          title="Evidence & Dependency Analysis"
          subtitle="Review dependent policies, why they are connected, and the policy-version evidence supporting further review."
          backendStatus={backendStatus}
        />

        <section className="dashboard-card">
          <CardHeading
            kicker="ANALYSIS CONTEXT"
            title={result?.selected_policy_name || getPolicyName(selectedPolicy)}
            meta={selectedPolicyId || "No policy selected"}
          />

          {!selectedPolicyId ? (
            <EmptyState text="Select a policy in Policy Changes or Dependencies first. Its connected policies and supporting evidence will appear here." />
          ) : loadingEvidence ? (
            <EmptyState text="Loading dependent policies and supporting evidence..." />
          ) : evidenceError ? (
            <div className="empty-analysis" role="alert">{evidenceError}</div>
          ) : (
            <>
              <div className="version-summary-grid">
                <div className="version-summary old">
                  <span>PREVIOUS VERSION</span>
                  <strong>
                    {result?.old_version?.version_number
                      ? `V${result.old_version.version_number}`
                      : getVersionLabel(oldVersion)}
                  </strong>
                  <small>{result?.old_version?.effective_date || getEffectiveDate(oldVersion)}</small>
                </div>
                <div className="version-summary new">
                  <span>CURRENT VERSION</span>
                  <strong>
                    {result?.new_version?.version_number
                      ? `V${result.new_version.version_number}`
                      : getVersionLabel(newVersion)}
                  </strong>
                  <small>{result?.new_version?.effective_date || getEffectiveDate(newVersion)}</small>
                </div>
              </div>
              <div className="version-summary-grid" style={{ marginTop: 16 }}>
                <div className="version-summary">
                  <span>RECORDED RELATIONSHIPS</span>
                  <strong>{relationships.length}</strong>
                  <small>Dependency links returned by the backend</small>
                </div>
                <div className="version-summary">
                  <span>CONNECTED POLICIES</span>
                  <strong>{relatedPolicies.filter((policy) => !policy.is_selected_policy).length}</strong>
                  <small>Policies retrieved for evidence review</small>
                </div>
              </div>
            </>
          )}
        </section>

        {!loadingEvidence && !evidenceError && selectedPolicyId && (
          <section className="dashboard-card">
            <CardHeading
              kicker="DEPENDENCY ANALYSIS"
              title="Dependent Policies — Why Are They Connected?"
              meta={`${relationships.length} relationships`}
            />
            {relationships.length === 0 ? (
              <EmptyState text="No dependency relationships were returned for this policy. The current data does not establish any dependent policies." />
            ) : (
              <div className="evidence-grid">
                {relationships.map((relationship, index) => {
                  const targetId = getTargetPolicyId(relationship);
                  const targetPolicy = policies.find((policy) => policy.policy_id === targetId);
                  const targetEvidence = relatedPolicies.find((policy) => policy.policy_id === targetId);
                  const relationshipType = getRelationshipType(relationship);
                  const reason = getRelationshipReason(relationship);

                  return (
                    <article className="evidence-item" key={`${targetId || "dependency"}-${index}`}>
                      <span className="evidence-source">
                        {String(relationshipType).replaceAll("_", " ").toUpperCase()}
                      </span>
                      <strong>
                        {targetPolicy ? getPolicyName(targetPolicy) : targetEvidence?.policy_name || targetId || "Related policy"}
                      </strong>
                      <p><b>Policy ID:</b> {targetId || "Not provided"}</p>
                      <p><b>Connected to:</b> {result?.selected_policy_name || getPolicyName(selectedPolicy)}</p>
                      <p><b>Relationship type:</b> {relationshipType}</p>

                      <div style={{ marginTop: 12 }}>
                        <b>Why is this policy listed?</b>
                        <p style={{ lineHeight: 1.65 }}>
                          {reason || `The stored dependency data links this policy to ${result?.selected_policy_name || getPolicyName(selectedPolicy)} through the relationship "${relationshipType}". The relationship record does not contain a more detailed rationale, so the policy text should be reviewed before confirming impact.`}
                        </p>
                      </div>

                      <div style={{ marginTop: 12 }}>
                        <b>Supporting policy evidence</b>
                        {!targetEvidence ? (
                          <p>Version evidence has not been retrieved for this policy.</p>
                        ) : targetEvidence.evidence_status === "unavailable" ? (
                          <p>The policy was found in the dependency data, but its version comparison could not be retrieved.</p>
                        ) : targetEvidence.evidence_status === "insufficient_versions" ? (
                          <p>There are not enough policy versions to compare this policy's text.</p>
                        ) : !(targetEvidence.changed_sections || []).length ? (
                          <p>No changed sections were returned for this policy's latest version comparison. This alone does not prove the policy is unaffected.</p>
                        ) : (
                          <details style={{ marginTop: 8 }}>
                            <summary style={{ cursor: "pointer", fontWeight: 600 }}>
                              View changed-section evidence ({targetEvidence.changed_sections.length})
                            </summary>
                            <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
                              {targetEvidence.changed_sections.map((change, changeIndex) => (
                                <div key={`${targetId}-${change.section || "section"}-${changeIndex}`} style={{ padding: 12, border: "1px solid rgba(128,128,128,0.25)", borderRadius: 8 }}>
                                  <strong>{change.section || `Changed section ${changeIndex + 1}`}</strong>
                                  <p><b>Change type:</b> {change.change_type || "Changed"}</p>
                                  {change.old_text && (
                                    <div style={{ marginTop: 8 }}>
                                      <b>Previous version</b>
                                      <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", lineHeight: 1.6 }}>{change.old_text}</p>
                                    </div>
                                  )}
                                  {change.new_text && (
                                    <div style={{ marginTop: 8 }}>
                                      <b>New version</b>
                                      <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", lineHeight: 1.6 }}>{change.new_text}</p>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>

                      <div style={{ marginTop: 12 }}>
                        <b>Recommended analyst action</b>
                        <p style={{ lineHeight: 1.65 }}>
                          Review the relationship and cited policy text, then determine whether the regulatory requirement applies and whether a revision is necessary. A dependency alone is not proof of regulatory impact.
                        </p>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {!loadingEvidence && !evidenceError && selectedPolicyId && (
          <section className="dashboard-card">
            <CardHeading
              kicker="PRIMARY POLICY EVIDENCE"
              title="Changes in the Selected Policy"
              meta={`${result?.changed_sections?.length || 0} changed sections`}
            />
            {!(result?.changed_sections || []).length ? (
              <EmptyState text="No changed-section evidence is available for the selected comparison. Select and compare versions in Policy Changes first." />
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {result.changed_sections.map((change, index) => (
                  <article className="evidence-item" key={`${change.section || "section"}-${index}`}>
                    <span className="evidence-source">{String(change.change_type || "changed").toUpperCase()}</span>
                    <strong>{change.section || `Changed section ${index + 1}`}</strong>
                    {change.old_text && (
                      <div style={{ marginTop: 10 }}>
                        <b>Previous version</b>
                        <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", lineHeight: 1.6 }}>{change.old_text}</p>
                      </div>
                    )}
                    {change.new_text && (
                      <div style={{ marginTop: 10 }}>
                        <b>New version</b>
                        <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", lineHeight: 1.6 }}>{change.new_text}</p>
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}
          </section>
        )}

        <section className="dashboard-card explanation-card">
          <div className="explanation-icon">i</div>
          <div>
            <span className="card-kicker">EVIDENCE INTERPRETATION</span>
            <h2>How to interpret these results</h2>
            <p style={{ lineHeight: 1.7 }}>
              Dependency records explain how policies are connected. Policy-version comparisons show the actual text differences retrieved by the Change Engine. These are supporting signals for analyst review, not automatic proof of regulatory impact.
            </p>
            <p style={{ lineHeight: 1.7 }}>
              To confirm impact, the relevant regulatory passage must be matched against the applicable policy clause and the dependency path. Where the database does not store a relationship rationale or regulatory passage, the dashboard explicitly identifies that evidence gap instead of inventing an explanation.
            </p>
          </div>
        </section>
      </>
    );
  };


  // MAIN RENDER

  // ============================================================

  return (

    <div className="dashboard-page">

      {/* ======================================================

          SIDEBAR

      ====================================================== */}

      <aside className="dashboard-sidebar">

        <div>

          <div className="dashboard-brand">

            <div className="dashboard-brand-mark">

              PL

            </div>

            <div>

              <h2>

                PolicyLens

              </h2>

              <span>

                Regulatory Intelligence

              </span>

            </div>

          </div>

          <div className="dashboard-divider" />

          <div className="dashboard-section-label">

            ANALYSIS

          </div>

          <nav className="dashboard-nav">

            <button

              className={`dashboard-nav-item ${

                activeSection ===

                "dashboard"

                  ? "active"

                  : ""

              }`}

              onClick={() =>

                changeSection(

                  "dashboard"

                )

              }

            >

              <span>⌂</span>

              Dashboard

            </button>

            <button

              className={`dashboard-nav-item ${

                activeSection ===

                "changes"

                  ? "active"

                  : ""

              }`}

              onClick={() =>

                changeSection(

                  "changes"

                )

              }

            >

              <span>▣</span>

              Policy Changes

            </button>

            <button

              className={`dashboard-nav-item ${

                activeSection ===

                "dependencies"

                  ? "active"

                  : ""

              }`}

              onClick={() =>

                changeSection(

                  "dependencies"

                )

              }

            >

              <span>◎</span>

              Dependencies

            </button>

            <button

              className={`dashboard-nav-item ${

                activeSection ===

                "evidence"

                  ? "active"

                  : ""

              }`}

              onClick={() =>

                changeSection(

                  "evidence"

                )

              }

            >

              <span>◌</span>

              Evidence

            </button>

          </nav>

        </div>

        <div className="dashboard-sidebar-bottom">

          <div className="analyst-profile">

            <div className="profile-circle">

              PA

            </div>

            <div>

              <strong>

                Policy Analyst

              </strong>

              <span>

                Standard Access

              </span>

            </div>

          </div>

          <button

            className="back-role-button"

            onClick={() =>

              navigate("/roles")

            }

          >

            ← Switch Workspace

          </button>

        </div>

      </aside>

      {/* ======================================================

          MAIN

      ====================================================== */}

      <main className="dashboard-main">

        {activeSection ===

          "dashboard" &&

          renderDashboard()}

        {activeSection ===

          "changes" &&

          renderPolicyChanges()}

        {activeSection ===

          "dependencies" &&

          renderDependencies()}

        {activeSection ===

          "evidence" &&

          renderEvidence()}

        <footer className="dashboard-footer">

          <span>

            PolicyLens · Regulatory Intelligence Platform

          </span>

          <span>

            Analyst Workspace

          </span>

        </footer>

      </main>

    </div>

  );

}

// ============================================================

// REUSABLE COMPONENTS

// ============================================================

function PageHeader({

  title,

  subtitle,

  backendStatus,

}) {

  return (

    <header className="dashboard-header">

      <div>

        <div className="dashboard-eyebrow">

          REGULATORY INTELLIGENCE

        </div>

        <h1>{title}</h1>

        <p>{subtitle}</p>

      </div>

      <div

        className={`engine-status ${

          backendStatus === "ok" ||

          backendStatus === "Online"

            ? "engine-online"

            : backendStatus ===

              "Offline"

            ? "engine-offline"

            : ""

        }`}

      >

        <span className="engine-dot" />

        Backend: {backendStatus}

      </div>

    </header>

  );

}

function SummaryCard({

  label,

  value,

  detail,

}) {

  return (

    <div className="summary-card">

      <span>{label}</span>

      <strong>{value}</strong>

      <small>{detail}</small>

    </div>

  );

}

function CardHeading({

  kicker,

  title,

  meta,

}) {

  return (

    <div className="card-heading">

      <div>

        <span className="card-kicker">

          {kicker}

        </span>

        <h2>{title}</h2>

      </div>

      {meta && (

        <span className="card-meta">

          {meta}

        </span>

      )}

    </div>

  );

}

function EmptyState({

  text,

}) {

  return (

    <div className="empty-analysis">

      {text}

    </div>

  );

}

export default PolicyDashboard;
