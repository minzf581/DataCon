from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Project(models.Model):
    """项目模型"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    objective = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')

    def __str__(self):
        return self.name

class Dataset(models.Model):
    """数据集模型"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='datasets', null=True)
    format = models.CharField(max_length=50)
    size = models.IntegerField(default=0)
    quality_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, default='pending')
    error_message = models.TextField(blank=True)
    external_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class DataRequirement(models.Model):
    """数据需求模型"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requirements')
    description = models.TextField()
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"需求 {self.id} - {self.project.name}"

class AgentPerformance(models.Model):
    """智能体性能记录模型"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='performances')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='performances')
    metrics = models.JSONField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"性能记录 {self.id} - {self.dataset.name}"

class DataQualityMetric(models.Model):
    """数据质量指标模型"""
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='quality_metrics')
    completeness_score = models.FloatField("完整性分数", validators=[MinValueValidator(0), MaxValueValidator(1)], default=0.0)
    consistency_score = models.FloatField("一致性分数", validators=[MinValueValidator(0), MaxValueValidator(1)], default=0.0)
    accuracy_score = models.FloatField("准确性分数", validators=[MinValueValidator(0), MaxValueValidator(1)], default=0.0)
    total_score = models.FloatField("总分", validators=[MinValueValidator(0), MaxValueValidator(1)], default=0.0)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "质量指标"
        verbose_name_plural = "质量指标"
        
    def __str__(self):
        return f"{self.dataset.name} - 质量评分: {self.total_score}" 