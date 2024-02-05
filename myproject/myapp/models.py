from django.db.models.signals import pre_save
from django.dispatch import receiver
#from django.utils.text import slugify
from django.db import models
from datetime import date,datetime
from django.contrib.auth.models import User
from django.utils import timezone
import re
from django.db import IntegrityError
import qrcode
from django.db.models.signals import post_save

class TemporaryAttendance(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(default=date.today)  
    timein = models.CharField(max_length=8,blank=True,null=True)  
    timeout = models.CharField(max_length=8,blank=True, null=True)  
    breakout = models.CharField(max_length=8,blank=True, null=True) 
    breakin = models.CharField(max_length=8,blank=True, null=True) 
    branch_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now,null=True)  
  
    def to_sql(self):
        timein = f"'{self.timein}'" if self.timein is not None else 'NULL'
        timeout = f"'{self.timeout}'" if self.timeout is not None else 'NULL'
        breakout = f"'{self.breakout}'" if self.breakout is not None else 'NULL'
        breakin = f"'{self.breakin}'" if self.breakin is not None else 'NULL'
        branch_name = f"'{self.branch_name}'" if self.branch_name is not None else 'NULL'
        
        return f"INSERT INTO temporary(name, date, timein, timeout, breakout, breakin, branch_name, created_at) VALUES " \
               f"('{self.name}', '{self.date}', {timein}, {timeout}, {breakout}, {breakin}, {branch_name}, '{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}');"
        
    def to_sql_all(self):
        timeout = f"'{self.timeout}'" if self.timeout is not None else 'NULL'
        breakout = f"'{self.breakout}'" if self.breakout is not None else 'NULL'
        breakin = f"'{self.breakin}'" if self.breakin is not None else 'NULL'

        return f"UPDATE temporary SET " \
               f"timeout = {timeout}, " \
               f"breakout = {breakout}, " \
               f"breakin = {breakin} " \
               f"WHERE name = '{self.name}' AND date = '{self.date}' AND branch_name = '{self.branch_name}';"

 
            

    class Meta:
        db_table = 'temporary'




class Archive(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(default=date.today)
    timein_names = models.CharField(max_length=100,null=True,blank=True)
    timeout_names = models.CharField(max_length=100,null=True,blank=True)
    breakout_names = models.CharField(max_length=100,null=True,blank=True)
    breakin_names = models.CharField(max_length=100,null=True,blank=True)
    timein_timestamps = models.DateTimeField(null=True,blank=True)
    breakout_timestamps = models.DateTimeField(null=True,blank=True)
    breakin_timestamps = models.DateTimeField(null=True,blank=True)
    timeout_timestamps = models.DateTimeField(null=True,blank=True)
    afternoonBreakout_timestamps = models.DateTimeField(null=True,blank=True)
    afternoonTimeout_timestramps = models.DateTimeField(null=True,blank=True)

    class Meta:
        db_table = 'archive'



       

class Student(models.Model):
    code = models.CharField(max_length=15,unique=True)
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)



class QRList(models.Model):
    name = models.CharField(max_length=100,null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    
    class Meta:
        db_table = 'qr_list'    
        
        
class qr_existing_list(models.Model):
        id = models.CharField(primary_key=True,max_length=11)
        employee_unique_id = models.CharField(max_length=200)
        fn = models.CharField(max_length=100)
        mn = models.CharField(max_length=100)
        ln = models.CharField(max_length=100)
        branch = models.CharField(max_length=200)
        qr_codes = models.CharField(max_length=100)
        
        class Meta:
            db_table = 'qr_existing_list'



class model_dbf_to_sql(models.Model):
    ACCTNO = models.DecimalField(max_digits=10,null=True,decimal_places=1)
    UDATE = models.CharField(max_length=50,null=True)
    UDIBAL = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    OLDACCT = models.DecimalField(null=True,max_digits=10, decimal_places=1)

    class Meta:
        db_table = 'md_dbf_to_sql'



        
@receiver(pre_save, sender=Student)
def generate_code(sender, instance, **kwargs):
    if not instance.code:
        current_number = Student.objects.count() + 10000
        new_code = f"EMB{current_number:05d}"
        instance.code = new_code