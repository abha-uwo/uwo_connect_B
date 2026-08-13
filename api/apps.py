import sys
import os
from django.apps import AppConfig

class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        if 'runserver' in sys.argv:
            from django.db import connections
            try:
                db_conn = connections['default']
                db_conn.ensure_connection()
                db_name = os.getenv('MONGODB_DB_NAME', 'unknown')
                print(f"\n[OK] SUCCESS: MongoDB connection is ACTIVE! (db: {db_name})\n")
            except Exception as e:
                print(f"\n[ERROR] MongoDB connection FAILED!")
                print(f"Check your .env URL and password. Reason: {str(e)}\n")

            # Start background YouTube poller thread in the main worker process
            is_main_process = os.environ.get('RUN_MAIN') == 'true' or '--noreload' in sys.argv
            if is_main_process:
                import threading
                import time
                from django.db import close_old_connections

                def youtube_poller():
                    time.sleep(5)  # Wait for db setup to settle
                    print("[YouTube Poller]: Background automation loop STARTED.")
                    while True:
                        try:
                            close_old_connections()
                            from api.models import Client
                            from api.views.youtube_views import auto_reply_to_youtube_comments, check_and_broadcast_youtube_uploads
                            
                            clients = Client.objects.filter(youtube_enabled=True)
                            for client in clients:
                                config = client.youtube_config or {}
                                
                                # Auto-reply comments
                                if config.get("bot_enabled", False):
                                    auto_reply_to_youtube_comments(client)
                                
                                # Broadcast uploads
                                if config.get("broadcast_enabled", False):
                                    check_and_broadcast_youtube_uploads(client)
                        except Exception as poll_err:
                            print(f"[YouTube Poller Error]: {poll_err}")
                        
                        # Wait 15 seconds before next polling iteration
                        time.sleep(15)

                thread = threading.Thread(target=youtube_poller, daemon=True, name="YouTubeBackgroundPoller")
                thread.start()

                def campaign_scheduler():
                    time.sleep(10)  # Wait for db setup to settle
                    print("[Campaign Scheduler]: Background loop STARTED.")
                    from django.utils import timezone
                    while True:
                        try:
                            close_old_connections()
                            from api.models import Campaign
                            from api.services.campaign_service import CampaignService
                            
                            # Find all scheduled campaigns where scheduled_at is less than or equal to now
                            now = timezone.now()
                            ready_campaigns = Campaign.objects.filter(status='SCHEDULED', scheduled_at__lte=now)
                            for campaign in ready_campaigns:
                                campaign.status = 'SENDING'
                                campaign.save()
                                
                                # Process each campaign in its own thread to avoid blocking the scheduler
                                camp_thread = threading.Thread(target=CampaignService.process_campaign, args=(campaign.id,))
                                camp_thread.start()
                        except Exception as e:
                            print(f"[Campaign Scheduler Error]: {e}")
                        
                        time.sleep(60)

                campaign_thread = threading.Thread(target=campaign_scheduler, daemon=True, name="CampaignBackgroundScheduler")
                campaign_thread.start()

                # Start Follow-up Scheduler
                from api.scheduler_followups import start_followup_scheduler
                start_followup_scheduler()
