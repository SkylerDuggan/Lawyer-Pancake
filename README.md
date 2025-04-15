# LSAT Prep Tool

A lightweight project to help break down LSAT PrepTests into drill questions (similar to LeetCode) and build a personalized study experience.

This repo contains the foundation for parsing full [LSAT PrepTests](https://www.lsac.org/lsat/lsat-prep/prep-books) PDFs into usable, structured data — questions, answers, and answer keys — with the goal of creating an application (what exactly? TBD) that drills users on real exam content.

---

## Current Files

- `spliter.py`: Script to split each LSAT PrepTest PDF into individual sections (RC, LR1, LR2, AR, Answer Key).
- `parser.py`: Work-in-progress for extracting questions, choices, and answers from split PDFs.
- `/LSATPreptests`: Raw PrepTest PDFs (PrepTest 1–90). More to be added.
- `/SplitSections`: Output directory for split section PDFs.
- Early JSON exports from PT90 (`pt90_questions.json`, `pt90_answers.json`). Just as examples of possible schema.
- `app.py`: Placeholder for future interface logic.

---

## Goals

This is meant to evolve into a full study tool with:

- A database of LSAT questions, answer choices, and correct answers
- Passages for reading comprehension questions
- A simple UI (wether web or local) to drill random questions by type and/or difficulty
- Performance tracking and review features

---

## The Overall Plan (Shit roadmap)

**Phase 1: Core**
1. Parse + structure questions into JSON/db (almost done)
2. Flask API to serve questions
3. React UI to show questions + receive answers
4. Record answers per session

**Phase 2: Users + Scores**
1. User auth (email/password or Google login)
2. Save question history
3. Track accuracy by type, section, etc.

**Phase 3: Review + Ranking**
1. Review incorrect questions
2. Add streaks, accuracy trends
3. Leaderboards (optional)

---

## Notes

- This repo is private for now since it contains actual LSAC issued LSAT PDFs.
- If we publish it later, all copyrightable LSAT content will be removed.
- Keys/secrets are no longer in this repo (rotated + moved to `.env`)
- Don't commit `.env` files if this ever becomes public. Git is forever.


