# -*- coding: utf-8 -*-
"""Rebuild everything in order: model -> design -> model with designed sizes -> BOQ/plan/tracker data -> report PDF."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for step in ('make_model.py', 'design_calc.py', 'make_model.py', 'boq.py', 'design_report.py'):
    print('==', step)
    subprocess.run([sys.executable, os.path.join(HERE, step)], check=True, cwd=HERE)
