import os
import json
import base64
import time
import traceback
from pathlib import Path
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from openai import OpenAI


API_KEY = ""
BASE_URL = "https://chat.intern-ai.org.cn/api/v1/"


client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


input_path = r"/.../Multimodal-661.jsonl"
output_path = r"/.../answer-Multimodal-661.jsonl"
image_base_path = r"/.../Orig"


OUT_DIR = Path(output_path).parent
OUT_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now().strftime("%Y%m%d-%H%M%S")
log_file = OUT_DIR / f"answer-test_log_{ts}.txt"
jsonl_log_file = OUT_DIR / f"answer-test_log_{ts}.jsonl"

def setup_logger():
    logger = logging.getLogger("runner")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)


    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

LOGGER = setup_logger()

def write_jsonl_log(obj: dict):

    with open(jsonl_log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ========== image transfer to base64 ==========
def encode_image(image_path: str) -> str:
    mime_type = "image/jpeg"
    ext = Path(image_path).suffix.lower()
    if ext == ".png":
        mime_type = "image/png"
    with open(image_path, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")
        return f"data:{mime_type};base64,{base64_data}"

# ========== Prompt  ==========
PROMPT_TEMPLATE = """
You are a university-level mathematics instructor. Given the following question, provide a complete and rigorous solution. The final answer must be clearly marked as `groundtruth`.

If the question is a proof problem, provide the full proof in the solution section, but leave the groundtruth field empty.

Please strictly follow this output format (use English field names exactly as shown):

question:
<Original question text>
answer/solution:
<Your detailed solution>
groundtruth:
<Final answer or leave empty if proof>

Please read the reference image at image_path.
""".strip()

def main():
    start_all = time.perf_counter()
    LOGGER.info("==== Task begin ====")
    LOGGER.info(f"Input_path: {input_path}")
    LOGGER.info(f"Output_path: {output_path}")
    LOGGER.info(f"Image_base_path: {image_base_path}")
    LOGGER.info(f"Log_file: {log_file}")
    LOGGER.info(f"Jsonl_lof_file: {jsonl_log_file}")


    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for idx, line in enumerate(infile, start=1):
            line = line.strip()
            if not line:
                continue

            item_start = time.perf_counter()
            try:
                data = json.loads(line)
            except Exception:
                LOGGER.error(f"[#{idx}] can not transfer to JSON：{line[:120]}...")
                write_jsonl_log({
                    "index": idx, "status": "parse_error", "line_head": line[:200],
                    "time": datetime.now().isoformat()
                })
                continue

            raw_image_path = str(data.get("image_path", "")).strip()
            image_filename = os.path.basename(raw_image_path) if raw_image_path else ""
            image_path = Path(image_base_path).joinpath(image_filename).as_posix() if image_filename else ""
            question = str(data.get("question", "")).strip()

            LOGGER.info(f"[#{idx}] begin process；image: {image_path or '(无)'}")
            if not question:
                LOGGER.warning(f"[#{idx}] question is empty，skip.")
                write_jsonl_log({
                    "index": idx, "status": "empty_question",
                    "image_path": image_path, "time": datetime.now().isoformat()
                })
                continue


            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_TEMPLATE + "\n\nQuestion:\n" + question}
                    ]
                }
            ]


            if image_path and Path(image_path).exists():
                try:
                    encoded = encode_image(image_path)
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": encoded}
                    })
                except Exception as e:
                    LOGGER.warning(f"[#{idx}] read/code image false：{e}；continue with pure text。")
            else:
                if image_path:
                    LOGGER.warning(f"[#{idx}] images not exist：{image_path}；continue with pure text。")

            answer = None
            model_name = "internvl3.5-241b-a28b"
            max_retries = 7
            last_err = None

            for attempt in range(1, max_retries + 1):
                try:
                    t0 = time.perf_counter()
                    LOGGER.info(f"[#{idx}] attempt to call（the {attempt}/{max_retries} round）...")
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=2048,
                        temperature=0.3,
                        top_p=0.9
                    )
                    dt = time.perf_counter() - t0
                    answer = (response.choices[0].message.content or "").strip()
                    LOGGER.info(f"[#{idx}] success；use time {dt:.2f}s；output length {len(answer)}")
                    write_jsonl_log({
                        "index": idx, "status": "success", "attempt": attempt,
                        "latency_sec": round(dt, 3),
                        "model": model_name,
                        "image_attached": "image_url" in [c.get("type") for c in messages[0]["content"]],
                        "time": datetime.now().isoformat()
                    })
                    break
                except Exception as e:
                    last_err = e
                    backoff = min(2 ** attempt, 30)
                    LOGGER.error(f"[#{idx}] false（the {attempt} round）：{e}")
                    write_jsonl_log({
                        "index": idx, "status": "api_error", "attempt": attempt,
                        "error": repr(e),
                        "trace": traceback.format_exc()[:2000],
                        "time": datetime.now().isoformat()
                    })
                    if attempt < max_retries:
                        LOGGER.info(f"[#{idx}] {backoff}s later to continue...")
                        time.sleep(backoff)

            if answer is None:
                msg = f"API call error：{last_err!r}" if last_err else "API call error "
                answer = f"Error: {msg}"
                LOGGER.error(f"[#{idx}] {msg}")
                write_jsonl_log({
                    "index": idx, "status": "give_up",
                    "error": repr(last_err) if last_err else "unknown",
                    "time": datetime.now().isoformat()
                })


            data["answer"] = answer
            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            outfile.flush()

            item_dt = time.perf_counter() - item_start
            LOGGER.info(f"[#{idx}] finish；total use time {item_dt:.2f}s")

    total_dt = time.perf_counter() - start_all
    LOGGER.info(f"==== All finish；Total use time {total_dt:.2f}s ====")
    LOGGER.info(f"Output path：{output_path}")
    LOGGER.info(f"Log file：{log_file}")
    LOGGER.info(f"Jsonl_log_file：{jsonl_log_file}")

if __name__ == "__main__":
    main()
