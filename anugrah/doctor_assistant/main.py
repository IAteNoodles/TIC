"""
Entry point module. Run the Streamlit app with:
  streamlit run doctor_assistant/frontend/app.py
"""

from logging_config import get_logger

logger = get_logger("main")

if __name__ == "__main__":
    logger.info("Launch the Streamlit app with: streamlit run doctor_assistant/frontend/app.py")
