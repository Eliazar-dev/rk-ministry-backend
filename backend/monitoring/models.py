from django.db import models


class Heartbeat(models.Model):
    """One row per minute at most, written only by the status page and /health/. Nothing under /api/ touches it."""

    at = models.DateTimeField(db_index=True)
    ok = models.BooleanField(default=True)

    class Meta:
        ordering = ['-at']
