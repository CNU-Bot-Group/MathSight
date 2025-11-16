import os
import json
import base64
import time
import logging
from datetime import datetime
from pathlib import Path
from openai import OpenAI

# ========== GPT-4o API  ==========
client = OpenAI(
    api_key="",
    base_url="https://openkey.cloud/v1"
)


standard_file = r"/.../final-vision-661.jsonl"
student_file = r"/.../answer-draw-gpt4o.jsonl"
image_base_path = r"/.../Orig"
output_file = r"/.../judge-gpt4o-vision-draw-to-draw.jsonl"

MODEL_NAME = "gpt-4o-2024-11-20"

# ========== log ==========
def setup_logger(output_jsonl_path: str) -> logging.Logger:
    """

    """
    out_dir = os.path.dirname(os.path.abspath(output_jsonl_path)) or "."
    base = os.path.splitext(os.path.basename(output_jsonl_path))[0]
    log_path = os.path.join(out_dir, f"{base}.log")

    logger = logging.getLogger("judge_logger")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger, log_path

logger, LOG_PATH = setup_logger(output_file)

# ========== image transfer to base64 ==========
def encode_image(image_path: str) -> str:
    mime_type = "image/jpeg"
    if image_path.lower().endswith(".png"):
        mime_type = "image/png"
    with open(image_path, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"

# ========== is proof ==========
def is_proof_problem(question_text):
    return "prove" in question_text.lower() or "证明" in question_text

# ==========  prompt ==========
def build_judge_prompt(question, ref_solution, ref_answer, stu_solution, stu_answer):
    if is_proof_problem(question):
        return f"""You are a university-level mathematics instructor. Determine whether the following student's proof is logically valid and correctly proves the statement. Focus strictly on the correctness of reasoning and mathematical logic, and ignore differences in wording or format.

Question:
{question}

Reference Proof:
{ref_solution}

Student's Proof:
{stu_solution}

Return only "Yes" if the proof is complete and logically correct, or "No" if it is missing steps, incorrect, or incomplete."""
    else:
        return f"""You are a mathematics evaluator. Compare the student's final answer to the reference final answer. Evaluate whether they are mathematically equivalent.

Question:
{question}

Reference Final Answer:
{ref_answer}

Student's Final Answer:
{stu_answer}

Rules:
- If either answer is missing or empty, return "No".
- Ignore differences in formatting, variable names, or simplification, as long as the mathematical meaning is identical.
- Only return "Yes" if you are certain they are mathematically equivalent. Otherwise, return "No".

Answer only with "Yes" or "No"."""


# ==========  ground_truth ==========
def normalize_gt(gt):
    if isinstance(gt, list):
        return ", ".join(map(str, gt)).strip()
    return str(gt).strip()

# ========== judge ==========
def get_model_judgment(messages, retries=5):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=2048
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            logger.warning(f"API error (attempt {attempt+1}/{retries}): {e}")
            time.sleep(min(2 ** attempt, 30))
    return "no"

# ========== main ==========
start_ts = time.time()
start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

logger.info("===== Experiment START =====")
logger.info(f"Start Time        : {start_time_str}")
logger.info(f"Model             : {MODEL_NAME}")
logger.info(f"Standard File     : {standard_file}")
logger.info(f"Student File      : {student_file}")
logger.info(f"Image Base Path   : {image_base_path}")
logger.info(f"Output JSONL      : {output_file}")
logger.info(f"Log File          : {LOG_PATH}")

with open(standard_file, "r", encoding="utf-8") as f1, open(student_file, "r", encoding="utf-8") as f2:
    ref_data = [json.loads(line) for line in f1]
    stu_data = [json.loads(line) for line in f2]

assert len(ref_data) == len(stu_data), "the lines number of student's jsonl is not same with reference's jsonl"

total = len(ref_data)
logger.info(f"Total Items       : {total}")

results = []
correct_count = 0

for i, (ref, stu) in enumerate(zip(ref_data, stu_data), start=1):
    question = ref["question"]
    ref_solution = ref.get("answer/solution", "")
    stu_solution = stu.get("answer", "") or stu.get("answer/solution", "")
    ref_gt = normalize_gt(ref.get("ground_truth", ""))
    stu_gt = normalize_gt(stu.get("ground_truth", ""))
    proof_flag = is_proof_problem(question)

    image_path = Path(image_base_path).joinpath(ref["image_path"]).as_posix()
    img_exists = os.path.exists(image_path)

    if not img_exists:
        msg = f"[{i:03}] ❌ lose image，skip: {image_path}"
        print(msg)
        logger.info(msg)
        continue

    #
    if not proof_flag and (not ref_gt or not stu_gt):
        judgment = "no"
        reason = "Non-proof & GT missing -> forced 'no'"
    else:
        prompt = build_judge_prompt(question, ref_solution, ref_gt, stu_solution, stu_gt)
        messages = [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": encode_image(image_path)}},
                {"type": "text", "text": prompt}
            ]
        }]
        judgment = get_model_judgment(messages)
        reason = "LLM judged"

    correct = (judgment == "yes")
    if correct:
        correct_count += 1


    print(f"[{i:03}] {'✔️' if correct else '❌'} → {'Proof' if proof_flag else 'Answer'} | Judgment: {judgment}")


    logger.info(
        f"[{i:03}] type={'Proof' if proof_flag else 'Answer'} | "
        f"img_exists={img_exists} | ref_gt_empty={not bool(ref_gt)} | stu_gt_empty={not bool(stu_gt)} | "
        f"judgment={judgment} | correct={correct} | reason={reason} | image_path={image_path}"
    )

    results.append({
        "question": question,
        "reference_solution": ref_solution,
        "student_solution": stu_solution,
        "ground_truth_ref": ref_gt,
        "ground_truth_stu": stu_gt,
        "judgment": judgment,
        "correct": correct,
        "is_proof": proof_flag
    })

# ========== Output ==========
os.makedirs(os.path.dirname(os.path.abspath(output_file)) or ".", exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    for item in results:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

acc = (correct_count / len(results)) if results else 0.0
end_ts = time.time()
duration_sec = end_ts - start_ts
end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


print(f"\n✅ Accuracy: {acc:.2%} ({correct_count}/{len(results)})")
print(f"✅ Results saved to: {output_file}")
print(f"📝 Log saved to: {LOG_PATH}")


logger.info("===== Experiment SUMMARY =====")
logger.info(f"End Time          : {end_time_str}")
logger.info(f"Duration (sec)    : {duration_sec:.2f}")
logger.info(f"Processed Items   : {len(results)}")
logger.info(f"Correct Count     : {correct_count}")
logger.info(f"Accuracy          : {acc:.2%}")
logger.info("===== Experiment END =====")
