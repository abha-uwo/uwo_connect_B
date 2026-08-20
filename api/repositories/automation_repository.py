from ..models import Automation, Workflow, WorkflowSession

class AutomationRepository:
    @staticmethod
    def filter_automations(**kwargs):
        return Automation.objects.filter(**kwargs)
        
    @staticmethod
    def get_automation(id=None, trigger_word=None, client=None):
        if trigger_word and client:
            return Automation.objects.filter(trigger_word=trigger_word, client=client).first()
        return Automation.objects.filter(id=id).first()

    @staticmethod
    def get_all_automations():
        return Automation.objects.all()

    @staticmethod
    def get_all():
        return Automation.objects.all()

class WorkflowRepository:
    @staticmethod
    def filter_workflows(**kwargs):
        return Workflow.objects.filter(**kwargs)
        
    @staticmethod
    def get_workflow(id=None, trigger_word=None, client=None):
        if trigger_word and client:
            return Workflow.objects.filter(trigger_word=trigger_word, client=client).first()
        return Workflow.objects.filter(id=id).first()

class WorkflowSessionRepository:
    @staticmethod
    def filter_sessions(**kwargs):
        return WorkflowSession.objects.filter(**kwargs)
        
    @staticmethod
    def get_session(contact, workflow, is_active=True):
        return WorkflowSession.objects.filter(contact=contact, workflow=workflow, is_active=is_active).first()
        
    @staticmethod
    def create_session(**kwargs):
        return WorkflowSession.objects.create(**kwargs)

    @staticmethod
    def filter_workflowsessions(**kwargs):
        return WorkflowSession.objects.filter(**kwargs)

    @staticmethod
    def create_workflowsession(**kwargs):
        return WorkflowSession.objects.create(**kwargs)
