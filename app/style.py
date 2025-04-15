"""
Styling for the Basketball Classifier application.
This file contains the styling constants used throughout the app.
"""

# App styling
STYLE = """
QWidget {
    background-color: #121212;
    color: #f1f1f1;
    font-family: 'Consolas';
    font-size: 9pt;
}

QLabel {
    color: #f1f1f1;
    border: none;
    font-size: 9pt;
}

QPushButton {
    background-color: #1e1e1e;
    color: #ff3e3e;
    border: 1px solid #ff3e3e;
    border-radius: 4px;
    padding: 6px 10px;
    font-weight: bold;
    font-size: 9pt;
}

QPushButton:hover {
    background-color: #ff3e3e;
    color: #121212;
}

QPushButton:pressed {
    background-color: #b71c1c;
    color: #121212;
}

QProgressBar {
    border: 1px solid #ff3e3e;
    border-radius: 2px;
    text-align: center;
    background-color: #1e1e1e;
}

QProgressBar::chunk {
    background-color: #ff3e3e;
}

QSlider::groove:horizontal {
    height: 8px;
    background: #1e1e1e;
    border: 1px solid #ff3e3e;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #ff3e3e;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
"""

# Color constants
RED_COLOR = "#ff3e3e"
DARK_BG_COLOR = "#121212"
LIGHT_TEXT_COLOR = "#f1f1f1"
SECONDARY_BG_COLOR = "#1e1e1e" 