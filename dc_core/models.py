from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Project(models.Model):
    """项目模型"""
    name = models.CharField(max_length=100, verbose_name='项目名称')
    description = models.TextField(blank=True, null=True, verbose_name='项目描述')
    objective = models.TextField(blank=True, null=True, verbose_name='项目目标')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', verbose_name='所有者')

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = '项目'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Dataset(models.Model):
    """数据集模型"""
    name = models.CharField(max_length=100, verbose_name='数据集名称')
    description = models.TextField(blank=True, null=True, verbose_name='数据集描述')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='datasets', null=True, blank=True, verbose_name='所属项目')
    format = models.CharField(max_length=50, blank=True, null=True, verbose_name='数据格式')
    size = models.IntegerField(default=0, verbose_name='数据大小')
    quality_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=50, default='pending')
    error_message = models.TextField(blank=True)
    external_id = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '数据集'
        verbose_name_plural = '数据集'
        ordering = ['-created_at']

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

class Task(models.Model):
    """任务模型"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败')
    )

    name = models.CharField(max_length=100, verbose_name='任务名称')
    description = models.TextField(blank=True, null=True, verbose_name='任务描述')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True, verbose_name='所属项目')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True, verbose_name='关联数据集')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='任务状态')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def start(self):
        """开始任务"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        """完成任务"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def fail(self):
        """标记任务失败"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.save() 