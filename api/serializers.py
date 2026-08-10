from rest_framework import serializers
from .models import User, Client, Automation, Workflow, GlobalSetting, Contact, Template, Campaign, SupportMessage, AuditLog, TeamInvite, KnowledgeDocument, TeamMessage, Product, Order, Project, Task, TaskComment, WorkReport, WorkApproval, TeamChannel, TeamChatMessage, Attendance, LeaveRequest, Message, Conversation, ConversationAuditLog, Guide, GuideSection, GuideStep, GuideProgress, EmailAccount, EmailMessage, EmailAutoReplyRule, EmailAutomationWorkflow, EmailTeamNote
from .repositories.contact_repository import ContactRepository
from .repositories.workflow_repository import WorkflowRepository
from .repositories.automation_repository import AutomationRepository
from .repositories.user_repository import UserRepository
from .repositories.team_invite_repository import TeamInviteRepository
from .repositories.client_repository import ClientRepository

class ObjectIdField(serializers.Field):
    """
    Custom field that serializes MongoDB ObjectId to a plain string
    and deserializes a string back to an ObjectId-compatible value.
    """
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
        return data


class ClientSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    _id = serializers.SerializerMethodField()
    total_contacts = serializers.SerializerMethodField()
    total_workflows = serializers.SerializerMethodField()
    total_bots = serializers.SerializerMethodField()
    onedrive_config = serializers.SerializerMethodField()
    google_calendar_config = serializers.SerializerMethodField()
    google_sheets_config = serializers.SerializerMethodField()
    google_docs_config = serializers.SerializerMethodField()
    google_slides_config = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = '__all__'

    def get__id(self, obj):
        return str(obj.id)

    def get_total_contacts(self, obj):
        from .models import Contact
        return ContactRepository.filter_contacts(client=obj).count()

    def get_total_workflows(self, obj):
        from .models import Workflow
        return WorkflowRepository.filter_workflows(client=obj).count()

    def get_total_bots(self, obj):
        from .models import Automation
        return AutomationRepository.filter_automations(client=obj).count()

    def get_onedrive_config(self, obj):
        """Return OneDrive config without sensitive OAuth tokens."""
        config = obj.onedrive_config or {}
        safe_keys = {
            'account_name', 'account_email', 'drive_id', 'drive_name',
            'drive_type', 'storage_total', 'storage_used', 'web_url',
            'last_sync_time', 'connected_at', 'synced_count',
            'pending_count', 'failed_count',
        }
        return {k: v for k, v in config.items() if k in safe_keys}

    def get_google_calendar_config(self, obj):
        """Return Google Calendar config without sensitive OAuth tokens."""
        config = obj.google_calendar_config or {}
        safe_keys = {
            'account_email', 'primary_calendar_id', 'timezone',
            'auto_sync_whatsapp', 'auto_sync_crm', 'default_duration',
            'last_sync_time', 'connected_at', 'events_count',
        }
        return {k: v for k, v in config.items() if k in safe_keys}

    def get_google_sheets_config(self, obj):
        """Return Google Sheets config without sensitive OAuth tokens."""
        config = obj.google_sheets_config or {}
        safe_keys = {
            'account_email', 'spreadsheet_id', 'spreadsheet_name',
            'sheet_name', 'spreadsheet_url', 'auto_export_leads',
            'auto_export_orders', 'auto_export_crm', 'rows_synced',
            'last_sync_time', 'connected_at',
        }
        return {k: v for k, v in config.items() if k in safe_keys}

    def get_google_docs_config(self, obj):
        """Return Google Docs config without sensitive OAuth tokens."""
        config = obj.google_docs_config or {}
        safe_keys = {
            'account_email', 'default_doc_id', 'default_doc_name',
            'default_doc_url', 'auto_generate_summaries',
            'auto_generate_receipts', 'docs_created_count',
            'last_sync_time', 'connected_at', 'recent_docs',
        }
        return {k: v for k, v in config.items() if k in safe_keys}

    def get_google_slides_config(self, obj):
        """Return Google Slides config without sensitive OAuth tokens."""
        config = obj.google_slides_config or {}
        safe_keys = {
            'account_email', 'default_presentation_id', 'default_presentation_name',
            'default_presentation_url', 'auto_generate_pitch_decks',
            'auto_generate_catalog_decks', 'presentations_created_count',
            'last_sync_time', 'connected_at', 'recent_presentations',
        }
        return {k: v for k, v in config.items() if k in safe_keys}


class UserSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    name = serializers.CharField(source='first_name', required=False)
    reporting_manager_name = serializers.ReadOnlyField(source='reporting_manager.username')

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'name', 'first_name', 'role', 'enterprise_role', 'department',
            'designation', 'reporting_manager', 'reporting_manager_name', 'status', 'client',
            'permissions', 'assigned_platforms', 'assigned_social_channels', 'permission_matrix',
            'employee_id', 'joining_date', 'working_hours', 'salary_visibility', 'skills',
            'availability_status', 'is_online', 'last_active_at', 'timezone', 'language',
            'current_page', 'last_login_ip', 'last_login_browser', 'last_login_os', 'login_history'
        )
        extra_kwargs = {'password': {'write_only': True}}

class TeamInviteSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = TeamInvite
        fields = '__all__'
        read_only_fields = ('client', 'token', 'created_at', 'is_used')


class AutomationSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Automation
        fields = '__all__'
        read_only_fields = ('client',)


class WorkflowSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Workflow
        fields = '__all__'
        read_only_fields = ('client',)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField()
    businessName = serializers.CharField(required=False, allow_blank=True)
    invite_token = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        email = value.lower().strip()
        if UserRepository.filter_users(email=email).exists() or UserRepository.filter_users(username=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def create(self, validated_data):
        email = validated_data['email'].lower().strip()
        business_name = validated_data.get('businessName', f"{validated_data['name']}'s Business")
        invite_token = validated_data.get('invite_token')

        if invite_token:
            from django.utils import timezone
            invite = TeamInviteRepository.filter_teaminvites(
                token=invite_token, 
                is_used=False, 
                expires_at__gt=timezone.now()
            ).first()
            
            if not invite:
                raise serializers.ValidationError({"invite_token": "Invalid or expired invite token."})
                
            user = User.objects.create_user(
                username=email,
                email=email,
                password=validated_data['password'],
                first_name=validated_data['name'],
                role='AGENT',
                status='APPROVED',
                client=invite.client,
                permissions=invite.permissions
            )
            
            invite.is_used = True
            invite.save()
            return user
        else:
            client = Client.objects.create(business_name=business_name)
    
            user = User.objects.create_user(
                username=email,
                email=email,
                password=validated_data['password'],
                first_name=validated_data['name'],
                role='CLIENT',
                status='PENDING',
                client=client
            )
            return user


class GlobalSettingSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = GlobalSetting
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ('client', 'created_at', 'updated_at')

class TemplateSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Template
        fields = '__all__'
        read_only_fields = ('client', 'created_at', 'updated_at')

class CampaignSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ('client', 'created_at', 'updated_at')

class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    
    class Meta:
        model = KnowledgeDocument
        fields = '__all__'
        read_only_fields = ('client', 'uploaded_at', 'status')

class SupportMessageSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    sender = ObjectIdField(read_only=True)
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_role = serializers.ReadOnlyField(source='sender.role')

    class Meta:
        model = SupportMessage
        fields = '__all__'
        read_only_fields = ('sender', 'client')

class AuditLogSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'

class TeamMessageSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    sender = ObjectIdField(read_only=True)
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_role = serializers.ReadOnlyField(source='sender.role')

    class Meta:
        model = TeamMessage
        fields = '__all__'
        read_only_fields = ('sender', 'client', 'created_at')


class ProductSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('client',)


class OrderSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    contact_name = serializers.ReadOnlyField(source='contact.name')
    contact_phone = serializers.ReadOnlyField(source='contact.phone_number')

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('client',)


class TaskCommentSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    author_name = serializers.ReadOnlyField(source='author.username')
    author_role = serializers.ReadOnlyField(source='author.enterprise_role')

    class Meta:
        model = TaskComment
        fields = '__all__'
        read_only_fields = ('author', 'created_at')


class TaskSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    comments = TaskCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('client', 'created_by', 'created_at', 'updated_at')


class WorkReportSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    employee_name = serializers.ReadOnlyField(source='employee.username')
    employee_department = serializers.ReadOnlyField(source='employee.department')

    class Meta:
        model = WorkReport
        fields = '__all__'
        read_only_fields = ('client', 'employee', 'created_at')


class WorkApprovalSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    task_title = serializers.ReadOnlyField(source='task.title')
    employee_name = serializers.ReadOnlyField(source='employee.username')
    reviewer_name = serializers.ReadOnlyField(source='reviewer.username')

    class Meta:
        model = WorkApproval
        fields = '__all__'
        read_only_fields = ('employee', 'submitted_at', 'reviewed_at')


class TeamChannelSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = TeamChannel
        fields = '__all__'
        read_only_fields = ('client', 'created_by', 'created_at')

    def get_member_count(self, obj):
        return obj.members.count()


class TeamChatMessageSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_role = serializers.ReadOnlyField(source='sender.enterprise_role')

    class Meta:
        model = TeamChatMessage
        fields = '__all__'
        read_only_fields = ('sender', 'created_at')


class ProjectSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.username')
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('client', 'owner', 'created_at', 'updated_at')

    def get_task_count(self, obj):
        return obj.tasks.count()


class AttendanceSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ('client', 'user', 'created_at')


class LeaveRequestSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    user_name = serializers.ReadOnlyField(source='user.username')
    reviewer_name = serializers.ReadOnlyField(source='reviewed_by.username')

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ('client', 'user', 'created_at')


class ConversationSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    assigned_to_name = serializers.ReadOnlyField(source='assigned_to.username')
    assigned_to_avatar = serializers.SerializerMethodField()
    locked_by_name = serializers.ReadOnlyField(source='locked_by.username')
    contact_name = serializers.SerializerMethodField()
    contact_phone = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ('client', 'created_at', 'updated_at')

    def get_assigned_to_avatar(self, obj):
        if obj.assigned_to and hasattr(obj.assigned_to, 'username'):
            return f"https://api.dicebear.com/7.x/avataaars/svg?seed={obj.assigned_to.username}"
        return None

    def get_contact_name(self, obj):
        if obj.contact:
            return obj.contact.name or obj.contact.phone_number or obj.contact_platform_id
        return obj.contact_platform_id

    def get_contact_phone(self, obj):
        if obj.contact:
            return obj.contact.phone_number
        return None


class ConversationAuditLogSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = ConversationAuditLog
        fields = '__all__'
        read_only_fields = ('client', 'created_at')


class MessageSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('client', 'created_at')


class GuideStepSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = GuideStep
        fields = '__all__'


class GuideSectionSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    steps = GuideStepSerializer(many=True, read_only=True)

    class Meta:
        model = GuideSection
        fields = '__all__'


class GuideListSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    total_sections = serializers.SerializerMethodField()
    total_steps = serializers.SerializerMethodField()

    class Meta:
        model = Guide
        fields = ['id', 'slug', 'title', 'icon', 'category', 'status', 'description', 'estimated_time', 'order', 'language', 'version', 'total_sections', 'total_steps']

    def get_total_sections(self, obj):
        return obj.sections.count()

    def get_total_steps(self, obj):
        return GuideStep.objects.filter(section__guide=obj).count()


class GuideDetailSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    sections = GuideSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Guide
        fields = '__all__'


class GuideProgressSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)

    class Meta:
        model = GuideProgress
        fields = '__all__'
        read_only_fields = ('user',)


