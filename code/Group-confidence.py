import os
import json
import math
import logging
from datetime import datetime
from statistics import mean, pstdev

# ========== Configuration ==========
# Input: First API-generated jsonl (contains token_confidences)
INPUT_JSONL = r"/Volumes/Mac SSD/UMMBench/macmini 处理数据/Group-Confidence实验集/Proof增补实验/gpt-4/answer-gpt-4.jsonl"
# Output: A new jsonl with appended group metrics (only include records containing token_confidences)
OUTPUT_JSONL = os.path.splitext(INPUT_JSONL)[0] + "_with_groups.jsonl"
# Log file: placed in the same directory as output
LOG_FILE = os.path.splitext(INPUT_JSONL)[0] + "_group_metrics_log.txt"

# Sliding window size / step
W = 6
S = 3
# Tail window mode: last window forced to full length W
TAIL_MODE = "full"  # optional: "short"

# ========== Logging ==========
SCRIPT_NAME = os.path.basename(__file__) if "__file__" in globals() else "compute_group_confidence_logperitem.py"
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s | {SCRIPT_NAME} | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")]
)
LINE = "─" * 96


def fmt_float(x, nd=6):
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def sliding_windows_indices(n_tokens: int, w: int, s: int, tail_mode: str = "full"):
    """
    Generate (start, end) window indices (1-based, inclusive), using:
    - overlapping windows with step size s
    - tail window:
        full  -> [N-W+1, N] (full-sized)
        short -> [last+1, N] (short window)
    Returns: [(start, end), ...], deduplicated and sorted.
    """
    idx = []
    if n_tokens <= 0:
        return idx

    # Full windows
    j = 0
    while True:
        st = 1 + j * s
        ed = st + w - 1
        if ed <= n_tokens:
            idx.append((st, ed))
            j += 1
        else:
            break

    # Tail window
    if tail_mode == "full":
        if n_tokens >= w:
            st_tail = n_tokens - w + 1
            if not idx or idx[-1] != (st_tail, n_tokens):
                idx.append((st_tail, n_tokens))
        else:
            idx = [(1, n_tokens)]
    else:  # short
        if idx:
            last_st, last_ed = idx[-1]
            if last_ed < n_tokens:
                idx.append((last_ed + 1, n_tokens))
        else:
            idx = [(1, n_tokens)]

    # Deduplicate & sort
    seen, out = set(), []
    for it in idx:
        if it not in seen:
            out.append(it)
            seen.add(it)
    out.sort(key=lambda x: x[0])
    return out


def group_mean(values, a, b):
    """ values and indices a,b are 1-based (inclusive). """
    a0 = max(a - 1, 0)
    b0 = min(b, len(values))
    if a0 >= b0:
        return None
    window = values[a0:b0]
    return sum(window) / len(window) if window else None


def group_within_std(values, a, b):
    """ Within-group std: sqrt( (1/|I|) * Σ (C_i - g_j)^2 ) """
    a0 = max(a - 1, 0)
    b0 = min(b, len(values))
    if a0 >= b0:
        return None
    window = values[a0:b0]
    if not window:
        return None
    g = sum(window) / len(window)
    var = sum((x - g) ** 2 for x in window) / len(window)
    return math.sqrt(var)


def record_id_hint(rec: dict, idx: int) -> str:
    """Construct a readable record identifier."""
    q = rec.get("question") or rec.get("prompt") or ""
    q = " ".join(str(q).split())
    if q:
        q = (q[:80] + "…") if len(q) > 80 else q
        return f"#{idx} | {q}"
    return f"#{idx}"


def process_record(rec: dict):
    """Append group metrics; return (None, False) if token_confidences is missing."""
    confs = rec.get("token_confidences", None)
    if not confs or not isinstance(confs, list):
        return None, False

    N = len(confs)
    windows = sliding_windows_indices(N, W, S, tail_mode=TAIL_MODE)
    g_list, s_list = [], []

    for (a, b) in windows:
        gj = group_mean(confs, a, b)
        sj = group_within_std(confs, a, b)
        if gj is None or sj is None:
            continue
        g_list.append(gj)
        s_list.append(sj)

    if not g_list:
        return None, False

    g_mean_overall = mean(g_list)
    g_std = pstdev(g_list) if len(g_list) > 1 else 0.0
    g_cv = (g_std / g_mean_overall) if g_mean_overall != 0 else 0.0
    g_bottom = min(g_list)
    s_mean_overall = mean(s_list)

    rec_out = dict(rec)
    rec_out["group_config"] = {"window": W, "step": S, "tail_mode": TAIL_MODE}
    rec_out["group_count"] = len(g_list)
    rec_out["group_means"] = g_list
    rec_out["group_within_std"] = s_list
    rec_out["group_mean_overall"] = g_mean_overall
    rec_out["group_bottom"] = g_bottom
    rec_out["group_std"] = g_std
    rec_out["group_cv"] = g_cv
    rec_out["group_mean_within_std"] = s_mean_overall

    return rec_out, True


def main():
    logging.info(LINE)
    logging.info(f"Start computing group metrics | window={W} | step={S} | tail={TAIL_MODE}")
    logging.info(f"Input  : {INPUT_JSONL}")
    logging.info(f"Output : {OUTPUT_JSONL}")
    logging.info(LINE)

    read_total = 0
    written_total = 0

    with open(INPUT_JSONL, "r", encoding="utf-8") as fin, \
            open(OUTPUT_JSONL, "w", encoding="utf-8") as fout:

        for line_id, line in enumerate(fin, start=1):
            read_total += 1
            try:
                rec = json.loads(line)
            except Exception as e:
                # JSON parsing failure: still log warning
                logging.warning(f"[Line {line_id}] JSON parse failed: {e}")
                continue

            out, flag = process_record(rec)

            # Only write if successfully computed (must contain token_confidences)
            if not flag:
                continue

            fout.write(json.dumps(out, ensure_ascii=False) + "\n")
            written_total += 1

            # Per-record logging
            rid = record_id_hint(rec, line_id)
            gm_show = ", ".join(fmt_float(x, 4) for x in out["group_means"][:5])
            gs_show = ", ".join(fmt_float(x, 4) for x in out["group_within_std"][:5])
            logging.info(
                "\n".join([
                    LINE,
                    f"{rid}",
                    f"  tokens (len(token_confidences))  : {len(rec.get('token_confidences', []))}",
                    f"  groups (count)                   : {out['group_count']}",
                    f"  group_mean_overall (ḡ)          : {fmt_float(out['group_mean_overall'], 6)}",
                    f"  group_bottom (min g_j)           : {fmt_float(out['group_bottom'], 6)}",
                    f"  group_std (std of g_j)           : {fmt_float(out['group_std'], 6)}",
                    f"  group_cv (std/mean of g_j)       : {fmt_float(out['group_cv'], 6)}",
                    f"  group_mean_within_std (avg s_j)  : {fmt_float(out['group_mean_within_std'], 6)}",
                    f"  group_means (first 5)            : [{gm_show}]",
                    f"  group_within_std (first 5)       : [{gs_show}]",
                ])
            )

            if written_total % 100 == 0:
                logging.info(f"Progress: {written_total} written...")

    logging.info(LINE)
    logging.info(f"Total read: {read_total} | Written (with token_confidences): {written_total}")
    logging.info(f"Log file: {LOG_FILE}")
    logging.info(LINE)


if __name__ == "__main__":
    main()
