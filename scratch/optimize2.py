import re

with open('api/views/super_admin_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

wa_drill_old = """        # WhatsApp conversation drill-down
        wa_conversation_list = []
        for convo in wa_convos.order_by('-updated_at')[:25]:
            thread_msgs = list(Message.objects.filter(conversation=convo).order_by('-created_at')[:10])
            last_m = thread_msgs[0] if thread_msgs else None
            recent_thread = []
            for m in thread_msgs:
                recent_thread.append({
                    "id": str(m.id),
                    "sender": "AI Bot" if m.sender_user is None else (m.sender_name or safe_get_relation_attr(m, 'sender_user', 'username', 'Customer')),
                    "is_bot": m.sender_user is None,
                    "body": m.body,
                    "timestamp": m.created_at.isoformat(),
                    "type": m.message_type
                })
            wa_conversation_list.append({
                "id": str(convo.id),
                "customer_name": safe_get_relation_attr(convo, 'contact', 'name', getattr(convo, 'customer_phone', "Customer") if hasattr(convo, 'customer_phone') else "Customer"),
                "customer_phone": safe_get_relation_attr(convo, 'contact', 'phone_number', getattr(convo, 'customer_phone', "—") if hasattr(convo, 'customer_phone') else "—"),
                "status": convo.status,
                "assigned_to": safe_get_relation_attr(convo, 'assigned_to', 'username', 'Unassigned (Bot)'),
                "unread_count": convo.unread_count_admin + convo.unread_count_employee,
                "last_message": last_m.body if last_m else "",
                "last_message_time": (last_m.created_at if last_m else convo.updated_at).isoformat(),
                "thread": list(reversed(recent_thread))
            })"""

wa_drill_new = """        # WhatsApp conversation drill-down
        wa_convos_qs = wa_convos.select_related('contact', 'assigned_to').order_by('-updated_at')[:25]
        wa_convo_ids = [c.id for c in wa_convos_qs]
        
        recent_msgs = Message.objects.filter(conversation_id__in=wa_convo_ids).select_related('sender_user').order_by('-created_at')[:250]
        from collections import defaultdict
        convo_msg_map = defaultdict(list)
        for m in recent_msgs:
            if len(convo_msg_map[m.conversation_id]) < 10:
                convo_msg_map[m.conversation_id].append(m)
                
        wa_conversation_list = []
        for convo in wa_convos_qs:
            thread_msgs = convo_msg_map[convo.id]
            last_m = thread_msgs[0] if thread_msgs else None
            recent_thread = []
            for m in thread_msgs:
                recent_thread.append({
                    "id": str(m.id),
                    "sender": "AI Bot" if m.sender_user is None else (m.sender_name or safe_get_relation_attr(m, 'sender_user', 'username', 'Customer')),
                    "is_bot": m.sender_user is None,
                    "body": m.body,
                    "timestamp": m.created_at.isoformat(),
                    "type": m.message_type
                })
            
            cust_name = "Customer"
            cust_phone = "—"
            if hasattr(convo, 'customer_phone'):
                cust_name = getattr(convo, 'customer_phone', "Customer")
                cust_phone = getattr(convo, 'customer_phone', "—")
                
            wa_conversation_list.append({
                "id": str(convo.id),
                "customer_name": safe_get_relation_attr(convo, 'contact', 'name', cust_name),
                "customer_phone": safe_get_relation_attr(convo, 'contact', 'phone_number', cust_phone),
                "status": convo.status,
                "assigned_to": safe_get_relation_attr(convo, 'assigned_to', 'username', 'Unassigned (Bot)'),
                "unread_count": convo.unread_count_admin + convo.unread_count_employee,
                "last_message": last_m.body if last_m else "",
                "last_message_time": (last_m.created_at if last_m else convo.updated_at).isoformat(),
                "thread": list(reversed(recent_thread))
            })"""

content = content.replace(wa_drill_old, wa_drill_new)

with open('api/views/super_admin_views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Optimization pass 2 completed.")
