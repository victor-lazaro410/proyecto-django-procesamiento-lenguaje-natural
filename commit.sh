#!/usr/bin/env bash
set -euo pipefail
# Ejecutar dentro del repo ya clonado
git add .
git commit -m "feat(ngrams): generación configurable de n-gramas y frecuencias integrada sin romper flujo existente"