# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillProof is an AI-powered trade certification platform. Workers upload videos of themselves performing tasks (tiling, painting & decorating). AI vision assesses technique, safety, and result quality, issuing certificates in minutes instead of weeks.

**Customers:** Training providers, recruitment agencies, employers hiring tradespeople, and self-serve workers.

**User flow:** Select certification goal → Enter a test → AI assigns tasks (quality over quantity — few good tasks beat many bad ones) → Upload videos → AI review → Approve or reject → Certificate issued.

## Development Conventions

- **Use `uv run` for everything** — all Python commands go through `uv`
- **Modular architecture:** one file per pipeline step
- **Concise code, no bloat**
- **`shit_test/`** directory is for throwaway/experimental scripts