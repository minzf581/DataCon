from django.views.generic import TemplateView
from evaluation.services import PerformanceEvaluator
from feedback.services import FeedbackOptimizer

class PerformanceAnalysisView(TemplateView):
    template_name = 'performance/analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs['project_id']
        
        # 获取性能数据
        optimizer = FeedbackOptimizer(project_id)
        performance_data = optimizer.get_performance_history()
        
        context.update({
            'performance_data': performance_data,
            'recommendations': optimizer.get_latest_recommendations()
        })
        return context 