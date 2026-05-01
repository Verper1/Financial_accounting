try:
    from .celery import app as celery_app
except ImportError:
    celery_app = None  # type: ignore[assignment]

__all__ = ["celery_app"]
