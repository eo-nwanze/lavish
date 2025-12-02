#!/usr/bin/env python
"""
Test runner for Orders and Fulfillment API
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lavish_backend.settings')
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True, keepdb=False)
    
    # Run tests for orders and shipping apps
    failures = test_runner.run_tests([
        'orders.tests',
        'shipping.tests',
    ])
    
    if failures:
        sys.exit(1)
    else:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)