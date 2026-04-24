"""Design preview — shows 3 sidebar variations side by side as HTML mockups.
Run with:  streamlit run slideqa/design_preview.py --server.port 8502
"""
import streamlit as st

st.set_page_config(page_title="Design Preview", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1.5rem !important; }
h1 { font-size: 1.1rem !important; font-weight: 700; letter-spacing: -0.01em; }
h3 { font-size: 0.82rem !important; font-weight: 700; letter-spacing: 0.06em;
     text-transform: uppercase; color: #64748b; margin-bottom: 0.75rem; }
.var-label { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
             text-transform: uppercase; color: #94a3b8; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("# Sidebar — 3 Variations")
st.caption("Pick the one you want to build from. The main content area stays the same across all.")
st.markdown("---")

colA, colB, colC = st.columns(3, gap="large")

# ── Variation A: Dark banner header ─────────────────────────────────────────
with colA:
    st.markdown('<p class="var-label">Variation A — Dark banner</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="width:100%;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
            overflow:hidden;font-family:system-ui,sans-serif;">

  <!-- Banner -->
  <div style="background:#1e293b;padding:18px 20px 14px;">
    <div style="color:#f1f5f9;font-size:1.05rem;font-weight:700;letter-spacing:-0.01em;">
      SlideQA
    </div>
    <div style="color:#94a3b8;font-size:0.72rem;margin-top:3px;line-height:1.4;">
      Multimodal QA benchmark<br>across university lecture slides
    </div>
  </div>

  <!-- Body -->
  <div style="padding:16px 18px;display:flex;flex-direction:column;gap:14px;">

    <div>
      <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.07em;
                  text-transform:uppercase;color:#94a3b8;margin-bottom:5px;">Course</div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;">
        CS 288 — Berkeley NLP
        <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
    </div>

    <div style="border-top:1px solid #e2e8f0;padding-top:14px;">
      <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.07em;
                  text-transform:uppercase;color:#94a3b8;margin-bottom:8px;">Filter</div>
      <div style="font-size:0.75rem;color:#475569;margin-bottom:4px;">Category</div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        All categories
        <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
      <div style="font-size:0.75rem;color:#475569;margin-bottom:4px;">Difficulty</div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;">
        All
        <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
    </div>

    <div style="border-top:1px solid #e2e8f0;padding-top:12px;
                font-size:0.72rem;color:#94a3b8;">
      150 of 150 questions
    </div>

  </div>
</div>
""", unsafe_allow_html=True)

# ── Variation B: White + color accent strip ──────────────────────────────────
with colB:
    st.markdown('<p class="var-label">Variation B — Color accent strip</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="width:100%;background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;
            overflow:hidden;font-family:system-ui,sans-serif;
            display:flex;flex-direction:row;">

  <!-- Left accent strip -->
  <div style="width:4px;background:linear-gradient(180deg,#6366f1,#a78bfa);flex-shrink:0;"></div>

  <!-- Content -->
  <div style="padding:18px 16px;flex:1;display:flex;flex-direction:column;gap:14px;">

    <div>
      <div style="font-size:1.05rem;font-weight:800;letter-spacing:-0.02em;color:#0f172a;">
        SlideQA
      </div>
      <div style="font-size:0.72rem;color:#94a3b8;margin-top:2px;">
        Multimodal benchmark · 3 courses · 450 questions
      </div>
    </div>

    <div style="border-top:1px solid #f1f5f9;padding-top:12px;">
      <div style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;
                  text-transform:uppercase;color:#6366f1;margin-bottom:6px;">Course</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;">
        CS 288 — Berkeley NLP
        <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
    </div>

    <div>
      <div style="font-size:0.7rem;font-weight:600;letter-spacing:0.06em;
                  text-transform:uppercase;color:#6366f1;margin-bottom:8px;">Filters</div>

      <!-- Category options with colored dots -->
      <div style="font-size:0.72rem;color:#475569;margin-bottom:5px;">Category</div>
      <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:10px;">
        <div style="display:flex;align-items:center;gap:7px;padding:5px 8px;
                    background:#ede9fe;border-radius:5px;">
          <span style="width:8px;height:8px;border-radius:50%;background:#6366f1;display:inline-block;"></span>
          <span style="font-size:0.78rem;color:#3730a3;font-weight:500;">All categories</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;padding:4px 8px;">
          <span style="width:8px;height:8px;border-radius:50%;background:#4A90D9;display:inline-block;"></span>
          <span style="font-size:0.78rem;color:#64748b;">Text Only</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;padding:4px 8px;">
          <span style="width:8px;height:8px;border-radius:50%;background:#E8A838;display:inline-block;"></span>
          <span style="font-size:0.78rem;color:#64748b;">Image / Diagram</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;padding:4px 8px;">
          <span style="width:8px;height:8px;border-radius:50%;background:#5BAD6F;display:inline-block;"></span>
          <span style="font-size:0.78rem;color:#64748b;">Table</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;padding:4px 8px;">
          <span style="width:8px;height:8px;border-radius:50%;background:#C0544C;display:inline-block;"></span>
          <span style="font-size:0.78rem;color:#64748b;">Chart / Graph</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;padding:4px 8px;">
          <span style="width:8px;height:8px;border-radius:50%;background:#9B6BB5;display:inline-block;"></span>
          <span style="font-size:0.78rem;color:#64748b;">Layout Aware</span>
        </div>
      </div>

      <div style="font-size:0.72rem;color:#475569;margin-bottom:5px;">Difficulty</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;">
        All
        <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
    </div>

    <div style="border-top:1px solid #f1f5f9;padding-top:10px;
                font-size:0.72rem;color:#94a3b8;">
      150 of 150 questions
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Variation C: Card-style grouped sections ─────────────────────────────────
with colC:
    st.markdown('<p class="var-label">Variation C — Card-grouped sections</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="width:100%;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:10px;
            overflow:hidden;font-family:system-ui,sans-serif;padding:14px;
            display:flex;flex-direction:column;gap:10px;">

  <!-- App name -->
  <div style="padding:4px 2px 8px;">
    <div style="font-size:1rem;font-weight:800;letter-spacing:-0.02em;color:#0f172a;">
      SlideQA
    </div>
    <div style="font-size:0.7rem;color:#64748b;margin-top:2px;">
      Multimodal QA benchmark
    </div>
  </div>

  <!-- Course card -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;
              box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.08em;
                text-transform:uppercase;color:#94a3b8;margin-bottom:8px;">Course</div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#0f172a;
                display:flex;justify-content:space-between;align-items:center;">
      CS 288 — Berkeley NLP
      <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
    </div>
  </div>

  <!-- Filter card -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px;
              box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.08em;
                text-transform:uppercase;color:#94a3b8;margin-bottom:10px;">Filter Questions</div>

    <div style="font-size:0.72rem;color:#475569;margin-bottom:4px;">Category</div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#0f172a;
                display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      All categories
      <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
    </div>

    <div style="font-size:0.72rem;color:#475569;margin-bottom:4px;">Difficulty</div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#0f172a;
                display:flex;justify-content:space-between;align-items:center;">
      All
      <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
    </div>
  </div>

  <!-- Count chip -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
              padding:10px 14px;display:flex;align-items:center;gap:10px;
              box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="background:#0f172a;color:#fff;font-size:0.78rem;font-weight:700;
                padding:3px 10px;border-radius:20px;">150</div>
    <div style="font-size:0.72rem;color:#64748b;">of 150 questions</div>
  </div>

</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("# More Variations — Card Direction")
st.caption("All three build on C's card structure, but with different tone and color treatment.")
st.markdown("&nbsp;")

colD, colE, colF = st.columns(3, gap="large")

# ── Variation D: Warm neutral, academic feel ─────────────────────────────────
with colD:
    st.markdown('<p class="var-label">Variation D — Warm neutral / academic</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="width:100%;background:#fafaf9;border:1px solid #e7e5e4;border-radius:10px;
            overflow:hidden;font-family:system-ui,sans-serif;padding:14px;
            display:flex;flex-direction:column;gap:10px;">

  <div style="padding:4px 2px 6px;border-bottom:1px solid #e7e5e4;margin-bottom:2px;">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;
                text-transform:uppercase;color:#a8a29e;margin-bottom:4px;">Research Demo</div>
    <div style="font-size:1.05rem;font-weight:800;letter-spacing:-0.02em;color:#1c1917;">
      SlideQA
    </div>
    <div style="font-size:0.71rem;color:#78716c;margin-top:3px;line-height:1.5;">
      Multimodal QA across<br>university lecture slides
    </div>
  </div>

  <div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;padding:12px 14px;">
    <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#a8a29e;margin-bottom:7px;">Course</div>
    <div style="background:#fafaf9;border:1px solid #e7e5e4;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#1c1917;
                display:flex;justify-content:space-between;align-items:center;">
      CS 288 — Berkeley NLP
      <span style="color:#a8a29e;font-size:0.75rem;">▾</span>
    </div>
  </div>

  <div style="background:#fff;border:1px solid #e7e5e4;border-radius:8px;padding:12px 14px;">
    <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#a8a29e;margin-bottom:10px;">Filter</div>
    <div style="font-size:0.72rem;color:#57534e;margin-bottom:4px;">Category</div>
    <div style="background:#fafaf9;border:1px solid #e7e5e4;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#1c1917;
                display:flex;justify-content:space-between;align-items:center;margin-bottom:9px;">
      All categories <span style="color:#a8a29e;font-size:0.75rem;">▾</span>
    </div>
    <div style="font-size:0.72rem;color:#57534e;margin-bottom:4px;">Difficulty</div>
    <div style="background:#fafaf9;border:1px solid #e7e5e4;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#1c1917;
                display:flex;justify-content:space-between;align-items:center;">
      All <span style="color:#a8a29e;font-size:0.75rem;">▾</span>
    </div>
  </div>

  <div style="font-size:0.71rem;color:#a8a29e;text-align:center;padding:4px 0;">
    150 / 150 questions
  </div>
</div>
""", unsafe_allow_html=True)

# ── Variation E: Colored top border per card ─────────────────────────────────
with colE:
    st.markdown('<p class="var-label">Variation E — Colored card accents</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="width:100%;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
            overflow:hidden;font-family:system-ui,sans-serif;padding:14px;
            display:flex;flex-direction:column;gap:10px;">

  <div style="padding:4px 2px 10px;">
    <div style="font-size:1.05rem;font-weight:800;letter-spacing:-0.02em;color:#0f172a;">
      SlideQA
    </div>
    <div style="font-size:0.71rem;color:#64748b;margin-top:3px;">
      Multimodal QA benchmark
    </div>
  </div>

  <!-- Course card — indigo top border -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
              overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.04);">
    <div style="height:3px;background:#6366f1;"></div>
    <div style="padding:11px 13px;">
      <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.09em;
                  text-transform:uppercase;color:#6366f1;margin-bottom:7px;">Course</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;">
        CS 288 — Berkeley NLP <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
    </div>
  </div>

  <!-- Filter card — teal top border -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
              overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,0.04);">
    <div style="height:3px;background:#0d9488;"></div>
    <div style="padding:11px 13px;">
      <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.09em;
                  text-transform:uppercase;color:#0d9488;margin-bottom:9px;">Filter</div>
      <div style="font-size:0.72rem;color:#475569;margin-bottom:4px;">Category</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;margin-bottom:9px;">
        All categories <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
      <div style="font-size:0.72rem;color:#475569;margin-bottom:4px;">Difficulty</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;
                  padding:7px 10px;font-size:0.82rem;color:#0f172a;
                  display:flex;justify-content:space-between;align-items:center;">
        All <span style="color:#94a3b8;font-size:0.75rem;">▾</span>
      </div>
    </div>
  </div>

  <!-- Count chip -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
              padding:9px 13px;display:flex;align-items:center;gap:8px;
              box-shadow:0 1px 2px rgba(0,0,0,0.04);">
    <div style="background:#6366f1;color:#fff;font-size:0.76rem;font-weight:700;
                padding:2px 10px;border-radius:20px;">150</div>
    <div style="font-size:0.72rem;color:#64748b;">of 150 questions</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Variation F: Dark card panels, high contrast ─────────────────────────────
with colF:
    st.markdown('<p class="var-label">Variation F — Dark cards, high contrast</p>', unsafe_allow_html=True)
    st.markdown("""
<div style="width:100%;background:#0f172a;border:1px solid #1e293b;border-radius:10px;
            overflow:hidden;font-family:system-ui,sans-serif;padding:14px;
            display:flex;flex-direction:column;gap:10px;">

  <div style="padding:4px 2px 10px;border-bottom:1px solid #1e293b;margin-bottom:2px;">
    <div style="font-size:1.05rem;font-weight:800;letter-spacing:-0.02em;color:#f1f5f9;">
      SlideQA
    </div>
    <div style="font-size:0.71rem;color:#475569;margin-top:3px;">
      Multimodal QA benchmark
    </div>
  </div>

  <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 14px;">
    <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#475569;margin-bottom:7px;">Course</div>
    <div style="background:#0f172a;border:1px solid #334155;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#e2e8f0;
                display:flex;justify-content:space-between;align-items:center;">
      CS 288 — Berkeley NLP
      <span style="color:#475569;font-size:0.75rem;">▾</span>
    </div>
  </div>

  <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 14px;">
    <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.09em;
                text-transform:uppercase;color:#475569;margin-bottom:9px;">Filter</div>
    <div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Category</div>
    <div style="background:#0f172a;border:1px solid #334155;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#e2e8f0;
                display:flex;justify-content:space-between;align-items:center;margin-bottom:9px;">
      All categories <span style="color:#475569;font-size:0.75rem;">▾</span>
    </div>
    <div style="font-size:0.72rem;color:#64748b;margin-bottom:4px;">Difficulty</div>
    <div style="background:#0f172a;border:1px solid #334155;border-radius:6px;
                padding:7px 10px;font-size:0.82rem;color:#e2e8f0;
                display:flex;justify-content:space-between;align-items:center;">
      All <span style="color:#475569;font-size:0.75rem;">▾</span>
    </div>
  </div>

  <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;
              padding:9px 13px;display:flex;align-items:center;gap:8px;">
    <div style="background:#f1f5f9;color:#0f172a;font-size:0.76rem;font-weight:700;
                padding:2px 10px;border-radius:20px;">150</div>
    <div style="font-size:0.72rem;color:#475569;">of 150 questions</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Sidebar locked to E. Now picking the main content area style.")

# ===========================================================================
# PART 2: Main content area variations
# ===========================================================================
st.markdown("---")
st.markdown("# Main Content — 3 Variations")
st.caption("All use the same data. Differences are in layout density, typography, and card treatment.")
st.markdown("&nbsp;")

m1, m2, m3 = st.columns(3, gap="large")

QUESTION = "What new ideas were introduced from EE & ASR during the statistical revolution of the 1990s?"
GOLD = "HMMs, Gaussian mixture models, and discriminative training brought to NLP from speech recognition."
PRED = "The statistical revolution introduced n-gram language models and log-linear models widely adopted from EE."

# ── Main Variation 1: Clean editorial ───────────────────────────────────────
with m1:
    st.markdown('<p class="var-label">Main 1 — Clean editorial</p>', unsafe_allow_html=True)
    st.markdown(f"""
<div style="font-family:system-ui,sans-serif;max-width:520px;">

  <!-- Question selector -->
  <div style="font-size:0.72rem;color:#94a3b8;margin-bottom:4px;font-weight:500;">Select a question</div>
  <div style="border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;
              font-size:0.82rem;color:#64748b;margin-bottom:20px;background:#f8fafc;">
    cs224n_q0001 — What new ideas were introduced… ▾
  </div>

  <!-- Metadata row -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
    <span style="font-size:0.68rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;
                 color:#6366f1;border:1px solid #c7d2fe;background:#eef2ff;
                 padding:2px 8px;border-radius:4px;">Text Only</span>
    <span style="font-size:0.68rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;
                 color:#64748b;border:1px solid #e2e8f0;background:#f8fafc;
                 padding:2px 8px;border-radius:4px;">medium</span>
    <span style="font-size:0.68rem;color:#cbd5e1;margin-left:auto;">cs224n_q0001</span>
  </div>

  <!-- Question -->
  <div style="font-size:1.15rem;font-weight:700;color:#0f172a;line-height:1.4;margin-bottom:18px;">
    {QUESTION}
  </div>

  <div style="height:1px;background:#f1f5f9;margin-bottom:18px;"></div>

  <!-- Two-col: gold + slide placeholder -->
  <div style="display:flex;gap:16px;">
    <div style="flex:1;">
      <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;
                  color:#0d9488;margin-bottom:6px;">Gold Answer</div>
      <div style="border:1px solid #e2e8f0;border-left:3px solid #0d9488;border-radius:0 6px 6px 0;
                  padding:10px 12px;font-size:0.82rem;color:#1e293b;line-height:1.5;background:#f8fffd;">
        {GOLD}
      </div>
      <div style="font-size:0.68rem;color:#94a3b8;margin-top:5px;">lecture_01/slide_012.png</div>
    </div>
    <div style="flex:1;background:#f1f5f9;border-radius:6px;display:flex;
                align-items:center;justify-content:center;min-height:90px;">
      <span style="font-size:0.72rem;color:#94a3b8;">slide image</span>
    </div>
  </div>

  <!-- Baseline cards -->
  <div style="margin-top:18px;">
    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;
                color:#6366f1;margin-bottom:10px;">Baseline Answers</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <div style="border:1px solid #e2e8f0;border-radius:6px;padding:10px 12px;">
        <div style="font-size:0.7rem;font-weight:600;color:#0f172a;margin-bottom:2px;">ColPali RAG</div>
        <div style="font-size:0.68rem;color:#6366f1;margin-bottom:5px;">Judge 4.2 / 5  ·  F1 0.41</div>
        <div style="font-size:0.78rem;color:#334155;line-height:1.4;">{PRED[:80]}…</div>
      </div>
      <div style="border:1px solid #e2e8f0;border-radius:6px;padding:10px 12px;opacity:0.6;">
        <div style="font-size:0.7rem;font-weight:600;color:#0f172a;margin-bottom:2px;">Text BM25</div>
        <div style="font-size:0.68rem;color:#94a3b8;margin-bottom:5px;">Judge 2.1 / 5  ·  F1 0.18</div>
        <div style="font-size:0.78rem;color:#334155;line-height:1.4;">N-gram models and statistical…</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main Variation 2: Horizontal rule sections, full-width cards ─────────────
with m2:
    st.markdown('<p class="var-label">Main 2 — Full-width answer cards</p>', unsafe_allow_html=True)
    st.markdown(f"""
<div style="font-family:system-ui,sans-serif;max-width:520px;">

  <!-- Question selector -->
  <div style="border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;
              font-size:0.82rem;color:#64748b;margin-bottom:16px;background:#f8fafc;">
    cs224n_q0001 — What new ideas were introduced… ▾
  </div>

  <!-- Question + inline badges -->
  <div style="font-size:1.1rem;font-weight:800;color:#0f172a;line-height:1.4;margin-bottom:8px;">
    {QUESTION}
  </div>
  <div style="display:flex;gap:6px;align-items:center;margin-bottom:16px;">
    <span style="font-size:0.65rem;font-weight:700;color:#6366f1;letter-spacing:0.05em;
                 text-transform:uppercase;">Text Only</span>
    <span style="color:#cbd5e1;font-size:0.7rem;">·</span>
    <span style="font-size:0.65rem;font-weight:700;color:#64748b;letter-spacing:0.05em;
                 text-transform:uppercase;">medium</span>
    <span style="color:#cbd5e1;font-size:0.7rem;">·</span>
    <span style="font-size:0.65rem;color:#cbd5e1;">cs224n_q0001</span>
  </div>

  <div style="height:1px;background:#f1f5f9;margin-bottom:16px;"></div>

  <!-- Gold answer full width -->
  <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;
              color:#0d9488;margin-bottom:6px;">Gold Answer · lecture_01/slide_012.png</div>
  <div style="border:1px solid #ccfbf1;background:#f0fdf9;border-radius:6px;
              padding:10px 14px;font-size:0.84rem;color:#134e4a;margin-bottom:16px;line-height:1.5;">
    {GOLD}
  </div>

  <div style="height:1px;background:#f1f5f9;margin-bottom:14px;"></div>

  <!-- Baselines stacked full-width with left score bar -->
  <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;
              color:#6366f1;margin-bottom:10px;">Baselines</div>
  <div style="display:flex;flex-direction:column;gap:6px;">
    <div style="display:flex;align-items:stretch;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;">
      <div style="width:4px;background:#6366f1;flex-shrink:0;"></div>
      <div style="padding:9px 12px;flex:1;">
        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
          <span style="font-size:0.7rem;font-weight:600;color:#0f172a;">ColPali RAG</span>
          <span style="font-size:0.68rem;color:#6366f1;">4.2 / 5</span>
        </div>
        <div style="font-size:0.78rem;color:#475569;line-height:1.4;">{PRED[:90]}…</div>
      </div>
    </div>
    <div style="display:flex;align-items:stretch;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;opacity:0.55;">
      <div style="width:4px;background:#94a3b8;flex-shrink:0;"></div>
      <div style="padding:9px 12px;flex:1;">
        <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
          <span style="font-size:0.7rem;font-weight:600;color:#0f172a;">Text BM25</span>
          <span style="font-size:0.68rem;color:#94a3b8;">2.1 / 5</span>
        </div>
        <div style="font-size:0.78rem;color:#475569;">N-gram models and statistical methods…</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Main Variation 3: Score-first, table-like ────────────────────────────────
with m3:
    st.markdown('<p class="var-label">Main 3 — Score-first compact</p>', unsafe_allow_html=True)
    st.markdown(f"""
<div style="font-family:system-ui,sans-serif;max-width:520px;">

  <!-- Question selector -->
  <div style="border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;
              font-size:0.82rem;color:#64748b;margin-bottom:16px;background:#f8fafc;">
    cs224n_q0001 — What new ideas were introduced… ▾
  </div>

  <!-- Question -->
  <div style="font-size:1.1rem;font-weight:800;color:#0f172a;line-height:1.4;margin-bottom:14px;">
    {QUESTION}
  </div>

  <!-- Meta pills inline -->
  <div style="display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap;">
    <span style="background:#eef2ff;color:#6366f1;font-size:0.65rem;font-weight:700;
                 padding:3px 9px;border-radius:20px;letter-spacing:0.04em;">TEXT ONLY</span>
    <span style="background:#f1f5f9;color:#64748b;font-size:0.65rem;font-weight:700;
                 padding:3px 9px;border-radius:20px;letter-spacing:0.04em;">MEDIUM</span>
    <span style="background:#f1f5f9;color:#94a3b8;font-size:0.65rem;
                 padding:3px 9px;border-radius:20px;">cs224n_q0001</span>
  </div>

  <div style="height:1px;background:#f1f5f9;margin-bottom:14px;"></div>

  <!-- Gold -->
  <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;
              color:#94a3b8;margin-bottom:5px;">Gold Answer</div>
  <div style="font-size:0.84rem;color:#0f172a;line-height:1.5;margin-bottom:14px;
              padding-left:10px;border-left:2px solid #0d9488;">
    {GOLD}
  </div>

  <div style="height:1px;background:#f1f5f9;margin-bottom:14px;"></div>

  <!-- Score header row -->
  <div style="display:grid;grid-template-columns:1fr 50px 50px;gap:4px;
              font-size:0.62rem;font-weight:700;letter-spacing:0.07em;
              text-transform:uppercase;color:#94a3b8;padding:0 4px;margin-bottom:6px;">
    <span>Baseline</span><span style="text-align:right;">Judge</span><span style="text-align:right;">F1</span>
  </div>
  <!-- Row 1 -->
  <div style="display:grid;grid-template-columns:1fr 50px 50px;gap:4px;
              padding:9px 4px;border-top:1px solid #f1f5f9;align-items:start;">
    <div>
      <div style="font-size:0.72rem;font-weight:600;color:#0f172a;margin-bottom:3px;">ColPali RAG</div>
      <div style="font-size:0.75rem;color:#475569;line-height:1.4;">{PRED[:70]}…</div>
    </div>
    <div style="font-size:0.78rem;font-weight:700;color:#6366f1;text-align:right;">4.2</div>
    <div style="font-size:0.78rem;color:#64748b;text-align:right;">0.41</div>
  </div>
  <!-- Row 2 -->
  <div style="display:grid;grid-template-columns:1fr 50px 50px;gap:4px;
              padding:9px 4px;border-top:1px solid #f1f5f9;align-items:start;opacity:0.6;">
    <div>
      <div style="font-size:0.72rem;font-weight:600;color:#0f172a;margin-bottom:3px;">Text BM25</div>
      <div style="font-size:0.75rem;color:#475569;">N-gram models and statistical…</div>
    </div>
    <div style="font-size:0.78rem;font-weight:700;color:#94a3b8;text-align:right;">2.1</div>
    <div style="font-size:0.78rem;color:#94a3b8;text-align:right;">0.18</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Pick Main 1, 2, or 3 — then we'll implement it and move to the question card details.")
