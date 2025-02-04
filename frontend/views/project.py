from django.views.generic import TemplateView
from core.models import Project

class ProjectDashboardView(TemplateView):
    template_name = 'projects/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.filter(owner=self.request.user)
        return context 