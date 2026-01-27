# UAI Engine - Master Build Implementation Plan

## ✅ Completed Foundation

### 1. Database Schema (`apps/api/models.py`)
- ✅ User model with roles (FREE, PRO, ENTERPRISE) and credits
- ✅ Project model with status, preview URLs, watermark control
- ✅ ProjectVersion model for version history
- ✅ Build model with status tracking and logs
- ✅ ChatMessage model for iteration history
- ✅ CreditTransaction model for monetization

### 2. Core Services
- ✅ **BuildService** (`apps/api/services/build_service.py`)
  - Docker sandboxed execution
  - CPU/Memory limits
  - Network isolation
  - Build validation with lint and build checks
  - Log extraction

- ✅ **RepairService** (`apps/api/services/repair_service.py`)
  - Failure analysis
  - Error pattern detection
  - Repair suggestion generation
  - Retry logic (up to 3 attempts)
  - ⚠️ AI-powered repair generation (placeholder - needs AI integration)

- ✅ **DiffService** (`apps/api/services/diff_service.py`)
  - Unified diff generation
  - File change computation
  - ⚠️ Minimal diff generation (placeholder - needs AI integration)

### 3. Stable Next.js Template (`apps/api/templates/nextjs-stable/`)
- ✅ Complete Next.js 14 App Router structure
- ✅ Layout with Header and Footer components
- ✅ Routes: home, pricing, about, contact
- ✅ Reusable section components (Hero, Features, CTA)
- ✅ Watermark component (controlled by env var)
- ✅ SEO helpers (metadata, OpenGraph)
- ✅ robots.ts and sitemap.ts
- ✅ Contact form with server route
- ✅ Theme tokens support
- ✅ TypeScript configuration
- ✅ Tailwind CSS setup

## 🚧 Next Steps (Priority Order)

### Phase 1: Core API Implementation

1. **Update main.py API endpoints**
   - [ ] User authentication (signup, login, JWT)
   - [ ] Project CRUD endpoints
   - [ ] Chat iteration endpoint (POST /api/projects/{id}/iterate)
   - [ ] Build trigger endpoint (POST /api/projects/{id}/build)
   - [ ] Version history endpoint (GET /api/projects/{id}/versions)
   - [ ] Rollback endpoint (POST /api/projects/{id}/rollback)
   - [ ] File tree endpoint (GET /api/projects/{id}/files)
   - [ ] File content endpoint (GET /api/projects/{id}/files/{path})
   - [ ] Diff viewer endpoint (GET /api/projects/{id}/diff/{version_id})
   - [ ] Build logs endpoint (GET /api/builds/{id}/logs)
   - [ ] Credit management endpoints

2. **Project Generation Service**
   - [ ] Prompt to spec parser (AI integration needed)
   - [ ] Spec to code generator (AI integration needed)
   - [ ] Template instantiation with placeholder replacement
   - [ ] Initial build validation
   - [ ] Preview URL generation (Vercel API integration)

3. **Iteration Service**
   - [ ] Chat message processing
   - [ ] Spec update from chat
   - [ ] Minimal diff generation (AI integration needed)
   - [ ] Diff application to project
   - [ ] Rebuild after iteration
   - [ ] Auto-repair on failure

### Phase 2: Frontend Implementation

1. **Authentication Pages**
   - [ ] Signup page
   - [ ] Login page
   - [ ] Auth context/provider

2. **Dashboard**
   - [ ] Projects list with status
   - [ ] Create project button
   - [ ] Project cards with preview thumbnails

3. **Project Editor**
   - [ ] Chat interface for iterations
   - [ ] File tree sidebar (Monaco editor integration)
   - [ ] File content viewer/editor
   - [ ] Diff viewer component
   - [ ] Build logs viewer
   - [ ] Version history sidebar
   - [ ] Preview iframe
   - [ ] Build status indicator

4. **UI Components**
   - [ ] Monaco editor wrapper
   - [ ] File tree component
   - [ ] Diff viewer component
   - [ ] Build logs component
   - [ ] Credit balance display
   - [ ] Paywall modals

### Phase 3: Integration & Polish

1. **Vercel Integration**
   - [ ] Vercel API client
   - [ ] Preview deployment on build success
   - [ ] Preview URL management
   - [ ] Production deployment (paywalled)

2. **Credit System**
   - [ ] Credit calculation for actions
   - [ ] Paywall checks
   - [ ] Payment processing (Stripe integration)
   - [ ] Credit purchase flow

3. **AI Integration**
   - [ ] OpenAI/Anthropic API integration for:
     - Prompt to spec parsing
     - Code generation from spec
     - Minimal diff generation
     - Auto-repair suggestions
   - [ ] Prompt engineering for reliable outputs
   - [ ] Error handling and retries

4. **Testing & Validation**
   - [ ] Unit tests for services
   - [ ] Integration tests for build flow
   - [ ] E2E tests for critical paths
   - [ ] Load testing for build queue

## 🔧 Technical Implementation Notes

### Build Validation Flow
1. User creates project with prompt
2. System generates spec (AI)
3. System generates code from spec (AI)
4. System applies code to template
5. System runs build in Docker sandbox
6. If build fails:
   - Capture logs
   - Run repair service
   - Apply fix
   - Retry (up to 3 times)
7. If build succeeds:
   - Deploy to Vercel preview
   - Update project status
   - Show preview URL

### Iteration Flow
1. User sends chat message
2. System updates spec based on message (AI)
3. System generates minimal diff (AI)
4. System applies diff to project
5. System rebuilds
6. If build fails, run repair flow
7. If build succeeds, update preview

### Version History
- Every successful build creates a new version
- Versions store spec snapshot and code diff
- Rollback applies previous version's diff in reverse

### Security Considerations
- Docker sandbox with strict limits
- No network access during builds
- Path traversal prevention
- File write restrictions
- Secret management (never log secrets)
- Rate limiting on API endpoints

## 📋 File Structure Created

```
apps/api/
├── models.py                    # Database models
├── services/
│   ├── build_service.py        # Docker sandbox build validation
│   ├── repair_service.py       # Auto-repair logic
│   └── diff_service.py         # Diff generation and application
└── templates/
    └── nextjs-stable/          # Stable Next.js template
        ├── app/                # Next.js App Router
        ├── components/         # Reusable components
        └── lib/                # Utilities (SEO, etc.)
```

## 🎯 Success Criteria

- [ ] Every generated project compiles and passes lint/build
- [ ] Failed builds trigger auto-repair (up to 3 attempts)
- [ ] Only minimal diffs applied (no full rewrites)
- [ ] Version history with rollback works
- [ ] No broken previews marked as successful
- [ ] Preview URLs work and update on iteration
- [ ] Credit system enforces paywalls correctly
- [ ] File tree, viewer, diff viewer, logs all functional

## 🚀 Getting Started

1. Update `apps/api/main.py` to use new models
2. Implement authentication endpoints
3. Implement project creation with AI integration
4. Implement build validation flow
5. Build frontend components
6. Integrate Vercel API
7. Add credit system
8. Test end-to-end

---

**Status**: Foundation complete. Ready for Phase 1 implementation.
