from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl, QObject, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from code.quiz import Quiz

LATIN_MODERN = "Latin Modern Roman"
GRADE_LIMITS = {90: 'A', 72: 'B', 62: 'C', 48: 'D', 38: 'E', 29: 'F'}

class SummaryBridge(QObject):
    def __init__(self, return_callback):
        super().__init__()
        self.return_callback = return_callback

    @pyqtSlot()
    def return_to_dashboard(self):
        self.return_callback()


class SummaryWindow(QWidget):
    def __init__(self, quiz: Quiz, return_callback):
        super().__init__()
        self.quiz = quiz
        self.return_callback = return_callback

        self.setWindowTitle("Quiz Summary")
        screen = self.screen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.95))
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.summary_view = QWebEngineView()
        layout.addWidget(self.summary_view)

        # WebChannel for å koble JS-knappen til Python-callback
        self.channel = QWebChannel()
        self.bridge = SummaryBridge(self.return_callback)
        self.channel.registerObject("summaryBridge", self.bridge)
        self.summary_view.page().setWebChannel(self.channel)

        html = self.render_mathjax_html()
        self.summary_view.setHtml(html, QUrl(""))

    def render_mathjax_html(self):
        correct = sum(self.quiz.results)
        total = len(self.quiz.results)
        percent = round((correct / total) * 100)
        grade = "F"
        for limit, g in sorted(GRADE_LIMITS.items(), reverse=True):
            if percent >= limit:
                grade = g
                break

        rows = [f"""
            <div class='summary-header'>
                <div><strong>Quiz Summary</strong></div>
                <div>{correct}/{total} correct ({percent}%)</div>
                <div>Grade: {grade}</div>
                <div>
                    <button onclick="returnToDashboard()">Return to Dashboard</button>
                </div>
            </div>
            <div class='divider'></div>
        """]

        for i, (p, was_correct) in enumerate(zip(self.quiz.problems, self.quiz.results)):
            qtext = p.question.strip().replace("\n", " ")
            if len(qtext) > 140:
                qtext = qtext[:140] + "..."
            rows.append(f"<p><b>{i+1}. {qtext}</b></p><ul>")
            for j, alt in enumerate(p.alternatives):
                alt_id = f"_alt{j+1}"
                symbol = ""
                if alt_id == p.correct_alt:
                    symbol = " ✅"
                elif self.quiz.user_answers[i] == j:
                    symbol = " ❌"
                text = alt.strip().replace("\n", " ")
                rows.append(f"<li>{j+1}) {text}{symbol}</li>")
            rows.append("</ul><div class='divider'></div>")

        content = "\n".join(rows)

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <style>
            body {{
                font-family: '{LATIN_MODERN}';
                font-size: 16pt;
                background-color: white;
                color: black;
                margin: 0;
                padding: 20px;
            }}
            .summary-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 16pt;
                font-weight: bold;
                color: #8000c8;
                margin-bottom: 10px;
            }}
            button {{
                background-color: #8000c8;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                font-size: 14pt;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #a34cd4;
            }}
            .divider {{
                border-bottom: 2px solid #8000c8;
                margin: 20px 0;
            }}
            ul {{
                margin-left: 20px;
            }}
        </style>
        <script>
            let bridge = null;
            new QWebChannel(qt.webChannelTransport, function(channel) {{
                bridge = channel.objects.summaryBridge;
            }});
            function returnToDashboard() {{
                if (bridge) {{
                    bridge.return_to_dashboard();
                }}
            }}
        </script>
        <script src='https://polyfill.io/v3/polyfill.min.js?features=es6'></script>
        <script>
            window.MathJax = {{
                tex: {{ inlineMath: [['$','$']] }},
                svg: {{ fontCache: 'global' }}
            }};
        </script>
        <script async src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'></script>
        </head>
        <body>
        {content}
        </body>
        </html>
        """
