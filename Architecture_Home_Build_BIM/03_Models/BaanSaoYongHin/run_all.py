# -*- coding: utf-8 -*-
"""Rebuild everything in order: model -> design -> model -> design (sizes settle) -> model -> BOQ/plan/tracker data -> report PDF -> drawings PDF -> PNG sheets for the LayOut export."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for step in ('make_model.py', 'design_calc.py', 'make_model.py', 'design_calc.py', 'make_model.py', 'boq.py', 'design_report.py', 'drawings.py', 'layout_sheets.py'):
    print('==', step)
    subprocess.run([sys.executable, os.path.join(HERE, step)], check=True, cwd=HERE)
