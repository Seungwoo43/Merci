# -*- coding: utf-8 -*-
import subprocess, sys, pathlib

BASE = pathlib.Path("/mnt/data/saju_pdf_tools")
def run(cmd):
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=False)

if __name__ == "__main__":
    py = sys.executable
    run([py, str(BASE / "extract_pdf_to_corpus.py")])
    run([py, str(BASE / "merge_corpus_master.py")])
    print("[DONE] 전체 파이프라인 실행 종료")
