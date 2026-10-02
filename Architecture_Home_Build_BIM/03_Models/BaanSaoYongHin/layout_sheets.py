# -*- coding: utf-8 -*-
"""Rasterise the 2D drawing set (design/BaanSaoYongHin_Drawings.pdf) to one PNG per sheet for the LayOut export.

BaanSaoYongHin_LayOut.rb places these PNGs as full-page images after the model-viewport sheets
(the LayOut Ruby API cannot insert PDF pages). Needs pdftoppm (poppler-utils)."""
import os, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(HERE, 'design', 'BaanSaoYongHin_Drawings.pdf')
OUT = os.path.join(HERE, 'layout_sheets')
SHEETS = ['S-01', 'S-02', 'S-03', 'E-01', 'E-02', 'E-03']   # page order of drawings.py
DPI = 150

def main():
    if not shutil.which('pdftoppm'):
        raise SystemExit('pdftoppm not found (apt install poppler-utils)')
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith('.png'):
            os.remove(os.path.join(OUT, f))
    for i, name in enumerate(SHEETS, 1):
        subprocess.run(['pdftoppm', '-png', '-r', str(DPI), '-f', str(i), '-l', str(i), '-singlefile',
                        PDF, os.path.join(OUT, name)], check=True)
    print('layout_sheets/: %d PNG at %d dpi' % (len(SHEETS), DPI))

if __name__ == '__main__':
    main()
