"""Chart generation (headless matplotlib)."""

import base64
import io
import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)


def generate_chart_base64(hist, title: str = "Price Chart") -> str:
    """Encode a simple close-price chart as base64 PNG."""
    try:
        plt.figure(figsize=(10, 4))
        plt.plot(hist.index, hist["Close"], label="Close Price", color="cyan")
        plt.title(title)
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid(True)
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        logger.exception("generate_chart_base64 failed: %s", e)
        raise
