# SkillProof — Product Spec

AI-powered trade skill certification. Worker uploads video/photo evidence of tasks. AI vision assesses. Certificate issued.

Two trades at launch: **Tiling** and **Painting & Decorating**. Both chosen because output is 100% visual — AI can judge quality from photos alone.

---

## Problem

- UK trade certification requires in-person assessor, costs £200-750, takes 4-8 weeks
- 250k+ unfilled trade jobs in UK — certification bottleneck slows the pipeline
- No one uses AI vision to assess physical trade skills (HireVue does office interviews, GoReact needs human graders, Cloud Assess makes written quizzes)

## Solution

Worker films themselves doing 5 defined tasks → uploads → AI scores safety, technique, result → certificate issued in minutes

## Customer

- Training providers (integrate into their courses)
- Recruitment agencies (verify candidate skills)
- Employers (check before hiring)
- Individual workers (self-serve)

---

## Trade 1: Wall & Floor Tiling

### Task T1 — Tool & Material Identification
- **Format:** Photo + multiple choice
- **Time:** 3 min
- **What worker does:** Lay out 6 tiling tools, photograph them, name each. Select correct adhesive for a given substrate.
- **AI checks:** Correct tool names (notched trowel, tile cutter, spirit level, spacers, grout float, sponge). Right adhesive for substrate. Correct spacer size for tile format.

### Task T2 — Surface Preparation
- **Format:** 60-90s video
- **Time:** 5 min
- **What worker does:** Clean a wall surface, check level, mark horizontal/vertical guidelines with pencil, fix a batten if needed.
- **AI checks:** Spirit level used. Guidelines visible and level. Surface cleaned. Batten placed horizontally if applicable.

### Task T3 — Cut a Tile
- **Format:** 60s video + photo of finished cut
- **Time:** 5 min
- **What worker does:** Measure and cut an L-shaped tile to fit around a pipe or obstacle.
- **AI checks:** Measurement taken before cutting. Correct tool used. Safety glasses worn. Clean cut, no chips. Tile fits the obstacle.

### Task T4 — Tile a 1m² Section
- **Format:** 2-3 min timelapse video + final photo
- **Time:** 15 min
- **What worker does:** Apply adhesive with notched trowel, place tiles with spacers, check level, clean excess adhesive.
- **AI checks:** Even adhesive spread with visible ridges. Tiles level with each other. Consistent spacer gaps. No lippage. Pattern aligned. Excess adhesive cleaned.

### Task T5 — Grouting & Finishing
- **Format:** 90s video + close-up photo
- **Time:** 10 min
- **What worker does:** Mix grout, apply diagonally with float, fill all joints, clean excess with sponge within working time.
- **AI checks:** Correct grout consistency. Diagonal application. All joints filled, no voids. Excess cleaned in time. Tiles not scratched. Even finish.

---

## Trade 2: Painting & Decorating

### Task P1 — Surface Assessment
- **Format:** Photo + 50-150 word written explanation
- **Time:** 3 min
- **What worker does:** Photograph a wall with visible defects. Identify each defect (cracks, damp, flaking, holes). Describe correct preparation method for each.
- **AI checks:** Defects correctly identified. Prep methods appropriate (e.g. fill and sand cracks, treat damp before painting, scrape flaking paint and prime). Correct filler/primer selected.

### Task P2 — Masking & Protection
- **Format:** 60s video
- **Time:** 5 min
- **What worker does:** Mask off a window frame, skirting board, and light switch. Lay drop sheets on floor.
- **AI checks:** Tape straight and tight to edges, no gaps. Window frame fully masked. Skirting board edge clean. Switch plate covered or removed. Drop sheets laid. No exposed areas.

