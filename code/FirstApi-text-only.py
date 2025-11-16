import json
import time
from openai import OpenAI

# ========== 配置 ==========
API_KEY = ""
BASE_URL = "https://openkey.cloud/v1"
MODEL_NAME = "gpt-4o-mini"

INPUT_FILE = r"text-only.jsonl"
OUTPUT_FILE = r"answer-text-only.jsonl"

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
"""


# ========== Extract Function ==========
def extract_solution_and_groundtruth(content: str):
    solution, groundtruth = "", ""
    if "answer/solution:" in content:
        _, after_solution = content.split("answer/solution:", 1)
        if "groundtruth:" in after_solution:
            solution, groundtruth = after_solution.split("groundtruth:", 1)
            solution = solution.strip()
            groundtruth = groundtruth.strip()
        else:
            solution = after_solution.strip()
    return solution, groundtruth

# ========== Retry ==========
def solve_question(question: str, client: OpenAI, retries: int = 3) -> dict:
    prompt = PROMPT_TEMPLATE.strip() + f"\n\nQuestion:\n{question.strip()}"
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.3,
            )
            content = response.choices[0].message.content.strip()
            solution, groundtruth = extract_solution_and_groundtruth(content)
            return {
                "question": question.strip(),
                "answer/solution": solution,
                "groundtruth": groundtruth
            }
        except Exception as e:
            print(f"[Retry {attempt+1}/{retries}] Error: {type(e).__name__}: {e}")
            time.sleep(2 ** attempt)
    return {
        "question": question.strip(),
        "answer/solution": "Error: ChatGPT API failed.",
        "groundtruth": ""
    }

# ========== Main ==========
def main():
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            data = json.loads(line)
            question = data.get("question", "").strip()
            if not question:
                continue

            result = solve_question(question, client)
            json.dump(result, outfile, ensure_ascii=False)
            outfile.write("\n")

    print(f"✅ All questions has been solved，output file is ：{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
