#!/usr/bin/env python3
"""批量目录修复与统计验收探针。

契约：
  from ftfy.batch import fix_tree
  rep = fix_tree(root, apply=False)
  rep.files_scanned    扫到的文本文件数
  rep.files_changed    需要修改（apply=True 时已改写）的文件数
  rep.details          列表，每项含 .path（相对路径）、.changed（布尔）
  .txt / .md / .csv 视为文本，其它后缀不处理
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILED = 0
PASSED = 0

BAD = "Caf\u00c3\u00a9 na\u00c3\u00afve"      # 典型 mojibake
GOOD = "Café naïve"
BAD_ENCODED = "CafÃ© naÃ¯ve"


def check(code, desc, fn):
    global FAILED, PASSED
    try:
        fn()
        print(f"[PASS] {code} {desc}")
        PASSED += 1
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {code} {desc}")
        print(f"        {type(exc).__name__}: {exc}")
        FAILED += 1


def main():
    try:
        from ftfy.batch import fix_tree  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] P0 导入 ftfy.batch 失败：{type(exc).__name__}: {exc}")
        print("-" * 60)
        print("探针汇总：0/6 通过")
        return 1

    def make_tree():
        root = Path(tempfile.mkdtemp())
        (root / "sub").mkdir()
        (root / "a.txt").write_text(BAD_ENCODED, encoding="utf-8")
        (root / "sub" / "b.md").write_text(GOOD, encoding="utf-8")
        (root / "sub" / "c.csv").write_text("x\n" + BAD_ENCODED, encoding="utf-8")
        (root / "blob.bin").write_bytes(b"\x00\x01\x02")
        return root

    def p1():
        root = make_tree()
        rep = fix_tree(root, apply=False)
        assert rep.files_scanned == 3, rep.files_scanned

    def p2():
        root = make_tree()
        rep = fix_tree(root, apply=False)
        assert rep.files_changed == 2, rep.files_changed

    def p3():
        root = make_tree()
        fix_tree(root, apply=False)
        assert (root / "a.txt").read_text(encoding="utf-8") == BAD_ENCODED

    def p4():
        root = make_tree()
        fix_tree(root, apply=True)
        assert (root / "a.txt").read_text(encoding="utf-8") == GOOD

    def p5():
        root = make_tree()
        rep = fix_tree(root, apply=True)
        changed = {d.path for d in rep.details if d.changed}
        assert changed == {"a.txt", "sub/c.csv"}, changed

    def p6():
        root = make_tree()
        rep = fix_tree(root, apply=True)
        assert "blob.bin" not in [d.path for d in rep.details], [d.path for d in rep.details]
        import ftfy
        assert ftfy.fix_text(BAD_ENCODED) == GOOD

    check("P1", "只扫文本文件", p1)
    check("P2", "统计需改动文件数", p2)
    check("P3", "dry-run 不写盘", p3)
    check("P4", "apply 后文件被修复", p4)
    check("P5", "明细用相对路径且标出子目录", p5)
    check("P6", "二进制跳过且 fix_text 不变", p6)

    print("-" * 60)
    print(f"探针汇总：{PASSED}/{PASSED + FAILED} 通过")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
