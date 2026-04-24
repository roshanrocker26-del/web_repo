from django.db import models


class Announcements(models.Model):
    title = models.CharField(max_length=255)
    file = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    school = models.ForeignKey('School', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'announcements'

class Books(models.Model):
    book_id = models.CharField(primary_key=True, max_length=50)
    series_name = models.CharField(max_length=100)
    class_field = models.CharField(db_column='class', max_length=20)  # Field renamed because it was a Python reserved word.
    path = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'books'


class Purchase(models.Model):
    purchase_id = models.CharField(primary_key=True, max_length=50)
    school = models.ForeignKey('School', models.DO_NOTHING)
    purchase_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase'


class PurchaseItems(models.Model):
    purchase = models.ForeignKey(Purchase, models.DO_NOTHING)
    book = models.ForeignKey(Books, models.DO_NOTHING)
    valid_upto = models.DateField()
    sent_to_school = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'purchase_items'
        unique_together = (('purchase', 'book'),)

class School(models.Model):
    school_name = models.CharField(max_length=150)
    school_id = models.CharField(primary_key=True, max_length=50)
    contact = models.CharField(max_length=15, blank=True, null=True)
    password_hash = models.CharField(max_length=200)
    branch = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'school'
