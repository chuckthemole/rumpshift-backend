# models.py
from django.db import models


class ArduinoMachine(models.Model):
    """
    Represents a physical Arduino machine.
    Stores IP and alias information for each machine.
    Tasks can be associated with a machine via the ArduinoTask model.
    """
    ip = models.GenericIPAddressField(unique=True)
    alias = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wakeup_payload = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Arduino Machine"
        verbose_name_plural = "Arduino Machines"

    def __str__(self):
        return f"{self.alias} ({self.ip})"


class ArduinoTask(models.Model):
    """
    Represents a task running on a specific Arduino machine.
    Tasks are linked to a machine via ForeignKey.
    Status can be idle, running, or paused.
    """
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('paused', 'Paused'),
    ]

    machine = models.ForeignKey(
        ArduinoMachine,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="The Arduino machine this task is associated with.",
        null=True
    )
    task_name = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='idle')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Arduino Task"
        verbose_name_plural = "Arduino Tasks"

    def __str__(self):
        return f"{self.task_name} ({self.machine.alias}) - {self.status}"
