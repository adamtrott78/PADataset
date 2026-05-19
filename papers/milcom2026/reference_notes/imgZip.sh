cd ~/adamArchives/Adam/varMax/PADataset

mkdir -p papers/milcom2026/reference_notes/upload_batches/model_diagram_pages

cp papers/milcom2026/reference_notes/layout_screenshots/2026_tiwari_dqn_ids/page_004.png \
   papers/milcom2026/reference_notes/upload_batches/model_diagram_pages/tiwari_page_004.png

cp papers/milcom2026/reference_notes/layout_screenshots/2026_tiwari_dqn_ids/page_005.png \
   papers/milcom2026/reference_notes/upload_batches/model_diagram_pages/tiwari_page_005.png

cp papers/milcom2026/reference_notes/layout_screenshots/2026_trott_rf_modulation_varmax/page_002.png \
   papers/milcom2026/reference_notes/upload_batches/model_diagram_pages/trott_page_002.png

cp papers/milcom2026/reference_notes/layout_screenshots/2026_trott_rf_modulation_varmax/page_004.png \
   papers/milcom2026/reference_notes/upload_batches/model_diagram_pages/trott_page_004.png

cp papers/milcom2026/reference_notes/layout_screenshots/2026_trott_rf_modulation_varmax/page_008.png \
   papers/milcom2026/reference_notes/upload_batches/model_diagram_pages/trott_page_008.png

cd papers/milcom2026/reference_notes/upload_batches
zip -r model_diagram_pages.zip model_diagram_pages