### Task P3 — Cutting In
- **Format:** 90s video + close-up photo
- **Time:** 10 min
- **What worker does:** Freehand (no tape) cut in paint along ceiling line, internal corner, and around a door frame.
- **AI checks:** Brush held correctly on narrow edge. Not overloaded. Ceiling line straight and consistent. No paint on ceiling or door frame. Coverage even at edges. Corner line clean.
- **Note:** This is the hardest task. It separates trained painters from amateurs.

### Task P4 — Roll a Wall Section
- **Format:** 2 min video + final photo
- **Time:** 10 min
- **What worker does:** Load roller from tray, apply paint in W-pattern across 2m² section, lay off with even vertical strokes, blend into cut-in edges.
- **AI checks:** Roller loaded evenly from tray, not dipped and slapped. W-pattern used. Even coverage, no thin spots. No drips or runs. Roller marks consistent. Blends into cut-in edges. Consistent sheen.

### Task P5 — Final Inspection
- **Format:** 4 photos from specified angles
- **Time:** 5 min
- **What worker does:** Photograph completed wall from four positions: straight-on overall, angled with raking light, close-up of ceiling line, shot showing masking removed.
- **AI checks:** Even coverage across wall. Clean lines at all edges. No brush/roller marks. Consistent colour, no patchiness. Tape removed cleanly, no bleed. Area tidy.

---

## User Flow

### Worker Flow (10 screens)

**1. Landing Page**
- Headline: "Get trade certified in hours, not weeks"
- Two trade cards (Tiling / Painting)
- How it works: 3 steps
- Price: £49 per certification
- CTA: "Start Free Assessment"

**2. Sign Up**
- Name, email, password
- Experience level dropdown (Beginner / Intermediate / Experienced)
- Optional employer referral code
- Google/Apple sign-in

**3. Select Trade**
- Two cards side by side
- Each shows: trade name, 5 tasks, ~40 min total, 70% pass threshold
- Tap to select → goes to task dashboard

**4. Task Dashboard**
- Progress bar: 0/5 tasks complete
- 5 task cards stacked vertically
- Each card: title, type (photo/video), time, difficulty
- Sequential unlock — must complete T1 before T2 opens
- Completed tasks show green tick + score
- Failed tasks show red X + retry button

**5. Task Brief**
- Task title + full description
- Checklist of what AI will assess (shown to user — no hidden criteria)
- Camera requirements: angle, lighting, distance, framing tips
- Example photo/video of good work vs bad work
- Timer
- Button: "Start Recording" or "Upload File"

**6. Record / Upload**
- Option A: Camera viewfinder using phone camera
- Option B: File upload dropzone (drag or tap)
- Recording timer visible
- Overlay hints: "Show your hands", "Keep camera steady"
- Pause / Resume / Stop controls
- Preview before submit
- Button: "Submit for Assessment"

**7. AI Processing**
- Progress indicator with steps: Extracting frames → Checking safety → Assessing technique → Evaluating result
- Estimated time: 30-60 seconds
- Trade fact shown while waiting

**8. Task Result**
- Pass or Fail with overall score
- Three criterion bars: Safety / Technique / Result Quality
- Each shows score + one-line feedback
- Written paragraph of detailed feedback
- If failed: specific reason + "Retry" button
- If passed: "Next Task" button

**9. Certificate**
- Only appears after all 5 tasks passed
- Shows: name, trade, date, overall score, certificate ID
- QR code linking to public verification page
- Buttons: Download PDF, Share to LinkedIn, Copy verification link

**10. Verification Page (public)**
- No login required
- Anyone with the link or QR sees: worker name, trade, score, date, task breakdown
- Status badge: Valid / Expired / Revoked
- Employer CTA: "Want bulk verification? Create employer account"

### Employer Flow (3 screens)

**1. Verify**
- Scan QR or visit verification link
- See worker's cert details without logging in

**2. Sign Up (Employer)**
- Company name, email, role
- Subscription plan selection

**3. Employer Dashboard**
- Search candidates by trade
- Filter by score, date, location
- Compare candidates side by side
- Export candidate lists

