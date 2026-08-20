import re

with open('api/views/super_admin_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block 2
block2_old = """        # ── 2. Messages & Chat Analytics ────────────────────────────────────────
        client_msgs = client.messages.all()
        total_msgs = client_msgs.count()
        msgs_sent = client_msgs.filter(message_type='OUTGOING').count()
        msgs_received = client_msgs.filter(message_type='INCOMING').count()
        bot_msgs = client_msgs.filter(sender_user__isnull=True).count()
        human_replies = client_msgs.filter(sender_user__isnull=False).count()
        msgs_today = client_msgs.filter(created_at__gte=today_start).count()
        msgs_this_week = client_msgs.filter(created_at__gte=seven_days_ago).count()
        msgs_this_month = client_msgs.filter(created_at__gte=month_start).count()

        client_convos = client.conversations.all()
        total_convos = client_convos.count()
        active_convos = client_convos.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
        closed_convos = client_convos.filter(status__in=['CLOSED', 'RESOLVED']).count()
        unread_convos = client_convos.filter(Q(unread_count_admin__gt=0) | Q(unread_count_employee__gt=0)).count()"""

block2_new = """        # ── 2. Messages & Chat Analytics ────────────────────────────────────────
        client_msgs = client.messages.all()
        msg_stats = client_msgs.aggregate(
            total_msgs=Count('id'),
            msgs_sent=Count('id', filter=Q(message_type='OUTGOING')),
            msgs_received=Count('id', filter=Q(message_type='INCOMING')),
            bot_msgs=Count('id', filter=Q(sender_user__isnull=True)),
            human_replies=Count('id', filter=Q(sender_user__isnull=False)),
            msgs_today=Count('id', filter=Q(created_at__gte=today_start)),
            msgs_this_week=Count('id', filter=Q(created_at__gte=seven_days_ago)),
            msgs_this_month=Count('id', filter=Q(created_at__gte=month_start)),
        )
        total_msgs = msg_stats['total_msgs']
        msgs_sent = msg_stats['msgs_sent']
        msgs_received = msg_stats['msgs_received']
        bot_msgs = msg_stats['bot_msgs']
        human_replies = msg_stats['human_replies']
        msgs_today = msg_stats['msgs_today']
        msgs_this_week = msg_stats['msgs_this_week']
        msgs_this_month = msg_stats['msgs_this_month']

        client_convos = client.conversations.all()
        convo_stats = client_convos.aggregate(
            total_convos=Count('id'),
            active_convos=Count('id', filter=Q(status__in=['OPEN', 'IN_PROGRESS'])),
            closed_convos=Count('id', filter=Q(status__in=['CLOSED', 'RESOLVED'])),
            unread_convos=Count('id', filter=Q(unread_count_admin__gt=0) | Q(unread_count_employee__gt=0)),
        )
        total_convos = convo_stats['total_convos']
        active_convos = convo_stats['active_convos']
        closed_convos = convo_stats['closed_convos']
        unread_convos = convo_stats['unread_convos']"""

content = content.replace(block2_old, block2_new)


# WhatsApp block
wa_old = """        # ── 4. WhatsApp Specific Analytics (Section 5) ───────────────────────────
        wa_msgs = client_msgs.filter(channel='WHATSAPP')
        wa_convos = client_convos.filter(channel='WHATSAPP')
        wa_incoming = wa_msgs.filter(message_type='INCOMING').count()
        wa_outgoing = wa_msgs.filter(message_type='OUTGOING').count()
        wa_bot_replies = wa_msgs.filter(sender_user__isnull=True).count()
        wa_human_replies = wa_msgs.filter(sender_user__isnull=False).count()
        wa_bot_handled_convos = wa_convos.filter(assigned_to__isnull=True).count()
        wa_human_handled_convos = wa_convos.filter(assigned_to__isnull=False).count()
        wa_unanswered = wa_convos.filter(Q(unread_count_admin__gt=0) | Q(unread_count_employee__gt=0)).count()
        wa_active = wa_convos.filter(status__in=['OPEN', 'IN_PROGRESS']).count()
        wa_closed = wa_convos.filter(status__in=['CLOSED', 'RESOLVED']).count()"""

wa_new = """        # ── 4. WhatsApp Specific Analytics (Section 5) ───────────────────────────
        wa_msgs = client_msgs.filter(channel='WHATSAPP')
        wa_convos = client_convos.filter(channel='WHATSAPP')
        
        wa_stats = wa_convos.aggregate(
            wa_bot_handled_convos=Count('id', filter=Q(assigned_to__isnull=True)),
            wa_human_handled_convos=Count('id', filter=Q(assigned_to__isnull=False)),
            wa_unanswered=Count('id', filter=Q(unread_count_admin__gt=0) | Q(unread_count_employee__gt=0)),
            wa_active=Count('id', filter=Q(status__in=['OPEN', 'IN_PROGRESS'])),
            wa_closed=Count('id', filter=Q(status__in=['CLOSED', 'RESOLVED'])),
        )
        wa_bot_handled_convos = wa_stats['wa_bot_handled_convos']
        wa_human_handled_convos = wa_stats['wa_human_handled_convos']
        wa_unanswered = wa_stats['wa_unanswered']
        wa_active = wa_stats['wa_active']
        wa_closed = wa_stats['wa_closed']
        
        wa_msg_stats = wa_msgs.aggregate(
            wa_incoming=Count('id', filter=Q(message_type='INCOMING')),
            wa_outgoing=Count('id', filter=Q(message_type='OUTGOING')),
            wa_bot_replies=Count('id', filter=Q(sender_user__isnull=True)),
            wa_human_replies=Count('id', filter=Q(sender_user__isnull=False)),
        )
        wa_incoming = wa_msg_stats['wa_incoming']
        wa_outgoing = wa_msg_stats['wa_outgoing']
        wa_bot_replies = wa_msg_stats['wa_bot_replies']
        wa_human_replies = wa_msg_stats['wa_human_replies']"""

content = content.replace(wa_old, wa_new)

# Facebook Block
fb_old = """        # ── 5. Facebook Analytics (Section 6) ───────────────────────────────────
        fb_msgs = client_msgs.filter(channel='FACEBOOK')
        fb_convos = client_convos.filter(channel='FACEBOOK')
        fb_incoming = fb_msgs.filter(message_type='INCOMING').count()
        fb_outgoing = fb_msgs.filter(message_type='OUTGOING').count()
        fb_bot_replies = fb_msgs.filter(sender_user__isnull=True).count()
        fb_human_replies = fb_msgs.filter(sender_user__isnull=False).count()"""

fb_new = """        # ── 5. Facebook Analytics (Section 6) ───────────────────────────────────
        fb_msgs = client_msgs.filter(channel='FACEBOOK')
        fb_convos = client_convos.filter(channel='FACEBOOK')
        fb_msg_stats = fb_msgs.aggregate(
            fb_incoming=Count('id', filter=Q(message_type='INCOMING')),
            fb_outgoing=Count('id', filter=Q(message_type='OUTGOING')),
            fb_bot_replies=Count('id', filter=Q(sender_user__isnull=True)),
            fb_human_replies=Count('id', filter=Q(sender_user__isnull=False)),
        )
        fb_incoming = fb_msg_stats['fb_incoming']
        fb_outgoing = fb_msg_stats['fb_outgoing']
        fb_bot_replies = fb_msg_stats['fb_bot_replies']
        fb_human_replies = fb_msg_stats['fb_human_replies']"""

content = content.replace(fb_old, fb_new)

# Instagram Block
ig_old = """        # ── 6. Instagram Analytics (Section 7) ──────────────────────────────────
        ig_msgs = client_msgs.filter(channel='INSTAGRAM')
        ig_convos = client_convos.filter(channel='INSTAGRAM')
        ig_incoming = ig_msgs.filter(message_type='INCOMING').count()
        ig_outgoing = ig_msgs.filter(message_type='OUTGOING').count()
        ig_bot_replies = ig_msgs.filter(sender_user__isnull=True).count()
        ig_human_replies = ig_msgs.filter(sender_user__isnull=False).count()"""

ig_new = """        # ── 6. Instagram Analytics (Section 7) ──────────────────────────────────
        ig_msgs = client_msgs.filter(channel='INSTAGRAM')
        ig_convos = client_convos.filter(channel='INSTAGRAM')
        ig_msg_stats = ig_msgs.aggregate(
            ig_incoming=Count('id', filter=Q(message_type='INCOMING')),
            ig_outgoing=Count('id', filter=Q(message_type='OUTGOING')),
            ig_bot_replies=Count('id', filter=Q(sender_user__isnull=True)),
            ig_human_replies=Count('id', filter=Q(sender_user__isnull=False)),
        )
        ig_incoming = ig_msg_stats['ig_incoming']
        ig_outgoing = ig_msg_stats['ig_outgoing']
        ig_bot_replies = ig_msg_stats['ig_bot_replies']
        ig_human_replies = ig_msg_stats['ig_human_replies']"""

content = content.replace(ig_old, ig_new)

with open('api/views/super_admin_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Optimization pass 1 completed.")
