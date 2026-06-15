# Changelog

All notable changes to the TriVerse ML project are documented in this file.

---

## [2026-06-15 18:08:00] - Major Core Fixes, Performance & Legibility Enhancements

### Added
- **Dynamic Auto-Prediction (Real-time scoring)**:
  - Integrated `useEffect` hooks in both the **Disease Prediction** and **Credit Scoring** tab interfaces ([DiseasePredictionTab.tsx](file:///f:/TriVerse-ML-main/TriVerse-ML-main/frontend/unified_dashboard/src/components/CreditScoringTab.tsx) and [CreditScoringTab.tsx](file:///f:/TriVerse-ML-main/TriVerse-ML-main/frontend/unified_dashboard/src/components/CreditScoringTab.tsx)).
  - System now automatically calls prediction endpoints and updates prediction scores and dynamic charts in real-time as users modify sliders/parameters or select different trained models, without needing to click a submit button.
- **Brave/Edge Browser Auto-fill Workaround**:
  - Added a notice box in the Login module ([LoginTab.tsx](file:///f:/TriVerse-ML-main/TriVerse-ML-main/frontend/unified_dashboard/src/components/LoginTab.tsx)) advising users to manually enter the password `admin123` to prevent browser password managers from auto-filling invalid cached credentials.

### Fixed
- **API Gateway connection-refused errors (HTTP 502/401)**:
  - Resolved local DNS proxy issue where Node gateway server on port 3000 tried to route requests to FastAPI backend on `localhost` (which Node 18+ resolves to the IPv6 address `::1` while Uvicorn binds to the IPv4 address `127.0.0.1`).
  - Swapped out `localhost` references with explicit `127.0.0.1` IPv4 hosts in Node Proxy gateway code ([server.ts](file:///f:/TriVerse-ML-main/TriVerse-ML-main/frontend/unified_dashboard/server.ts)).
- **Token 401 Unauthorized Expiry Actions**:
  - Updated centralized state store ([store.ts](file:///f:/TriVerse-ML-main/TriVerse-ML-main/frontend/unified_dashboard/src/state/store.ts)) to catch `401 Unauthorized` responses from API routes, clear the invalid/expired token from local storage, and trigger automatic redirect back to the Login view.
- **Python Indentation Syntax Error**:
  - Resolved Python startup `IndentationError` within backend router code ([training.py](file:///f:/TriVerse-ML-main/TriVerse-ML-main/backend/unified_api/app/api/routes/training.py)).

### Changed
- **High-contrast UI Legibility Theme**:
  - Overrode low-contrast text elements in ([index.css](file:///f:/TriVerse-ML-main/TriVerse-ML-main/frontend/unified_dashboard/src/index.css)).
  - High-visibility palette enforced across all tabs:
    - **Primary Text**: Full high-contrast white `#ffffff`
    - **Negative/Alert Statuses**: Crimson Red `#ef4444`
    - **Warning/Pending States**: Bright Amber Yellow `#eab308`
    - **Positive/Success States**: Vibrant Teal/Green `#2dd4bf`
