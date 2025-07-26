#!/bin/bash
uvicorn sql_analysis.main:app --host 0.0.0.0 --port 10000
