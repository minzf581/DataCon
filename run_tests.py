#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
import unittest
import coverage

def run_tests():
    """运行所有测试并生成覆盖率报告"""
    # 启动覆盖率统计
    cov = coverage.Coverage(
        source=['dc_core', 'dc_collector'],
        omit=['*/tests/*', '*/migrations/*']
    )
    cov.start()
    
    # 设置Django环境
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    django.setup()
    
    # 获取测试运行器
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # 运行测试
    failures = test_runner.run_tests(['tests'])
    
    # 停止覆盖率统计并生成报告
    cov.stop()
    cov.save()
    
    # 打印覆盖率报告
    print('\nCoverage Report:')
    cov.report()
    
    # 生成HTML报告
    cov.html_report(directory='coverage_html')
    
    return failures

if __name__ == '__main__':
    failures = run_tests()
    sys.exit(bool(failures)) 