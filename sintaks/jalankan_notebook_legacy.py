"""Jalankan notebook data lama dan simpan output sel ke file notebook yang sama."""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'sintaks/New_LST_RF_SVR_Regression_Colab.ipynb'

if __name__ == '__main__':
    notebook = nbformat.read(PATH, as_version=4)
    manager = KernelManager(kernel_name='python3')
    manager.kernel_spec.argv = [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}']
    client = NotebookClient(notebook, km=manager, timeout=1200,
                            resources={'metadata': {'path': str(ROOT)}})
    client.on_cell_start = lambda cell, cell_index: print(f'Sel {cell_index+1}/{len(notebook.cells)}: {cell.get("id")}', flush=True)
    try:
        client.execute()
    finally:
        nbformat.write(notebook, PATH)
    print('SELESAI:', PATH)
