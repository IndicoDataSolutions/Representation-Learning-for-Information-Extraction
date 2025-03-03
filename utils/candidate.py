import json
import traceback
from utils import operations as op
from tqdm import tqdm
from extract_candidates import get_candidates
from utils import config
import os


def attach_candidate(annotation, candidate_path):
    if not candidate_path.exists():
        os.makedirs(candidate_path)

    for anno in tqdm(annotation, desc="Attaching Candidate"):
        try:
            file_name = anno["filename"]
            candidate_json = candidate_path / f"{file_name}.json"
            if not candidate_json.exists():
                with open(config.OCR_DIR / f"{file_name}.json", "r") as f:
                    ocr_data = json.load(f)
                    candidates = get_candidates(ocr_data)
                with open(candidate_json, "w") as f:
                    json.dump(candidates, f)
            with open(candidate_json, "r") as f:
                candidate_data = json.load(f)

            for cls, cads in candidate_data.items():

                for true_cad in anno["fields"][cls]["true_candidates"]:
                    for cad in cads:
                        iou = op.bb_intersection_over_union(
                            [
                                true_cad["x1"],
                                true_cad["y1"],
                                true_cad["x2"],
                                true_cad["y2"],
                            ],
                            [cad["x1"], cad["y1"], cad["x2"], cad["y2"]],
                        )
                        # TODO: play with this to make the problem tighter.
                        if iou > 0.5:
                            anno["fields"][cls]["true_candidates"].remove(true_cad)
                            anno["fields"][cls]["true_candidates"].append(cad)
                            candidate_data[cls].remove(cad)
                            break
                anno["fields"][cls]["other_candidates"] = candidate_data[cls]

        except Exception:
            trace = traceback.format_exc()
            print("Error in processing candidate: %s : %s" % (anno["filename"], trace))
            break

    return annotation
