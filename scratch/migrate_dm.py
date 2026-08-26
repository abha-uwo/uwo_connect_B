import os, sys, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import User, TeamChannel, TeamChatMessage

u1 = User.objects.get(email='abha@uwo24.com')
u2 = User.objects.get(email='devansh@uwo24.com')

slug1 = (u1.username or u1.email).lower().replace('@', '-').replace('.', '-')
slug2 = (u2.username or u2.email).lower().replace('@', '-').replace('.', '-')
pair = sorted([slug1, slug2])
shared_slug = f"dm-{pair[0]}_{pair[1]}"

shared_ch, created = TeamChannel.objects.get_or_create(
    client=u1.client,
    name=shared_slug,
    defaults={
        'description': f"Direct message between {u1.username} and {u2.username}",
        'channel_type': 'DIRECT',
        'created_by': u1
    }
)
shared_ch.members.set([u1, u2])
print('SHARED CHANNEL:', shared_ch.id, shared_ch.name)

old_channels = list(TeamChannel.objects.filter(name__in=['dm-abha-uwo24-com', 'dm-devansh-uwo24-com']))
count = 0
for och in old_channels:
    for m in TeamChatMessage.objects.filter(channel_id=och.id):
        m.channel = shared_ch
        m.save()
        count += 1
    och.delete()

print(f"Migrated {count} messages into {shared_ch.name}")
print("ALL CHANNELS NOW:")
for c in TeamChannel.objects.all():
    print(c.id, c.name, c.channel_type)

print("MESSAGES IN SHARED CHANNEL:")
for m in TeamChatMessage.objects.filter(channel=shared_ch):
    print(m.id, m.sender.username, m.text)
