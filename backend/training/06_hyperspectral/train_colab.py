"""
TRINETRA / SatQuery AI — Standalone Hyperspectral Colab Fine-Tuning Pipeline
Script: backend/training/06_hyperspectral/train_colab.py
"""

# Re-exporting main from root script
import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, root_dir)

from importlib.machinery import SourceFileLoader
colab_script = os.path.join(root_dir, "06_train_hyperspectral_colab.py")
module = SourceFileLoader("colab_hsi", colab_script).load_module()

if __name__ == "__main__":
    module.main()
