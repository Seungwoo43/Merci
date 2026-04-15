# TongByun Core Module

This module completes the Tong / Byun layer for SAJU_ENGINE_MASTER.

## Files
- tongbyun_core.py

## What it does
- Builds fixed layer (통): 조후, 억부, 격국
- Builds contextual layer (변): 지장간, 통관, 체용, 사건, 인과, 타임라인, 사례, 처방
- Produces final merged report

## Integration
Call `TongByunIntegration().finalize(ctx)` after your pipeline has filled the AnalysisContext.