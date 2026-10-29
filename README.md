# MathSight

> **MathSight: A Benchmark Exploring Have Vision-Language Models Really Seen in University-Level Mathematical Reasoning?**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![ACL 2026](https://img.shields.io/badge/ACL%202026-Long%20Paper-4B8BBE.svg)](https://aclanthology.org/2026.acl-long.2198/)
[![ACL Anthology](https://img.shields.io/badge/ACL%20Anthology-2026.acl--long.2198-orange.svg)](https://aclanthology.org/2026.acl-long.2198/)
[![Paper](https://img.shields.io/badge/arXiv-2511.23112-B31B1B.svg)](https://arxiv.org/abs/2511.23112)
[![Website](https://img.shields.io/badge/Website-MathSight-black.svg)](https://cnu-bot-group.github.io/MathSight/)

🎉 **MathSight was accepted as a Long Paper at the ACL 2026 Main Conference and is now officially published in the Proceedings of ACL 2026.**

📖 **Official Paper:** [ACL Anthology](https://aclanthology.org/2026.acl-long.2198/)  
📄 **Preprint:** [arXiv:2511.23112](https://arxiv.org/abs/2511.23112)  
🌐 **Project Page:** [MathSight Website](https://cnu-bot-group.github.io/MathSight/)

---

## 🔔 Updates

- **2026-07:** 📚 MathSight is now published in the *Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)* and available on ACL Anthology.
- **2026-04-04:** 🎉 MathSight was accepted as a Long Paper at the ACL 2026 Main Conference.
- **2025-11-15:** Initial MathSight dataset and code released.

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
```


## 📄 Paper

**MathSight: A Benchmark Exploring Have Vision-Language Models Really Seen in University-Level Mathematical Reasoning?**

**Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (ACL 2026), Volume 1: Long Papers**

- **ACL Anthology:** https://aclanthology.org/2026.acl-long.2198/
- **DOI:** https://doi.org/10.18653/v1/2026.acl-long.2198
- **arXiv:** https://arxiv.org/abs/2511.23112
- **Project Page:** https://cnu-bot-group.github.io/MathSight/
- **Pages:** 47573–47604
- **Location:** San Diego, California, United States

---

## 📝 Citation

If you find MathSight useful in your research, please consider citing our paper:

```bibtex
@inproceedings{wang-etal-2026-mathsight,
    title = "{M}ath{S}ight: A Benchmark Exploring Have Vision-Language Models Really Seen in University-Level Mathematical Reasoning?",
    author = "Wang, Yuandong  and
      Cui, Yao  and
      Zhao, Yuxin  and
      Yang, Zhen  and
      Zhu, Yangfu  and
      Shao, Zhenzhou",
    editor = "Liakata, Maria  and
      Moreira, Viviane P.  and
      Zhang, Jiajun  and
      Jurgens, David",
    booktitle = "Proceedings of the 64th Annual Meeting of the {A}ssociation for {C}omputational {L}inguistics (Volume 1: Long Papers)",
    month = jul,
    year = "2026",
    address = "San Diego, California, United States",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2026.acl-long.2198/",
    doi = "10.18653/v1/2026.acl-long.2198",
    pages = "47573--47604",
    ISBN = "979-8-89176-390-6"
}
```

---

## 📜 License

This project is released under the [MIT License](LICENSE).