# ── ENTERPRISE EMAIL CENTER SERIALIZERS ────────────────────────────────────

class EmailAccountSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = EmailAccount
        fields = '__all__'
        read_only_fields = ('client', 'created_at')


class EmailTeamNoteSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    author_name = serializers.CharField(source='author.first_name', read_only=True)

    class Meta:
        model = EmailTeamNote
        fields = '__all__'
        read_only_fields = ('author', 'created_at')


class EmailMessageSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.first_name', read_only=True)
    account_provider = serializers.CharField(source='account.provider', read_only=True)
    team_notes = EmailTeamNoteSerializer(many=True, read_only=True)

    class Meta:
        model = EmailMessage
        fields = '__all__'
        read_only_fields = ('client', 'created_at', 'updated_at')


class EmailAutoReplyRuleSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)

    class Meta:
        model = EmailAutoReplyRule
        fields = '__all__'
        read_only_fields = ('client', 'created_at')


class EmailAutomationWorkflowSerializer(serializers.ModelSerializer):
    id = ObjectIdField(read_only=True)
    client = ObjectIdField(read_only=True)
    assign_user_name = serializers.CharField(source='assign_user.first_name', read_only=True)

    class Meta:
        model = EmailAutomationWorkflow
        fields = '__all__'
        read_only_fields = ('client', 'created_at')






