# Databricks notebook source
# Phase 001 - Enable CDF and Validate

from pathlib import Path

PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "phase001").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

PHASE_001_SQL_DIR = PROJECT_ROOT / "phase001" / "sql"


def run_sql(label, sql_text):
    print(f"[RUN] {label}")
    result = spark.sql(sql_text)
    print(f"[OK] {label}")
    return result


print("Phase 001 CDF enablement")
run_sql("Enable CDF", (PHASE_001_SQL_DIR / "007_enable_cdf.sql").read_text())
