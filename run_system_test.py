#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
import unittest
import coverage

def run_system_tests():
    """运行系统测试并生成覆盖率报告"""
    # 启动覆盖率统计
    cov = coverage.Coverage(
        source=['dc_core', 'dc_collector', 'data_processing', 'dc_validation'],
        omit=['*/tests/*', '*/migrations/*']
    )
    cov.start()
    
    # 设置Django环境
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    django.setup()
    
    # 获取测试运行器
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # 运行系统测试
    test_module = 'tests.test_system'
    failures = test_runner.run_tests([test_module])
    
    # 停止覆盖率统计并生成报告
    cov.stop()
    cov.save()
    
    # 打印覆盖率报告
    print('\n覆盖率报告:')
    cov.report()
    
    # 生成HTML报告
    cov.html_report(directory='coverage_html')
    
    return failures

if __name__ == '__main__':
    failures = run_system_tests()
    sys.exit(bool(failures)) 