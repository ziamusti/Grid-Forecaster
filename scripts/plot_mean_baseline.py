"""Render saved pooled metrics as SVG; no training or dependencies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/mean_baseline_v1'
m = json.loads((REPORT / 'run.json').read_text())['pooled_metrics']
co2, ee = m['target_co2_gco2eq_kwh'], m['target_renewable_share_pct']
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620">',
         '<title>Durchschnittsbaseline: Kennzahlen 2018–2024</title>',
         '<rect width="1200" height="620" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#243449}.title{font-size:29px;font-weight:bold}.head{font-size:20px;font-weight:bold}.small{font-size:15px}.value{font-size:19px;font-weight:bold}</style>']


def text(x, y, s, css='small', anchor='start'):
    parts.append(f'<text x="{x}" y="{y}" class="{css}" text-anchor="{anchor}">{s}</text>')


text(40, 48, 'Durchschnittsbaseline · Deutschland', 'title')
text(40, 79, 'Validierung 2018–2024 · jeweils 3 Trainingsjahre → 1 Folgejahr')
panels = [
    ('CO₂-Intensität', 'Fehler in gCO₂eq/kWh', [('MAE', co2['mae']), ('RMSE', co2['rmse'])], 160, '#2671b9', False),
    ('Grünanteil', 'Fehler in Prozentpunkten', [('MAE', ee['mae']), ('RMSE', ee['rmse'])], 20, '#16846a', False),
    ('Bestimmtheitsmaß R²', 'Dimensionslos · 1 = perfekte Vorhersage', [('CO₂', co2['r2']), ('Grünanteil', ee['r2'])], 1, '#7357a5', True),
]
for index, (title, unit, values, maximum, color, is_r2) in enumerate(panels):
    x = 40 + 395 * index
    text(x, 143, title, 'head')
    text(x, 170, unit)
    left, bottom, height = x+48, 438, 210
    for tick in range(5):
        value = maximum*tick/4
        y = bottom-height*tick/4
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left+280}" y2="{y}" stroke="#dfe5ed"/>')
        text(left-10, y+5, f'{value:g}'.replace('.', ','), anchor='end')
    for j, (label, value) in enumerate(values):
        bx = left+32+138*j
        h = value/maximum*height
        parts.append(f'<rect x="{bx}" y="{bottom-h}" width="66" height="{h}" fill="{color}"/>')
        text(bx+33, bottom-h-12, f'{value:.3f}' .replace('.', ',') if is_r2 else f'{value:.2f}'.replace('.', ','), 'value', 'middle')
        text(bx+33, bottom+27, label, anchor='middle')
    text(x+48, 502, 'Höher ist besser' if is_r2 else 'Niedriger ist besser')
text(40, 555, 'Kennzahlen über alle gültigen Bewertungsstunden zusammen; kein Mittelwert der jährlichen R²-Werte.')
text(40, 581, f'CO₂: {co2["n"]:,} Stunden · Grünanteil: {ee["n"]:,} Stunden · 2025/2026 nicht bewertet.'.replace(',', '.'))
parts.append('</svg>')
output = REPORT / 'kennzahlen_diagramm.svg'
output.write_text('\n'.join(parts), encoding='utf-8')
print(output)
