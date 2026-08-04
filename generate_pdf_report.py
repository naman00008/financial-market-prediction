"""
MarketPulse PDF Documentation Generator
Builds a publication-quality, professional technical report PDF
covering project details, quantitative methodology, system architecture,
deployment procedures, and technology stack.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Color Palette
PRIMARY_COLOR = colors.HexColor("#0F172A")    # Dark Navy
SECONDARY_COLOR = colors.HexColor("#0284C7")  # Tech Blue
ACCENT_COLOR = colors.HexColor("#0EA5E9")     # Sky Blue
TEXT_DARK = colors.HexColor("#1E293B")        # Slate Dark
TEXT_MUTED = colors.HexColor("#64748B")       # Slate Muted
BG_LIGHT = colors.HexColor("#F8FAFC")         # Ultra Light Gray
BORDER_COLOR = colors.HexColor("#E2E8F0")     # Border Gray
CODE_BG = colors.HexColor("#0F172A")          # Code Block Dark
CODE_TEXT = colors.HexColor("#38BDF8")        # Code Text Blue


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render total page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "MarketPulse — Financial Market Prediction Platform Documentation")
            self.drawRightString(612 - 54, 750, "Technical Specification & Architecture")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer (all pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        
        self.drawString(54, 32, "Confidential — Institutional Quantitative & Engineering Report")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.restoreState()


def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=SECONDARY_COLOR,
        spaceAfter=15
    )

    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_MUTED,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=SECONDARY_COLOR,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=CODE_TEXT,
        spaceAfter=0
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=0
    )

    story = []

    # ==========================================
    # COVER / HEADER SECTION
    # ==========================================
    story.append(Paragraph("MarketPulse Intelligence Platform", title_style))
    story.append(Paragraph("Comprehensive Project Specification, Methodology, Architecture & Deployment Blueprint", subtitle_style))
    story.append(Paragraph("<b>Version:</b> 3.5 (Production Release) &nbsp;|&nbsp; <b>Environment:</b> Cloud & Local Synced &nbsp;|&nbsp; <b>Classification:</b> Institutional Engineering", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY_COLOR, spaceBefore=0, spaceAfter=14))

    # ==========================================
    # 1. PROJECT OVERVIEW
    # ==========================================
    story.append(Paragraph("1. Executive Project Overview", h1_style))
    story.append(Paragraph(
        "<b>MarketPulse</b> is an institutional-grade financial analytics, machine learning price forecasting, and quantitative portfolio management platform. "
        "Engineered for research analysts, portfolio managers, and quantitative developers, the platform delivers end-to-end investment capabilities—from live tick data ingestion and technical indicator calculations to multi-algorithm machine learning model training, NLP financial sentiment scoring, and modern portfolio theory optimization.",
        body_style
    ))

    overview_bullets = [
        "<b>Interactive Financial Charting:</b> High-density candlestick visualizer equipped with dynamic technical overlays (Bollinger Bands, SMA, EMA, MACD, RSI, and Volume profiles).",
        "<b>Predictive ML Pipeline:</b> Automated training and backtesting across six regression algorithms (Linear Regression, Ridge, Lasso, Random Forest, Gradient Boosting, SVR) with performance scoring (RMSE, Directional Accuracy).",
        "<b>NLP Sentiment Engine:</b> Automated multi-source financial news aggregation (Google RSS, NewsAPI) with lexicon-based VADER compound polarity scoring.",
        "<b>Portfolio Optimization:</b> Modern Portfolio Theory (MPT) engine calculating Maximum Sharpe Ratio, Minimum Volatility, and Risk Parity asset allocations.",
        "<b>Institutional Audit & Storage:</b> Multi-user security with salted PBKDF2-HMAC-SHA256 password hashing, dedicated filesystem dossiers (<code>data/users/&lt;username&gt;/</code>), CSV spreadsheets, and sub-millisecond cloud telemetry synchronization."
    ]
    for b in overview_bullets:
        story.append(Paragraph(f"• {b}", bullet_style))

    story.append(Spacer(1, 10))

    # ==========================================
    # 2. QUANTITATIVE METHODOLOGY
    # ==========================================
    story.append(Paragraph("2. Quantitative Methodology & Mathematical Framework", h1_style))
    
    story.append(Paragraph("A. Technical Feature Engineering", h2_style))
    story.append(Paragraph(
        "Raw OHLCV time-series are transformed into stationarized, lagged feature vectors to prevent lookahead bias while capturing momentum, volatility, and trend strength:",
        body_style
    ))

    math_table_data = [
        [Paragraph("<b>Indicator / Feature</b>", body_style), Paragraph("<b>Mathematical Formulation</b>", body_style), Paragraph("<b>Financial Purpose</b>", body_style)],
        [
            Paragraph("<b>Relative Strength Index (RSI)</b>", body_style),
            Paragraph("RSI = 100 - [100 / (1 + RS)]<br/>RS = EMA(Gains, 14) / EMA(Losses, 14)", body_style),
            Paragraph("Measures velocity and magnitude of price movements (Overbought: &gt;70, Oversold: &lt;30).", body_style)
        ],
        [
            Paragraph("<b>MACD & Signal</b>", body_style),
            Paragraph("MACD = EMA(12) - EMA(26)<br/>Signal = EMA(MACD, 9)", body_style),
            Paragraph("Captures trend direction, momentum acceleration, and potential centerline crossovers.", body_style)
        ],
        [
            Paragraph("<b>Bollinger Bands</b>", body_style),
            Paragraph("Upper/Lower = SMA(20) ± (2 × σ_20)", body_style),
            Paragraph("Defines dynamic volatility channels based on standard deviation bands.", body_style)
        ],
        [
            Paragraph("<b>Log Returns & Lags</b>", body_style),
            Paragraph("R_t = ln(P_t / P_{t-1})<br/>Features = [R_{t-1}, ..., R_{t-k}]", body_style),
            Paragraph("Produces stationary returns and autoregressive feature inputs for ML algorithms.", body_style)
        ],
    ]
    t_math = Table(math_table_data, colWidths=[1.5*inch, 2.7*inch, 2.6*inch])
    t_math.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_math)
    story.append(Spacer(1, 8))

    story.append(Paragraph("B. Machine Learning Prediction Pipeline", h2_style))
    story.append(Paragraph(
        "1. <b>Chronological Train/Test Partitioning:</b> Non-shuffled 80/20 time-series split ensuring training occurs strictly on historical bars prior to the out-of-sample validation period.<br/>"
        "2. <b>Algorithms Evaluated:</b> Ordinary Least Squares (Linear Regression), L1/L2 Regularization (Lasso, Ridge), Random Forest Regressor, Gradient Boosting Regressor, Support Vector Regressor (SVR).<br/>"
        "3. <b>Validation Metrics:</b> Root Mean Squared Error (RMSE) for magnitude precision and Directional Accuracy (%) for trend prediction.",
        body_style
    ))

    story.append(Paragraph("C. Modern Portfolio Theory (Sharpe Optimization)", h2_style))
    story.append(Paragraph(
        "Asset weight allocations (w) are calculated by maximizing the portfolio Sharpe Ratio:<br/>"
        "<b>max_w [ (w^T μ - r_f) / sqrt(w^T Σ w) ]</b> &nbsp; subject to &nbsp; <b>sum(w_i) = 1, w_i &ge; 0</b><br/>"
        "where μ represents expected returns vector, Σ represents the empirical covariance matrix, and r_f is the benchmark risk-free rate.",
        body_style
    ))

    story.append(Spacer(1, 10))

    # ==========================================
    # 3. SYSTEM ARCHITECTURE
    # ==========================================
    story.append(Paragraph("3. System Architecture & Component Design", h1_style))
    story.append(Paragraph(
        "The platform is organized into modular decoupled layers ensuring clean separation of presentation, quantitative compute, security, persistence, and real-time cloud telemetry.",
        body_style
    ))

    arch_data = [
        [Paragraph("<b>Subsystem</b>", body_style), Paragraph("<b>Primary Components</b>", body_style), Paragraph("<b>Responsibilities & Flow</b>", body_style)],
        [
            Paragraph("<b>Presentation Layer</b>", body_style),
            Paragraph("<code>app/dashboard.py</code><br/><code>app/auth_ui.py</code><br/><code>app/styling.py</code>", body_style),
            Paragraph("Interactive multi-tab workspace, reactive form inputs, institutional CSS glassmorphism styling, and authentication gatekeeping.", body_style)
        ],
        [
            Paragraph("<b>Quantitative Core</b>", body_style),
            Paragraph("<code>src/live_data.py</code><br/><code>src/feature_engineering.py</code><br/><code>src/model_training.py</code><br/><code>src/sentiment_analysis.py</code>", body_style),
            Paragraph("yfinance ingestion caching, technical indicators computation, multi-model ML regression training, and VADER financial sentiment scoring.", body_style)
        ],
        [
            Paragraph("<b>Security & Auth</b>", body_style),
            Paragraph("<code>src/auth.py</code><br/><code>data/users.db</code>", body_style),
            Paragraph("PBKDF2-HMAC-SHA256 cryptographic hashing (100,000 rounds), hex salting, SQLite user database management, and credential verification.", body_style)
        ],
        [
            Paragraph("<b>Storage & Dossiers</b>", body_style),
            Paragraph("<code>src/tracker.py</code><br/><code>data/users/&lt;user&gt;/</code>", body_style),
            Paragraph("Dedicated per-user filesystem directories, plaintext activity dossiers, CSV spreadsheets, saved ML runs, and portfolio allocations.", body_style)
        ],
        [
            Paragraph("<b>Cloud Telemetry Sync</b>", body_style),
            Paragraph("<code>src/cloud_stream.py</code><br/><code>sync_live_users.py</code><br/><code>server.py</code>", body_style),
            Paragraph("Low-latency SSE socket listener over ntfy.sh and Tornado REST API (/api/sync) syncing cloud events directly into local SQLite and dossiers.", body_style)
        ]
    ]
    t_arch = Table(arch_data, colWidths=[1.4*inch, 2.3*inch, 3.1*inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_arch)

    story.append(Spacer(1, 10))

    # ==========================================
    # 4. TOOLS & TECHNOLOGIES
    # ==========================================
    story.append(Paragraph("4. Technology Stack & Tools Used", h1_style))

    tech_data = [
        [Paragraph("<b>Category</b>", body_style), Paragraph("<b>Tool / Library</b>", body_style), Paragraph("<b>Version</b>", body_style), Paragraph("<b>Technical Role</b>", body_style)],
        [Paragraph("Language & Runtime", body_style), Paragraph("Python", body_style), Paragraph("3.9 / 3.11", body_style), Paragraph("Core programming language and server runtime.", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("Streamlit", body_style), Paragraph(">=1.28.0", body_style), Paragraph("Reactive web platform, sidebar widgets, and tab routing.", body_style)],
        [Paragraph("Data Ingestion", body_style), Paragraph("yfinance", body_style), Paragraph(">=0.2.28", body_style), Paragraph("Historical and live equity/index OHLCV extraction.", body_style)],
        [Paragraph("Numerics & Tables", body_style), Paragraph("Pandas & NumPy", body_style), Paragraph(">=2.0.0", body_style), Paragraph("Time-series rolling operations, matrices, and indexing.", body_style)],
        [Paragraph("Machine Learning", body_style), Paragraph("Scikit-learn", body_style), Paragraph(">=1.3.0", body_style), Paragraph("Regression algorithms, train/test split, scaling, metrics.", body_style)],
        [Paragraph("Visualizations", body_style), Paragraph("Plotly & Seaborn", body_style), Paragraph(">=5.16.0", body_style), Paragraph("Interactive financial candlestick charts and heatmaps.", body_style)],
        [Paragraph("NLP & Sentiment", body_style), Paragraph("vaderSentiment", body_style), Paragraph(">=3.3.2", body_style), Paragraph("Lexicon sentiment analysis for financial headlines.", body_style)],
        [Paragraph("Database", body_style), Paragraph("SQLite3", body_style), Paragraph("Standard", body_style), Paragraph("Relational storage for registered user accounts & credentials.", body_style)],
        [Paragraph("REST & Web Server", body_style), Paragraph("Tornado Web", body_style), Paragraph("Bundled", body_style), Paragraph("Custom REST handlers for /api/sync and /api/download_users.", body_style)],
        [Paragraph("Cloud Telemetry", body_style), Paragraph("Requests / ntfy", body_style), Paragraph(">=2.31.0", body_style), Paragraph("Sub-millisecond unbuffered live activity streaming.", body_style)],
        [Paragraph("Deployment", body_style), Paragraph("Render Cloud", body_style), Paragraph("PaaS", body_style), Paragraph("Continuous GitHub CI/CD build and cloud hosting.", body_style)],
    ]
    t_tech = Table(tech_data, colWidths=[1.3*inch, 1.4*inch, 0.9*inch, 3.2*inch])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_tech)

    story.append(Spacer(1, 10))

    # ==========================================
    # 5. DEPLOYMENT STEPS
    # ==========================================
    story.append(Paragraph("5. Step-by-Step Deployment Guide", h1_style))
    
    story.append(Paragraph("A. Cloud Deployment (Render PaaS)", h2_style))
    story.append(Paragraph(
        "1. <b>Infrastructure Configuration:</b> Create <code>render.yaml</code> specifying service type, Python version (3.11.0), build command (<code>pip install -r requirements.txt</code>), and start command (<code>python server.py</code>).<br/>"
        "2. <b>Server Entry Point:</b> <code>server.py</code> binds to Render's dynamic <code>$PORT</code>, attaches Tornado sync endpoints (<code>/api/sync</code>), and launches Streamlit.<br/>"
        "3. <b>Continuous Deployment:</b> Every commit pushed to GitHub <code>main</code> triggers an automated zero-downtime build and redeployment on Render.",
        body_style
    ))

    story.append(Paragraph("B. Local Environment & Real-Time Sync Execution", h2_style))
    story.append(Paragraph(
        "1. <b>Install Dependencies:</b> <code>pip install -r requirements.txt</code><br/>"
        "2. <b>Launch Local Web Server:</b> <code>python server.py</code><br/>"
        "3. <b>Start Real-Time Telemetry Listener:</b> Double-click <code>Sync_Cloud_Users.command</code> or execute <code>python3 sync_live_users.py</code>. Captures live cloud transactions and synchronizes local SQLite database.<br/>"
        "4. <b>One-Click Instant Sync:</b> Double-click <code>Sync_Database_Now.command</code> or run <code>python3 sync_now.py</code> to immediately pull all cloud user records.",
        body_style
    ))

    story.append(Spacer(1, 10))

    # ==========================================
    # 6. STORAGE & AUDIT DOSSIER ARCHITECTURE
    # ==========================================
    story.append(Paragraph("6. Backend User Storage & Dossier Hierarchy", h1_style))
    story.append(Paragraph(
        "Every user account automatically receives an isolated filesystem directory structure under <code>data/users/&lt;username&gt;/</code>:",
        body_style
    ))

    dossier_data = [
        [Paragraph("<b>File / Folder</b>", body_style), Paragraph("<b>Format</b>", body_style), Paragraph("<b>Description & Contents</b>", body_style)],
        [Paragraph("<code>credentials.txt</code>", body_style), Paragraph("Plaintext", body_style), Paragraph("Security dossier detailing username, email, tier, PBKDF2 hash, and salt.", body_style)],
        [Paragraph("<code>credentials.json</code>", body_style), Paragraph("JSON", body_style), Paragraph("Structured authentication record with algorithm metadata for sync.", body_style)],
        [Paragraph("<code>profile.json</code>", body_style), Paragraph("JSON", body_style), Paragraph("User profile metadata, registration date, and total action counts.", body_style)],
        [Paragraph("<code>USER_PROFILE_&_ACTIVITY_REPORT.txt</code>", body_style), Paragraph("Plaintext", body_style), Paragraph("Chronological human-readable audit trail of every user transaction.", body_style)],
        [Paragraph("<code>activity_log.csv</code>", body_style), Paragraph("CSV", body_style), Paragraph("Spreadsheet-ready event log for Microsoft Excel or Apple Numbers.", body_style)],
        [Paragraph("<code>searched_stocks.txt</code>", body_style), Paragraph("Plaintext", body_style), Paragraph("Historical ledger of all analyzed and searched equity tickers.", body_style)],
        [Paragraph("<code>activity_logs/activity.jsonl</code>", body_style), Paragraph("JSONL", body_style), Paragraph("Immutable append-only raw telemetry stream record.", body_style)],
        [Paragraph("<code>saved_predictions/</code>", body_style), Paragraph("JSON Files", body_style), Paragraph("Stored ML model runs, test RMSE, directional accuracy, and metrics.", body_style)],
        [Paragraph("<code>portfolios/</code>", body_style), Paragraph("JSON Files", body_style), Paragraph("Saved portfolio optimization weight allocations and Sharpe metrics.", body_style)],
    ]
    t_dossier = Table(dossier_data, colWidths=[2.2*inch, 1.1*inch, 3.5*inch])
    t_dossier.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_dossier)

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Report Generated:</b> August 2026 &nbsp;|&nbsp; <b>Author:</b> MarketPulse Engineering Team &nbsp;|&nbsp; <b>Status:</b> Verified & Active", meta_style))

    # Build PDF with dynamic page numbering
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF at: {filename}")


if __name__ == "__main__":
    out_paths = [
        os.path.join(os.path.dirname(__file__), "MarketPulse_Project_Documentation.pdf"),
        os.path.expanduser("~/Desktop/MarketPulse_Project_Documentation.pdf")
    ]
    for p in out_paths:
        try:
            build_pdf(p)
        except Exception as e:
            print(f"Error writing to {p}: {e}")
