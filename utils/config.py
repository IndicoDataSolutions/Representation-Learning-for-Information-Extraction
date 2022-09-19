from pathlib import Path


NEIGHBOURS = 5
HEADS = 8
EMBEDDING_SIZE = 4
VOCAB_SIZE = 4000
BATCH_SIZE = 40
EPOCHS = 100
LR = 0.00015

current_directory = Path.cwd()
XML_DIR = current_directory / "assets/data/mantis/labeled"
OCR_DIR = (
    current_directory / "mantis_read_api/training/processed"
)  # "assets/data/mantis/labeled/tesseract_results_lstm"
IMAGE_DIR = current_directory / "assets/data/mantis"
CANDIDATE_DIR = (
    current_directory / "mantis_read_api/training/candidates"
)  # "assets/data/mantis/candidates"
SPLIT_DIR = current_directory / "assets/data/mantis/split"
OUTPUT_DIR = current_directory / "output"

PLOT = True

if not OUTPUT_DIR.exists():
    OUTPUT_DIR.mkdir(parents=True)
