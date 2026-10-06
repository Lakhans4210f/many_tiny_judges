import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = "http://127.0.0.1:5000";

const initialJudges = [
  {
    key: "Domain Expert",
    icon: "DE",
    state: "idle",
    text: ""
  },
  {
    key: "Adversarial Skeptic",
    icon: "AS",
    state: "idle",
    text: ""
  },
  {
    key: "Fact Verifier",
    icon: "FV",
    state: "idle",
    text: ""
  }
];

function App() {
  const [question, setQuestion] = useState("");
  const [judges, setJudges] = useState(initialJudges);
  const [arbiter, setArbiter] = useState({
    state: "idle",
    text: ""
  });
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    if (!question.trim() || busy) return;

    setBusy(true);
    setError("");
    setResult(null);
    setSelected(null);

    setJudges(
      initialJudges.map((judge) => ({
        ...judge,
        state: "waiting",
        text: ""
      }))
    );

    setArbiter({
      state: "waiting",
      text: ""
    });

    try {
      console.log("Sending question to backend...");

      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          question: question.trim()
        })
      });

      const data = await response.json();

      console.log("Backend response:", data);

      if (!response.ok) {
        throw new Error(
          data.error || `Server error: ${response.status}`
        );
      }

      /*
       * ---------------------------------------------------------
       * UPDATE JUDGE STATUS
       * ---------------------------------------------------------
       *
       * A judge is considered complete only when the backend
       * actually returned an analysis for that role.
       *
       * Missing judges are shown as "Unavailable", not as a
       * system-wide failure.
       */

      const returnedJudges = initialJudges.map((judge) => {
        const found = (data.judges || []).find(
          (item) =>
            String(item.role || "").trim().toLowerCase() ===
            judge.key.trim().toLowerCase()
        );

        if (found) {
          return {
            ...judge,
            state: "complete",
            text:
              found.assessment ||
              found.text ||
              "Analysis completed."
          };
        }

        return {
          ...judge,
          state: "unavailable",
          text:
            "This judge was unavailable for this analysis. Other judges continued."
        };
      });

      setJudges(returnedJudges);

      /*
       * ---------------------------------------------------------
       * CHIEF ARBITER
       * ---------------------------------------------------------
       */

      if (data.verdict) {
        const verdictText = [
          data.verdict.final_answer
            ? `FINAL ANSWER:\n${data.verdict.final_answer}`
            : "",
          data.verdict.resolved_discrepancies
            ? `RESOLVED DISCREPANCIES:\n${data.verdict.resolved_discrepancies}`
            : "",
          data.verdict.key_trap_avoided
            ? `KEY TRAP AVOIDED:\n${data.verdict.key_trap_avoided}`
            : ""
        ]
          .filter(Boolean)
          .join("\n\n");

        setArbiter({
          state: "complete",
          text: verdictText || "Chief Arbiter completed."
        });

        setResult(data.verdict);
      } else {
        setArbiter({
          state: "failed",
          text: "No final verdict was returned."
        });
      }

    } catch (err) {
      console.error("Analysis error:", err);

      setError(
        err.message ||
          "Unable to connect to the Many Tiny Judges backend."
      );

      /*
       * Only mark judges as failed if the entire request failed.
       * If we already received a successful response, their
       * actual states are preserved.
       */
      setJudges((previous) =>
        previous.map((judge) => ({
          ...judge,
          state:
            judge.state === "complete"
              ? "complete"
              : judge.state === "unavailable"
              ? "unavailable"
              : "failed"
        }))
      );

      setArbiter((previous) => ({
        ...previous,
        state:
          previous.state === "complete"
            ? "complete"
            : "failed",
        text:
          previous.text ||
          "Analysis did not complete."
      }));

    } finally {
      setBusy(false);
    }
  }

  function clearAll() {
    if (busy) return;

    setQuestion("");
    setJudges(initialJudges);

    setArbiter({
      state: "idle",
      text: ""
    });

    setResult(null);
    setSelected(null);
    setError("");
  }

  function loadExample() {
    setQuestion(
      "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?"
    );
  }

  return (
    <div className="desktop">
      <div className="window">

        {/* TITLE BAR */}
        <header className="titlebar">
          <div className="titlebar-left">
            <span className="app-mark">MT</span>
            <span>Many Tiny Judges</span>
          </div>

          <div className="window-buttons">
            <button>_</button>
            <button>□</button>
            <button>×</button>
          </div>
        </header>

        {/* MENU */}
        <nav className="menubar">
          <span>File</span>
          <span>View</span>
          <span>Judges</span>
          <span>Help</span>
        </nav>

        <main className="content">

          {/* QUESTION */}
          <section className="panel">
            <div className="panel-title">
              Reasoning Problem
            </div>

            <div className="panel-body">
              <label htmlFor="question">
                Enter a problem for the judges to analyze:
              </label>

              <textarea
                id="question"
                value={question}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
                disabled={busy}
                placeholder="Type a math, logic, fact-checking, or reasoning problem..."
              />

              <div className="button-row">
                <button
                  className="classic-button primary"
                  onClick={analyze}
                  disabled={!question.trim() || busy}
                >
                  {busy ? "Analyzing..." : "Analyze Problem"}
                </button>

                <button
                  className="classic-button"
                  onClick={clearAll}
                  disabled={busy}
                >
                  Clear
                </button>

                <button
                  className="classic-button"
                  onClick={loadExample}
                  disabled={busy}
                >
                  Example
                </button>
              </div>
            </div>
          </section>

          {/* ERROR */}
          {error && (
            <section className="error-box">
              <strong>System message:</strong>{" "}
              {error}

              <div className="error-note">
                Make sure the Python backend is running on
                port 5000.
              </div>
            </section>
          )}

          {/* JUDGES */}
          <section className="panel">
            <div className="panel-title">
              Judge Status
            </div>

            <div className="panel-body judge-grid">

              {judges.map((judge) => (
                <JudgeCard
                  key={judge.key}
                  judge={judge}
                  selected={selected === judge.key}
                  onClick={() =>
                    judge.text &&
                    setSelected(judge.key)
                  }
                />
              ))}

              <JudgeCard
                judge={{
                  key: "Chief Arbiter",
                  icon: "CA",
                  state: arbiter.state,
                  text: arbiter.text
                }}
                selected={selected === "Chief Arbiter"}
                onClick={() =>
                  arbiter.text &&
                  setSelected("Chief Arbiter")
                }
              />

            </div>
          </section>

          {/* ANALYSIS */}
          {selected && (
            <section className="panel">
              <div className="panel-title">
                {selected} — Analysis

                <button
                  className="close-analysis"
                  onClick={() => setSelected(null)}
                >
                  ×
                </button>
              </div>

              <div className="panel-body analysis-text">
                {selected === "Chief Arbiter"
                  ? arbiter.text
                  : judges.find(
                      (judge) =>
                        judge.key === selected
                    )?.text}
              </div>
            </section>
          )}

          {/* FINAL VERDICT */}
          {result && (
            <section className="panel verdict-panel">

              <div className="panel-title">
                Final Verdict
              </div>

              <div className="panel-body">

                <div className="verdict-label">
                  ANSWER
                </div>

                <div className="answer">
                  {result.final_answer}
                </div>

                <div className="verdict-label">
                  RESOLVED DISCREPANCIES
                </div>

                <p>
                  {result.resolved_discrepancies ||
                    "No discrepancies reported."}
                </p>

                <div className="verdict-label">
                  KEY TRAP AVOIDED
                </div>

                <p>
                  {result.key_trap_avoided ||
                    "No specific trap reported."}
                </p>

              </div>
            </section>
          )}

        </main>

        {/* STATUS BAR */}
        <footer className="statusbar">
          <span>Gemma 4</span>
          <span>3 Judges</span>
          <span>Chief Arbiter</span>

          <span className="status-ready">
            {busy ? "Working..." : "Ready"}
          </span>
        </footer>

      </div>
    </div>
  );
}


function JudgeCard({
  judge,
  selected,
  onClick
}) {

  const labels = {
    idle: "Ready",
    waiting: "Waiting",
    running: "Running",
    complete: "Complete",
    unavailable: "Unavailable",
    failed: "Failed"
  };

  return (
    <button
      className={`judge-card ${
        selected ? "selected" : ""
      }`}
      onClick={onClick}
      disabled={!judge.text}
    >

      <div className="judge-icon">
        {judge.icon}
      </div>

      <div className="judge-info">

        <strong>
          {judge.key}
        </strong>

        <span
          className={`state state-${judge.state}`}
        >
          <i />
          {labels[judge.state] || "Ready"}
        </span>

      </div>

    </button>
  );
}


createRoot(
  document.getElementById("root")
).render(<App />);