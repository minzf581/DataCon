from django.views.generic import ListView
from core.models import Task

class TaskMonitorView(ListView):
    model = Task
    template_name = 'tasks/monitor.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return Task.objects.filter(
            project__owner=self.request.user
        ).select_related('project', 'input_dataset', 'output_dataset')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tasks'] = self.get_queryset().filter(
            status__in=['PENDING', 'RUNNING']
        )
        return context 