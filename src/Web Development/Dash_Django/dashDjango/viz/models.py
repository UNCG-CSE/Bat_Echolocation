from django.db import models


class Echo(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images', blank=True)


class Abnormal(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images', blank=True)


class Noise(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images', blank=True)
