# Chapter 5 Gap Analysis & Implementation Plan

## Executive Summary

Chapter 5 describes an **evaluation of a working system**. We must ensure our codebase can produce results demonstrating:

- Schema-constrained entity extraction
- OCR fallback for scanned documents
- Embedding-based matching with ranked candidates
- Grounded feedback with evidence
- Latency < 20s, invalid JSON < 2%
- English/Arabic RTL support

---

## Current State vs Chapter 5 Requirements

| Requirement                  | Chapter Section | Current State                                               | Gap                                                       |
| ---------------------------- | --------------- | ----------------------------------------------------------- | --------------------------------------------------------- |
| **Resume Entity Extraction** | 5.3             | `types.ts` has schema (`skills`, `education`, `experience`) | ✅ Schema defined, ❌ Parser service not implemented      |
| **OCR Fallback**             | 5.3             | None                                                        | ❌ Needs `parser_service` with OCR (Tesseract/EasyOCR)    |
| **JSON Validation + Retry**  | 5.3             | `libs/ai` has structured output                             | ⚠️ Needs explicit retry logic + logging                   |
| **Embedding Matching**       | 5.4             | `BaseLLMProvider.get_embedding()` exists                    | ❌ Matching pipeline not implemented                      |
| **Ranked Candidate List**    | 5.4             | None                                                        | ❌ Similarity scoring + UI display needed                 |
| **Grounded Feedback**        | 5.6             | `alignmentInsights` in `types.ts`                           | ⚠️ Backend must populate `matched`, `missing`, `evidence` |
| **Latency Tracking**         | 5.5             | None                                                        | ❌ Needs timing instrumentation                           |
| **Error Handling UI**        | 5.5             | Basic toast                                                 | ⚠️ Needs retry notifications, loading states              |
| **Arabic RTL Layout**        | 5.7             | `LanguageCode` exists, `translations.ts` exists             | ⚠️ Needs RTL CSS, Arabic content testing                  |
| **Resume Upload**            | 5.2             | `OptimizationForm` exists                                   | ⚠️ Needs file upload (PDF/DOCX), not just text            |
| **Profile View**             | 5.3             | `ResultsSummaryPanel` exists                                | ⚠️ Needs explicit entity display (Fig 5.3)                |
| **Export Functionality**     | 5.6             | None                                                        | ❌ PDF/CSV export of feedback report                      |

---

## Implementation Phases

### Phase 1: Parser Service (Critical)

Makes entity extraction and OCR possible.

| Task                                | File/Location                         | Notes                                       |
| ----------------------------------- | ------------------------------------- | ------------------------------------------- |
| Create `parser_service` FastAPI app | `services/parser_service/app/main.py` |                                             |
| Add PDF text extraction             | `parser_service/core/extractor.py`    | Use `PyMuPDF` or `pdfplumber`               |
| Add DOCX extraction                 | `parser_service/core/extractor.py`    | Use `python-docx`                           |
| Add OCR fallback                    | `parser_service/core/ocr.py`          | Use `EasyOCR` (supports Arabic)             |
| Integrate with Gateway              | `gateway_service/routers/uploads.py`  | Proxy file to Parser, return extracted text |
| Update Dockerfile                   | `services/parser_service/Dockerfile`  | Include OCR dependencies                    |

### Phase 2: Matching & Retrieval (Core)

Implements embedding similarity and ranked output.

| Task                             | File/Location                            | Notes                                     |
| -------------------------------- | ---------------------------------------- | ----------------------------------------- |
| Add embedding storage model      | `libs/db/models.py`                      | Vector column (pgvector or JSON)          |
| Implement similarity calculation | `orchestrator_service/core/matcher.py`   | Cosine similarity                         |
| Create weighted aggregation      | `orchestrator_service/core/matcher.py`   | Skills 50%, Experience 30%, Education 20% |
| Return ranked results            | `orchestrator_service/app/api.py`        | `GET /internal/jobs/{id}/matches`         |
| Populate `alignmentInsights`     | `orchestrator_service/core/optimizer.py` | `matched`, `missing`, `weak`, `evidence`  |
| Add retry logic with logging     | `orchestrator_service/core/optimizer.py` | Count invalid JSON, auto-retry            |

### Phase 3: Frontend Polish

Aligns UI with Chapter 5 figures.

| Task                   | File/Location                     | Notes                                       |
| ---------------------- | --------------------------------- | ------------------------------------------- |
| File upload component  | `components/FileUpload.tsx`       | Drag-drop, PDF/DOCX preview                 |
| Extracted profile view | `components/ExtractedProfile.tsx` | Display entities (skills, experience, etc.) |
| Ranked candidates list | `components/CandidateRanking.tsx` | Similarity scores, highlights               |
| Feedback panel         | `components/FeedbackPanel.tsx`    | Matched/missing skills with excerpts        |
| Export button          | `components/ExportButton.tsx`     | PDF/CSV download                            |
| RTL layout             | `index.css` + components          | `dir="rtl"` for Arabic                      |
| Loading states         | `components/ui/Spinner.tsx`       | Progress indicator during processing        |
| Latency display        | `ResultsSummaryPanel.tsx`         | Show `reliability.latencySeconds`           |

---

## Priority Order (Recommended)

1. **Parser Service** - Without this, no file uploads or OCR
2. **JSON Retry Logic** - Quick win, proves < 2% invalid rate
3. **Grounded Feedback** - Populates `alignmentInsights`
4. **File Upload UI** - Frontend can accept PDFs
5. **Extracted Profile View** - Displays entities per Fig 5.3
6. **Matching Pipeline** - Embeddings + similarity
7. **Export Functionality** - Feedback report download
8. **RTL Polish** - Arabic layout fixes
9. **Latency Instrumentation** - Timing metrics

---

## Effort Estimates

| Phase              | Scope   | Estimated Hours |
| ------------------ | ------- | --------------- |
| Phase 1 (Parser)   | 6 tasks | 8-12 hrs        |
| Phase 2 (Matching) | 6 tasks | 10-15 hrs       |
| Phase 3 (Frontend) | 9 tasks | 12-16 hrs       |
| **Total**          |         | **30-43 hrs**   |

---

## Files to Modify/Create

### Backend (New)

- `services/parser_service/app/main.py`
- `services/parser_service/core/extractor.py`
- `services/parser_service/core/ocr.py`
- `services/parser_service/Dockerfile`
- `services/orchestrator_service/core/matcher.py`
- `services/gateway_service/routers/uploads.py`

### Backend (Modify)

- `libs/db/models.py` - Add embedding column
- `services/orchestrator_service/core/optimizer.py` - Add retry, populate insights
- `services/orchestrator_service/app/api.py` - Add matching endpoints

### Frontend (New)

- `components/FileUpload.tsx`
- `components/ExtractedProfile.tsx`
- `components/CandidateRanking.tsx`
- `components/FeedbackPanel.tsx`
- `components/ExportButton.tsx`

### Frontend (Modify)

- `components/OptimizationForm.tsx` - Integrate file upload
- `components/ResultsSummaryPanel.tsx` - Display entities, latency
- `index.css` - RTL support
- `pages/AppPage.tsx` - Wire new components

---

## Next Steps

1. Confirm this plan aligns with your priorities
2. Start with Phase 1 (Parser Service) to unblock file uploads
3. Proceed incrementally, testing each component before integration
