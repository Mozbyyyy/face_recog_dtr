# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import datetime
# from django.db import transaction

# def clear_temporary_table():
#     from myapp.models import Archive
    
#     try:
#         with transaction.atomic():
   

#             Archive.objects.all().delete()

#             now = datetime.now()

#             print(f"Data transferred and ArchiveAttendance cleared at: {now}")
            
#     except Exception as e:
#         print(f"Error transferring data: {e}")


# scheduler = BackgroundScheduler()

# scheduler.add_job(clear_temporary_table, 'cron', hour=10, minute=31)

# scheduler.start()