---

## AI Assessment Pipeline

**Step 1: Frame Extraction** (2-5 sec)
- Video → extract 1 frame per second using OpenCV or ffmpeg
- Select 10-15 key frames covering start, middle, end of task
- For photo tasks, use images directly

**Step 2: Safety Pre-Check** (3-5 sec)
- Send first 3 frames to Claude Vision
- Check: PPE (safety glasses, gloves if required), safe workspace, no obvious hazards
- This is a gate — safety fail = instant task fail, no further assessment

**Step 3: Technique Assessment** (10-20 sec)
- Send all key frames as a sequence to Claude Vision
- Prompt includes task-specific rubric (the AI checks listed above for each task)
- Claude returns JSON: per-criterion score (0-100) + observation per criterion

**Step 4: Result Quality Check** (5-10 sec)
- Send final photo(s) of completed work
- Assess end result independently of technique
- Catches cases where technique looked OK but result is poor

**Step 5: Score Aggregation** (<1 sec)
- Weights: Safety 30% (must pass) + Technique 40% + Result 30%
- Pass threshold: 70% overall AND safety must pass
- Generate written feedback paragraph
- Store in database

**Total time per task:** 20-40 seconds
**API calls per task:** 3-4
**API calls per full certification:** 15-20
**API cost per certification:** ~$0.30-0.60

---

## System Requirements

### Frontend
- React (single page app) or Lovable for rapid prototyping
- Mobile-first — workers will use phones on job sites
- Camera access via MediaRecorder API (for live recording)
- File upload accepting image/* and video/*
- Video preview before submission

### Backend
- Python + FastAPI
- Anthropic Claude API (claude-sonnet-4-20250514) for vision assessment
- OpenCV or ffmpeg for frame extraction from video
- ReportLab or WeasyPrint for PDF certificate generation
- qrcode library for QR code generation

### Database
- Supabase (Postgres) or Firebase
- Tables: users, certifications, task_results, certificates
- Store: user info, submission file references, AI assessment JSON responses, certificate metadata

### Storage
- Cloud storage (S3 or Supabase Storage) for uploaded videos/photos
- Store extracted key frames for audit trail
- Generated certificates stored as PDFs

### Auth
- Supabase Auth or Firebase Auth
- Email/password + Google sign-in
- Employer accounts separate from worker accounts

### Hosting
- Frontend: Vercel or Netlify
- Backend: Railway, Render, or AWS Lambda
- Domain: skillproof.ai or similar

---

## Hackathon MVP — What to Build

### Must build (P0)
1. Trade selector (2 cards)
2. Task dashboard with sequential unlock
3. Task brief screen with instructions
4. File upload (photo and video)
5. Claude Vision assessment returning JSON scores
6. Result screen with scores and feedback
7. PDF certificate with QR code

### Nice to have (P1)
1. Camera recording directly in browser
2. Processing animation with step indicators
3. Public verification page at /verify/[id]
4. Example good/bad work per task

### Skip for hackathon (P2)
1. Employer dashboard
2. User accounts and database persistence
3. Payment
4. Multiple retries logic
5. Video frame extraction (use photos only for demo)

### Estimated build time
- Core assessment pipeline (Claude API + scoring): 3 hours
- Task flow UI (6 screens): 4 hours
- Certificate generation: 1 hour
- Polish and demo prep: 2 hours
- **Total: ~10 hours**


---

## Key Risk

AI vision cannot verify everything. It cannot tell if a pipe joint is watertight, if wiring is correctly connected, or if a surface is smooth to the touch. This is why Tiling and Painting were chosen — their outputs are genuinely assessable from photographs. Expanding to trades like plumbing or electrical will require additional verification methods beyond AI vision alone.

The honest framing: AI does 80% of the assessment. For the remaining 20%, the photo of the finished result and optional human review for edge cases covers it. This is still 10x faster and cheaper than the current system.