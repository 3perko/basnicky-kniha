#!/usr/bin/env python3
"""Vypíše hotový prompt pre kritika: python3 spusti_kritika.py A davky/davka_1_v1.md hodnotenia/d1_k1_A.md"""
import sys, os
k, davka, vystup = sys.argv[1:4]
base = os.path.dirname(__file__)
root = "/home/user/basnicky-kniha"
rola = open(os.path.join(base, "prompty", f"kritik_{k}.md"), encoding="utf-8").read()
spol = open(os.path.join(base, "prompty", "spolocne.md"), encoding="utf-8").read()
spol = spol.replace("{DAVKA}", os.path.join(root, davka)).replace("{VYSTUP}", os.path.join(root, vystup)).replace("{K}", k)
print(rola + "\n" + spol)
