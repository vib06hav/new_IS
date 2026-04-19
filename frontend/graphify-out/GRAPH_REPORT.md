# Graph Report - C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend  (2026-04-18)

## Corpus Check
- 82 files · ~169,788 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 275 nodes · 315 edges · 68 communities detected
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 50 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]

## God Nodes (most connected - your core abstractions)
1. `apiRequest()` - 38 edges
2. `loadData()` - 9 edges
3. `loadInterviewers()` - 8 edges
4. `toggleHidden()` - 8 edges
5. `loadWorkspace()` - 5 edges
6. `fetchApplications()` - 5 edges
7. `mutateAssignment()` - 4 edges
8. `loadUploads()` - 4 edges
9. `updateTheme()` - 4 edges
10. `fetchInterviewers()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `handleOpenPdf()` --calls--> `fetchSourcePdf()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\app\interviewer\applications\[id]\page.tsx → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\lib\api.ts
- `loadInterviewers()` --calls--> `fetchInterviewers()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\app\admin\interviewers\page.tsx → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\lib\api.ts
- `loadInterviewers()` --calls--> `fetchApplications()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\app\admin\interviewers\page.tsx → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\lib\api.ts
- `loadData()` --calls--> `fetchApplications()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\app\admin\reports\page.tsx → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\lib\api.ts
- `apiRequest()` --calls--> `getCsrfToken()`  [INFERRED]
  C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\lib\api.ts → C:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser\frontend\lib\csrf.ts

## Communities

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (29): apiRequest(), assignApplication(), deleteApplication(), fetchApplicationDetail(), fetchAssignments(), fetchInterviewerAssignmentSummary(), fetchInterviewers(), fetchLlmCapacity() (+21 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (2): buildItemAnnotationTitle(), getItemAnnotation()

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (12): createInterviewWorkspace(), fetchInterviewWorkspace(), launchInterviewWorkspace(), buildPopupFeatures(), openInterviewPopup(), openInterviewPopupPlaceholder(), handleLaunch(), handleOpenConfigure() (+4 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (10): loadSession(), login(), getSession(), signOut(), getCsrfToken(), readCookie(), handleSubmit(), loadSession() (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.17
Nodes (10): createInterviewer(), deleteInterviewer(), saveInterviewerAssignments(), updateInterviewer(), handleAssignmentSave(), handleCreate(), handleEmailUpdate(), handleProfileUpdate() (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.2
Nodes (6): fetchApplications(), retryApplication(), uploadApplication(), handleRetry(), loadUploads(), processQueueLoop()

### Community 6 - "Community 6"
Cohesion: 0.24
Nodes (8): completeInterviewWorkspace(), saveInterviewWorkspace(), addQuestion(), handlePublish(), handleSave(), removeQuestion(), updateQuestion(), updateTheme()

### Community 7 - "Community 7"
Cohesion: 0.29
Nodes (8): changeMyPassword(), updateMyProfile(), uploadMyProfileImage(), handleCropCancel(), handleCropComplete(), handlePasswordChange(), handleProfileImageChange(), handleProfileSave()

### Community 8 - "Community 8"
Cohesion: 0.2
Nodes (0): 

### Community 9 - "Community 9"
Cohesion: 0.43
Nodes (6): finishInterviewWorkspace(), addCustomQuestion(), cycleQuestionStatus(), handleFinish(), updateQuestion(), updateTheme()

### Community 10 - "Community 10"
Cohesion: 0.5
Nodes (3): askReportChat(), handleRetry(), handleSubmit()

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (2): ReportsDashboardSandboxPlayground(), usePolling()

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (2): Badge(), cn()

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (2): Reveal(), useScrollReveal()

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 0.67
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 0.67
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 0.67
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 0.67
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (0): 

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (0): 

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (0): 

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (0): 

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (0): 

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **Thin community `Community 22`** (2 nodes): `layout.tsx`, `RootLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `layout.tsx`, `AdminLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `page.tsx`, `AdminIndexPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `page.tsx`, `AdminLoginPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `page.tsx`, `DesignLabAdminInterviewersPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `page.tsx`, `DesignLabAdminProfilePage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `page.tsx`, `DesignLabAdminUploadPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `page.tsx`, `DesignLabPublishedReportPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `page.tsx`, `DesignLabReportsDashboardPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `page.tsx`, `DesignLabReportsDashboardPlaygroundPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `layout.tsx`, `InterviewerLayout()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `page.tsx`, `InterviewerIndexPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `page.tsx`, `InterviewerLoginPage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (2 nodes): `JsonSection.tsx`, `JsonSection()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `SynthesisReportSection.tsx`, `if()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `handlePointerDown()`, `AdminReportCard.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `AdminDesignLabNavbar()`, `AdminDesignLabNavbar.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (2 nodes): `AdminInterviewersSandbox()`, `AdminInterviewersSandbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `AdminProfileSandbox()`, `AdminProfileSandbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (2 nodes): `InterviewerReportCard.tsx`, `handlePointerDown()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (2 nodes): `AdminShell()`, `AdminShell.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (2 nodes): `InterviewerNavbar.tsx`, `InterviewerNavbar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (2 nodes): `InterviewerShell.tsx`, `InterviewerShell()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (2 nodes): `cn()`, `button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (2 nodes): `separator.tsx`, `cn()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (2 nodes): `Button()`, `Button.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (2 nodes): `EmptyState.tsx`, `EmptyState()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (2 nodes): `HeroPanel.tsx`, `HeroPanel()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (2 nodes): `Loader.tsx`, `Loader()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (2 nodes): `StatusBadge.tsx`, `StatusBadge()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (2 nodes): `upload-queue.spec.ts`, `login()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `next.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `playwright.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `ReviewPackageSection.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `PublishedReportPreviewSandbox.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `FinalInterviewReportSection.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `Card.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `SegmentedControl.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `types.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `adminInterviewersMock.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `interviewerMock.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `reportsDashboardMock.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `dev-clean.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `apiRequest()` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 9`, `Community 10`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `getCsrfToken()` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `loadData()` (e.g. with `fetchApplications()` and `fetchInterviewers()`) actually correct?**
  _`loadData()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `loadInterviewers()` (e.g. with `fetchInterviewers()` and `fetchApplications()`) actually correct?**
  _`loadInterviewers()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `toggleHidden()` (e.g. with `hideApplication()` and `unhideApplication()`) actually correct?**
  _`toggleHidden()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `loadWorkspace()` (e.g. with `fetchInterviewWorkspace()` and `createInterviewWorkspace()`) actually correct?**
  _`loadWorkspace()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._