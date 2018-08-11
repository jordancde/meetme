from django.db import models

class MeetMeUser(models.Model):
    user = models.CharField(max_length=255)
    slots = models.CharField(max_length=1000,default="")
    requests = models.CharField(max_length=255,default="")
    meetings = models.CharField(max_length=255,default="")

class Slot(models.Model):
    start = models.DateTimeField()
    end = models.DateTimeField()
    user = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    tag = models.CharField(max_length=255,null=True)

class Request(models.Model):
    user_from = models.CharField(max_length=255)
    user_to = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=255)
    status = models.NullBooleanField(null=True)
    description = models.CharField(max_length=255)
    tag = models.CharField(max_length=255,null=True)

class Meeting(models.Model):
    request = models.CharField(max_length=255)
    tag = models.CharField(max_length=255,null=True)

