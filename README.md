# Forest Conservation AI

A reproducible, local-first research prototype for satellite-based forest-loss screening and priority-aware early warning.

The project follows the supplied project materials: use transfer learning for land-cover classification, compare imagery from different dates to identify candidate forest-to-nonforest transitions, and later connect those events to a publish/subscribe notification layer with prioritized routing.

## Phase 1 status

Phase 1 established the repository and runtime foundation.

## Phase 2 status — complete

Phase 2 implements the land-cover classification layer and the fast reproducible evaluation path.

## Phase 3 status — complete

Phase 3 implements the bi-temporal detection core using the public Forest-Change benchmark as the fast, reproducible input source. The dataset provides aligned pre-change RGB images, post-change RGB images, and binary change masks. The adapter does not commit the external dataset to this repository.

Phase 3 provides:

- Dataset discovery for `images/<split>/{A,B,label}`.
- Aligned non-overlapping 64×64 patch extraction.
- Binary change-mask fraction calculation.
- The project reference forest-to-nonforest candidate rule.
- Confidence gating using both before/after model confidences.
- Unit tests and a network-free smoke verification script.

### Phase 3 source

Forest-Change repository: https://github.com/zhoujinghe2025/forest-change_256

The source repository documents 334 annotated bi-temporal image pairs, approximately 30 m/pixel imagery, 256×256 processed images, binary deforestation masks, and train/validation/test splits. It is MIT licensed for academic reuse. Use its published citation when results are reported.

### Phase 3 data layout

Place the downloaded Forest-Change dataset at:

    data/external/forest_change/

Expected layout:

    data/external/forest_change/
    └── images/
        ├── train/
        │   ├── A/
        │   ├── B/
        │   └── label/
        ├── val/
        │   ├── A/
        │   ├── B/
        │   └── label/
        └── test/
            ├── A/
            ├── B/
            └── label/

The repository intentionally excludes these large image files from Git.

### Phase 3 verification

Run the network-free smoke test first:

    python scripts/verify_phase3.py

Expected output:

    Phase 3 smoke verification passed.
    Aligned 256x256 pair -> 16 x 64x64 patches: passed
    Binary change-mask fraction: passed
    Forest -> non-forest candidate rule: passed
    Confidence threshold handling: passed

### Current scope

Phase 3 does not train a segmentation model. The binary masks are used as independent reference data for later evaluation. Model inference over the real benchmark will be wired in the end-to-end phase after the dataset is present locally.

## License

MIT. See LICENSE.
