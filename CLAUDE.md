# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is for developing an AI-enhanced application for automated data preparation, estimation, and report writing as part of a Government of India Ministry of Statistics and Programme Implementation (MoSPI) initiative. The project is part of a Statathon competition (Problem Statement 4).

## Project Goals

The application should build a prototype that:
- Ingests raw survey files (CSV/Excel)
- Performs data cleaning (imputation, outlier & rule-based checks)
- Integrates survey weights
- Produces final estimates with margins of error
- Generates standardized output reports in PDF/HTML format
- Offers a user-friendly, configurable interface

## Key Technical Requirements

### Data Processing Features
- **Data Input**: CSV/Excel upload with schema mapping via UI or JSON config
- **Cleaning Modules**: 
  - Missing-value imputation (mean, median, KNN)
  - Outlier detection (IQR, Z-score, winsorization)
  - Rule-based validation (consistency, skip-patterns)
- **Weight Application**: Apply design weights and compute weighted/unweighted summaries with margins of error
- **Report Generation**: Auto-generate reports using templates with workflow logs, diagnostics, and visualizations

### User Experience
- Configurable modules for different survey types
- Tooltips, inline explanations, error-checking alerts
- User-friendly interface for non-technical users

## Development Context

This is a hackathon/competition project with focus on:
- Rapid prototyping
- Statistical accuracy and methodology
- Government statistical agency workflows
- Reproducibility and methodological consistency

## Resources Available
- Gold-standard benchmark datasets for validation
- PDF report templates
- Documentation on survey-weight methodology