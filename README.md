# MathSight

> **MathSight: A Benchmark Exploring Have Vision-Language Models Really Seen in University-Level Mathematical Reasoning?**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-XXXX.XXXXX-B31B1B.svg)](https://arxiv.org/abs/2511.23112)
[![Website](https://img.shields.io/badge/Website-MathSight-black.svg)](https://cnu-bot-group.github.io/MathSight/)

---

## 🧠 What is MathSight?

**MathSight** is a university-level **multimodal mathematical reasoning benchmark** designed to answer a simple question:

> **Have vision-language models (VLMs) really *seen* in mathematical reasoning?**

Most existing multimodal math benchmarks report high overall accuracy, but they rarely isolate how much the **visual modality** actually contributes. MathSight systematically controls visual variants and text-only settings, so we can disentangle:

- What can be solved **from text alone**?
- When do models **truly rely on images**?
- How robust are models to **style changes** in diagrams?

---

## ✨ Key Features

- **Multi-view visual variants**

  Each multimodal problem may contain:
  - Original clean diagram  
  - Hand-drawn style  
  - Photo-captured version  
  - Text-only condition (no image)

  This enables controlled comparison between **vision + language** vs **language-only** reasoning.

- **Challenging university-level coverage**

  - 2,048 total problems  
  - Covers core university math subjects  
  - Multimodal split is mainly **graduate-level**, closer to real exam-style questions.

- **Vision vs text analysis**

  MathSight is built to compare:
  - Closed-source & open-source VLMs
  - VLMs **with vs. without** image input
  - Answer consistency across different image styles and resolutions

---

## 📊 Dataset Statistics

- **Total problems:** 2,048  
- **Multimodal items:** 661  
- **Images:** 632 × 3 variants (original / hand / photo)  
- **Subjects:** 6 core areas of mathematics  
- **Question types:** 1,713 non-proof vs. 335 proof problems  
- **Difficulty:** 1,668 graduate-level vs. 380 undergraduate-level

## 📦 Dataset

We will gradually release the MathSight benchmark in JSONL format.

### File structure

All dataset files will be stored under the `data/` directory:

- `Dataset/final-language-1387-with-subject-withfixed-new-proof.jsonl`  
  Text-only version of the problems (no image paths), for pure LLM evaluation.

- `Dataset/661/final-vision-661-new.jsonl`  
  Multimodal version including `image_path` fields and visual variants.

Each JSONL line corresponds to one problem and follows the schema:

```json
{
  "question": "...",
  "answer/solution": "...",
  "ground_truth": "...",
  "image_path": "",
  "subject": "Calculus",
  "difficulty": "Graduate-level",
  "is_proof": false
}
