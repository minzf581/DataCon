from django.views.generic import DetailView
from core.models import Dataset
from data_processing.services import DataProcessor

class DatasetDetailView(DetailView):
    model = Dataset
    template_name = 'datasets/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dataset = self.get_object()
        
        # 获取数据预览
        processor = DataProcessor(dataset)
        preview_data = processor.get_preview()
        
        context.update({
            'preview_data': preview_data,
            'statistics': processor.get_statistics(),
            'quality_metrics': processor.get_quality_metrics()
        })
        return context 