import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Feature, Plan, PlanFeature

FEATURES = [
    # Channels (4)
    {"key": "channel_whatsapp", "name": "WhatsApp", "category": "Channels", "feature_type": "Channel", "description": "Official WhatsApp Cloud API & automated conversations"},
    {"key": "channel_instagram", "name": "Instagram", "category": "Channels", "feature_type": "Channel", "description": "Instagram Direct automation & real-time messaging"},
    {"key": "channel_facebook", "name": "Facebook", "category": "Channels", "feature_type": "Channel", "description": "Facebook Messenger & page conversation sync"},
    {"key": "channel_youtube", "name": "YouTube", "category": "Channels", "feature_type": "Channel", "description": "YouTube comments, audience replies & engagement"},

    # Connectors (8)
    {"key": "connector_gmail", "name": "Gmail", "category": "Connectors", "feature_type": "Connector", "description": "Google Gmail workspace integration & email sync"},
    {"key": "connector_outlook", "name": "Microsoft Outlook", "category": "Connectors", "feature_type": "Connector", "description": "Microsoft Outlook email & enterprise calendar connector"},
    {"key": "connector_google_maps", "name": "Google Maps", "category": "Connectors", "feature_type": "Connector", "description": "Google Maps location intelligence & business verification"},
    {"key": "connector_google_docs", "name": "Google Docs", "category": "Connectors", "feature_type": "Connector", "description": "Google Docs templates & automated client documents"},
    {"key": "connector_onedrive", "name": "OneDrive", "category": "Connectors", "feature_type": "Connector", "description": "Microsoft OneDrive cloud storage & file synchronization"},
    {"key": "connector_google_sheets", "name": "Google Sheets", "category": "Connectors", "feature_type": "Connector", "description": "Google Sheets automated spreadsheets & live data export"},
    {"key": "connector_google_slides", "name": "Google Slides", "category": "Connectors", "feature_type": "Connector", "description": "Google Slides presentations & pitch deck creator"},
    {"key": "connector_google_news", "name": "Google News Feed", "category": "Connectors", "feature_type": "Connector", "description": "Google News live feed monitoring & real-time alerts"},

    # Features (9)
    {"key": "feature_team_dashboard", "name": "Team Dashboard", "category": "Features", "feature_type": "Module", "description": "Collaborative team workspace & performance dashboard"},
    {"key": "feature_quotation", "name": "Quotation", "category": "Features", "feature_type": "Module", "description": "Instant sales quotations, estimates & digital approvals"},
    {"key": "feature_invoice", "name": "Invoice", "category": "Features", "feature_type": "Module", "description": "Automated GST & tax invoicing with payment receipts"},
    {"key": "feature_proposal", "name": "Proposal", "category": "Features", "feature_type": "Module", "description": "Multi-page branded client business proposals"},
    {"key": "feature_catalog", "name": "Catalog", "category": "Features", "feature_type": "Module", "description": "Products & services catalog with pricing & SKUs"},
    {"key": "feature_payment", "name": "Payment", "category": "Features", "feature_type": "Module", "description": "Payment gateway integration, checkout links & transaction tracking"},
    {"key": "feature_crm", "name": "CRM", "category": "Features", "feature_type": "Module", "description": "Client directory, contact management & deal pipeline stages"},
    {"key": "feature_autoreply", "name": "Auto Reply", "category": "Features", "feature_type": "Module", "description": "Automated 24/7 instant replies & trigger bot flows"},
    {"key": "feature_voice_video_call", "name": "Voice / Video Call", "category": "Features", "feature_type": "Module", "description": "Integrated voice calling & video meeting capabilities"},
]

def seed():
    print("Clearing stale features...")
    # Keep only the valid 21 keys
    valid_keys = [f["key"] for f in FEATURES]
    Feature.objects.exclude(key__in=valid_keys).delete()

    created_or_updated = 0
    for feat_data in FEATURES:
        feat, _ = Feature.objects.update_or_create(
            key=feat_data["key"],
            defaults={
                "name": feat_data["name"],
                "category": feat_data["category"],
                "feature_type": feat_data["feature_type"],
                "description": feat_data["description"],
                "is_active": True,
            }
        )
        created_or_updated += 1

    print(f"Features in DB: {Feature.objects.count()} (Updated/Created: {created_or_updated})")

if __name__ == '__main__':
    seed()
