#!/usr/bin/env python3
"""Переносит блоки ответов из параграфов в файл ответов в конце части.

Канон (docs/style-guide.md, «Ответы — в конце части, не под вопросом»):
ответ, увиденный сразу после вопроса, отменяет припоминание. Поэтому ответы
уезжают из параграфа в отдельный файл NN-99_otvety.md.

Запуск из корня книги:  python3 migrate_otvety.py [--dry]
"""
import re, sys, glob, os, collections

DRY = "--dry" in sys.argv
ANSWER_HEAD = re.compile(r"^## Ответы[^\n]*$", re.M)

def split_answers(text):
    """Возвращает (текст без ответов, тело ответов) или (текст, None)."""
    m = ANSWER_HEAD.search(text)
    if not m:
        return text, None
    tail = text[m.end():]
    # ответы кончаются либо следующим ## , либо горизонтальной чертой перехода
    nxt = re.search(r"^## |^---\s*$", tail, re.M)
    end = m.end() + (nxt.start() if nxt else len(tail))
    body = text[m.end():end].strip("\n")
    return (text[:m.start()].rstrip("\n") + "\n\n" + text[end:].lstrip("\n")), body

parts = collections.defaultdict(list)
for f in sorted(glob.glob("chapters/*/*.md")):
    if re.search(r"-99_otvety\.md$", f):
        continue
    src = open(f, encoding="utf-8").read()
    rest, answers = split_answers(src)
    if answers is None:
        continue
    title = re.search(r"^# (.+)$", src, re.M).group(1).strip()
    parts[os.path.dirname(f)].append((f, title, answers))
    if not DRY:
        # после «Упражнений» ставим указание, где искать ответы
        rest = re.sub(r"\n+(---\n\n\*)", r"\n\nОтветы — в конце части.\n\n\1", rest, count=1)
        if "Ответы — в конце части." not in rest:
            rest = rest.rstrip("\n") + "\n\nОтветы — в конце части.\n"
        open(f, "w", encoding="utf-8").write(rest)

for d, items in sorted(parts.items()):
    num = os.path.basename(d).split("_")[0]
    out = os.path.join(d, f"{num}-99_otvety.md")
    part = re.sub(r"^§ (\d+)\..*", r"\1", items[0][1])
    lines = ["---", "status: draft", "---", "", f"# Ответы к части {part}", "",
             "Ответы собраны здесь, а не под вопросами: подсказка, увиденная сразу",
             "после вопроса, отменяет попытку вспомнить.", ""]
    for _, title, body in items:
        lines += [f"## {title}", "", body, ""]
    if not DRY:
        open(out, "w", encoding="utf-8").write("\n".join(lines).rstrip("\n") + "\n")
    print(f"{'[dry] ' if DRY else ''}{out}: {len(items)} параграфов, {sum(len(b.split()) for _,_,b in items)} слов")
