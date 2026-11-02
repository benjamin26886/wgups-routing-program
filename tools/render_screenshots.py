# Helper (not part of the graded program): runs main.py with scripted menu
# input and renders the real console output as terminal-style PNG screenshots.
import os
import re
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'screenshots')
os.makedirs(OUT, exist_ok=True)

PROMPT = re.compile(r'(Enter your choice \(1-4\): |24-hour\): |\(1-40\): )')


def run(inputs):
    # Feed the inputs to main.py and re-insert them after each prompt, the way a
    # terminal would echo what the user typed.
    result = subprocess.run([sys.executable, os.path.join(ROOT, 'main.py')],
                            input='\n'.join(inputs) + '\n', capture_output=True,
                            text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert result.stderr == '', result.stderr
    parts = PROMPT.split(result.stdout)
    text, it = '', iter(inputs)
    for part in parts:
        text += part
        if PROMPT.fullmatch(part):
            text += next(it, '') + '\n'
    return text.rstrip('\n').split('\n')


def render(lines, name, title):
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 15)
    bar = 34
    cw = font.getlength('M')
    lh = 20
    width = int(max(len(l) for l in lines) * cw + 40)
    height = bar + lh * (len(lines) + 1) + 24
    img = Image.new('RGB', (width, height), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, bar], fill=(58, 58, 58))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([14 + i * 22, 11, 26 + i * 22, 23], fill=c)
    d.text((width // 2, 17), title, font=font, fill=(200, 200, 200), anchor='mm')
    y = bar + 12
    for line in lines:
        d.text((20, y), line, font=font, fill=(230, 230, 230))
        y += lh
    img.save(os.path.join(OUT, name))
    print('saved', name, img.size)


cmd = 'python3 main.py'
shots = [
    ('D1_status_0900.png', ['1', '09:00:00', '4'], 'D1: all packages at 09:00 (between 8:35 and 9:25)'),
    ('D2_status_1000.png', ['1', '10:00:00', '4'], 'D2: all packages at 10:00 (between 9:35 and 10:25)'),
    ('D3_status_1215.png', ['1', '12:15:00', '4'], 'D3: all packages at 12:15 (between 12:03 and 1:12)'),
    ('E_total_mileage.png', ['3', '4'], 'E: total mileage traveled by all trucks'),
    ('single_package_lookup.png', ['2', '10:00:00', '9', '2', '10:25:00', '9', '4'], 'Single package look-up (Package 9 before / after 10:20)'),
]
for name, inputs, title in shots:
    render(run(inputs), name, f'main.py - {title}')
