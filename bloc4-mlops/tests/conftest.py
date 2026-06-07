"""
tests/conftest.py

Permet aux tests d'importer `src.*` depuis le dossier parent bloc4-mlops/.
"""
import sys
from pathlib import Path

# Ajoute bloc4-mlops/ au sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
