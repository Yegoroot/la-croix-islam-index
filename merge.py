#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ann_p = os.path.join(HERE, "annotations.json")
new_p = os.path.join(HERE, "new_entries.json")
ann = json.load(open(ann_p, encoding="utf-8")) if os.path.exists(ann_p) else {}
new = json.load(open(new_p, encoding="utf-8"))
ann.update(new)
json.dump(ann, open(ann_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("merged:", len(new), "| total annotated:", len(ann))
