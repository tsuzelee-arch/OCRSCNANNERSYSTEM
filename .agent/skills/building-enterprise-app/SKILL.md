---
name: building-enterprise-app
description: Guides the agent through planning, scaffolding, and delivering a full-stack enterprise application with a database schema, REST API, and React frontend. Use when the user asks to build an enterprise app, create a full-stack project, scaffold a CRUD application, or generate a production-ready todo/user management system.
---

# Enterprise Application Builder

## When to Use
- User asks to build or scaffold a full-stack enterprise application.
- User requests a CRUD app with users and todos.
- User wants a guided, step-by-step implementation plan for a React + Node.js + SQL project.
- User mentions enterprise app, production-ready scaffold, or full-stack project.

## Workflow Overview
The agent follows a strict Plan-Validate-Execute loop across seven phases. Each phase must be completed and validated before the next begins.
* Phase 0: Clarification & Requirements Gathering
* Phase 1: Task Planning & Tool Preparation
* Phase 2: Database Schema Design
* Phase 3: API Route Design & File Structure
* Phase 4: Backend Implementation
* Phase 5: Frontend Implementation (React + Hooks)
* Phase 6: Test Data, Manual E2E Testing & Final Validation

## Phase 0 — Clarification & Requirements Gathering
Before writing any code, the agent MUST review the user's request for ambiguity.
If ANY of the following are unclear, ASK the user — do NOT assume:
  - Target database engine (SQLite, PostgreSQL, MySQL)?
  - Authentication method (JWT, session-based, none for MVP)?
  - Deployment target (local only, Docker, cloud)?
  - Any additional tables beyond users and todos?
  - Preferred CSS framework (Tailwind, plain CSS, MUI)?
Only proceed to Phase 1 when all requirements are confirmed.

**Checklist:**
- [ ] Database engine confirmed
- [ ] Auth approach confirmed
- [ ] Deployment scope confirmed
- [ ] Additional entities confirmed or declined
- [ ] CSS/UI approach confirmed

## Phase 1 — Task Planning & Tool Preparation
State every step you will perform in plain language before touching any code. List every tool, library, and runtime you will use.

**Tool Inventory:**
- runtime: Node.js >= 18 LTS
- package_manager: npm (free, open-source)
- backend_framework: Express.js 4.x (free, open-source)
- database: SQLite3 via better-sqlite3 (free, open-source, zero-config) — or PostgreSQL via pg if user confirms
- orm_query_builder: Knex.js (free, open-source) for migrations and queries
- frontend_framework: React 18 via Vite (free, open-source)
- form_validation: React Hook Form + Zod (free, open-source)
- http_client: Axios or native fetch
- testing: Vitest (unit), manual E2E checklist (no paid services)
- linting: ESLint + Prettier (free, open-source)
- api_documentation: Swagger/OpenAPI via swagger-jsdoc + swagger-ui-express (free, open-source)

**Constraints Check:**
- ALL tools above are open-source and free. No paid APIs.
- If the user requests a paid integration (e.g., Stripe, AWS managed services), respond: 'It is beyond my limit for this skill, but here is a solution path for future implementation:' and provide a brief architecture note.

**Detailed Task Plan:**
1. Initialize monorepo or two-folder structure (server/ and client/).
2. Set up Express server with error-handling middleware.
3. Design and run DB migrations for users and todos tables.
4. Implement CRUD API routes with input validation.
5. Scaffold React app with Vite.
6. Build form components with React Hook Form + Zod validation.
7. Connect frontend to backend via Axios.
8. Seed database with three test records.
9. Write manual E2E test steps.
10. Run full validation: lint, build, start, and smoke-test.

**Checklist:**
- [ ] All tools listed and confirmed open-source
- [ ] Step-by-step plan written
- [ ] User has approved the plan (or no objections)

## Phase 2 — Database Schema Design
Generate the DB schema FIRST, before any API or frontend code.

**Schema:**
- `users` table: id (INTEGER PRIMARY KEY AUTOINCREMENT), username (VARCHAR(50) NOT NULL UNIQUE), email (VARCHAR(100) NOT NULL UNIQUE), password_hash (VARCHAR(255) NOT NULL), created_at (DATETIME DEFAULT CURRENT_TIMESTAMP), updated_at (DATETIME DEFAULT CURRENT_TIMESTAMP)
- `todos` table: id (INTEGER PRIMARY KEY AUTOINCREMENT), user_id (INTEGER NOT NULL), title (VARCHAR(200) NOT NULL), description (TEXT), status (VARCHAR(20) DEFAULT 'pending'), due_date (DATE), created_at (DATETIME DEFAULT CURRENT_TIMESTAMP), updated_at (DATETIME DEFAULT CURRENT_TIMESTAMP)
  - Foreign Keys: FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE

**Migration Script Path:** scripts/setup-project.sh includes knex migrate:latest
**Validation:** After generating the schema, run the migration and confirm both tables exist by querying sqlite_master or information_schema.

**Checklist:**
- [ ] users table migration written
- [ ] todos table migration written
- [ ] Foreign key constraint confirmed
- [ ] Migration executed successfully
- [ ] Tables verified in database

## Phase 3 — API Route Design & File Structure

**API Routes:**
- `POST /api/auth/register`: Register a new user. Validates username, email, password.
- `POST /api/auth/login`: Authenticate user, return JWT token.
- `GET /api/todos`: List all todos for the authenticated user.
- `POST /api/todos`: Create a new todo.
- `PUT /api/todos/:id`: Update an existing todo (title, description, status, due_date).
- `DELETE /api/todos/:id`: Delete a todo.

**File Structure:**
```
enterprise-todo-app/
  server/
    package.json
    index.js                  // Entry point: Express app setup, middleware, error handler
    knexfile.js               // Knex configuration (DB connection)
    db/migrations/            // Knex migration files
    db/seeds/                 // Seed files for test data
    routes/auth.js            // /api/auth/* routes
    routes/todos.js           // /api/todos/* routes
    middleware/authenticate.js // JWT verification middleware
    middleware/errorHandler.js // Centralized error handler — user-friendly messages
    validators/authValidator.js   // Zod schemas for auth input
    validators/todoValidator.js   // Zod schemas for todo input
    utils/logger.js           // Simple console logger with timestamps
  client/
    package.json
    vite.config.js
    index.html
    src/main.jsx              // React entry point
    src/App.jsx               // Router setup
    src/pages/LoginPage.jsx   // Login form with validation
    src/pages/RegisterPage.jsx// Registration form with validation
    src/pages/TodoListPage.jsx// Main todo CRUD view
    src/components/TodoForm.jsx    // Add/Edit todo form (React Hook Form + Zod)
    src/components/TodoItem.jsx    // Single todo card/row
    src/components/ErrorMessage.jsx // Reusable user-friendly error display
    src/hooks/useAuth.js       // Custom hook for auth state & token
    src/hooks/useTodos.js      // Custom hook for todo CRUD operations
    src/api/client.js          // Axios instance with interceptors
    src/utils/validators.js    // Zod schemas shared with forms
```

**Checklist:**
- [ ] All 6 API routes documented with request/response shapes
- [ ] File structure created on disk
- [ ] Each file has a clear single responsibility

## Phase 4 — Backend Implementation
* Implement each file listed in Phase 3's server/ structure.
* EVERY function and middleware MUST have a JSDoc comment explaining what it does.
* ALL error responses MUST return user-friendly messages (never raw stack traces).
* Use try/catch in every route handler; pass errors to errorHandler middleware.
* Validate ALL inputs using Zod before any database operation.
* Hash passwords with bcryptjs (free, open-source) — NEVER store plaintext.
* Sign JWTs with jsonwebtoken (free, open-source) using an env variable secret.

**Error Handling Pattern:** Centralized error handler in server/middleware/errorHandler.js. Example comment: `// errorHandler.js — Catches all errors passed via next(err). Returns { error: 'user-friendly message' } with appropriate HTTP status. Logs full error internally.`

**Validation:**
* After implementing, run: `node server/index.js`
* Confirm server starts without errors on port 3001.
* Test one route with curl or a script to verify DB connectivity.

**Checklist:**
- [ ] All route files implemented and commented
- [ ] Input validation with Zod on every POST/PUT route
- [ ] JWT auth middleware working
- [ ] Error handler returns user-friendly messages
- [ ] Server starts and listens successfully

## Phase 5 — Frontend Implementation (React + Hooks)
* Scaffold with: `npm create vite@latest client -- --template react`
* Use React 18 functional components and Hooks ONLY (no class components).
* Use React Hook Form for all forms.
* Use Zod for validation schemas; connect to React Hook Form via @hookform/resolvers/zod.
* Display validation errors inline next to each field — user-friendly wording.
* Use the custom hooks (useAuth, useTodos) to encapsulate API calls and state.
* ALL components must have a comment block at the top explaining their purpose.

**Form Validation Requirements:**
* Register Form: username (Required, 3-50 chars, alphanumeric + hyphens only), email (Required, valid email format), password (Required, minimum 8 chars, at least one uppercase, one number)
* Login Form: email (Required, valid email format), password (Required, not empty)
* Todo Form: title (Required, 1-200 chars), description (Optional, max 1000 chars), due_date (Optional, must be today or future date if provided), status (Must be one of: pending, in_progress, completed)

**Validation Steps:**
* Run: `cd client && npm run build` — must complete with zero errors.
* Run: `npm run dev` — open browser, confirm pages render.

**Checklist:**
- [ ] All pages and components created and commented
- [ ] React Hook Form + Zod wired on all forms
- [ ] Inline validation errors display correctly
- [ ] useAuth hook manages login/logout/token
- [ ] useTodos hook manages CRUD state
- [ ] Client builds with zero errors

## Phase 6 — Test Data, Manual E2E Testing & Final Validation

**Test Data:**
1. alice_dev (alice@example.com / Secure1Pass): Has 2 todos (1 pending, 1 in progress).
2. bob_tester (bob@example.com / Testing2Day): Has 1 completed todo.
3. charlie_new (charlie@example.com / NewUser3Here): Has 0 todos.

**Seed Script:** `server/db/seeds/01_test_data.js` — Knex seed file that inserts the three users (with hashed passwords) and their todos. Run via: `npx knex seed:run`

**Manual E2E Test Steps:**
1. Start the backend server (`cd server && npm start`). Expected: Console shows: 'Server running on port 3001'
2. Start the frontend dev server (`cd client && npm run dev`). Expected: Console shows Vite dev server URL
3. Open browser and navigate to the Register page. Expected: Registration form renders with username, email, password fields
4. Submit the register form with EMPTY fields. Expected: Inline validation errors appear
5. Submit the register form with invalid data. Expected: Inline errors
6. Register with valid data. Expected: Success message or redirect to login page. No errors.
7. Log in with the newly created account. Expected: Redirected to the Todo List page. Page shows empty todo list.
8. Create a new todo. Expected: Todo appears in the list with status 'pending'
9. Edit the todo. Expected: Todo updates in the list
10. Delete the todo. Expected: Todo is removed from the list. Confirmation message displayed.
11. Log out and try to access /api/todos directly in browser. Expected: Returns 401 Unauthorized
12. Run the seed script and log in as alice_dev (`cd server && npx knex seed:run`). Expected: Alice's two todos appear in the list. Bob's and Charlie's data are NOT visible.

**Final Validation:**
Before delivering ANY output, the agent MUST run these checks:
1. `cd server && npm install && npx knex migrate:latest && npm start` — server starts without errors
2. `cd client && npm install && npm run build` — zero build errors
3. `cd client && npm run dev` — frontend loads in browser
4. Execute at least steps 3, 6, 7, 8 from the E2E test manually or via script
5. Verify all error messages are user-friendly (no raw stack traces)

**Checklist:**
- [ ] Three test data sets defined and documented
- [ ] Seed script created and runs successfully
- [ ] All 12 E2E steps documented
- [ ] Final validation checks all pass
- [ ] All code is commented
- [ ] All error messages are user-friendly

## Constraints — Enforced at Every Phase
- **C1**: Use ONLY open-source and free components. No paid APIs. (Enforcement: Before adding any dependency, verify it is MIT/Apache/BSD licensed and free.)
- **C2**: If a request exceeds capability, say: 'It is beyond my limit' and provide a future solution path. (Enforcement: Do not fabricate capabilities.)
- **C3**: Always check and run before output. Input and Output format must be correct and runnable. (Enforcement: Execute the final validation checks in Phase 6.)
- **C4**: Errors must display user-friendly messages. All actions must be commented. (Enforcement: Grep all response objects for raw error forwarding. Every function must have a comment.)
- **C5**: If anything is unclear, ASK — do not assume. (Enforcement: Phase 0 is mandatory.)

## Handling "Beyond My Limit" Scenarios
When the user requests functionality that cannot be implemented within this skill's scope, respond with this template:
---
'It is beyond my limit to implement [FEATURE] within this skill. However, here is a recommended solution path for future implementation:'

'**Architecture:** [Brief description of how it would work]'
'**Key Libraries/Services:** [List open-source options if available]'
'**Implementation Estimate:** [Rough scope: small/medium/large]'
'**Reference:** [Link to documentation or tutorial if available]'
---

## Resources
- `scripts/setup-project.sh` — Automates: mkdir, npm init, install dependencies, run migrations
- `scripts/seed-db.sh` — Runs knex seed:run to populate test data
- `scripts/validate-output.sh` — Runs lint, build, and start checks; exits with error if any fail
- `examples/sample-schema.sql` — Raw SQL version of the schema for reference
- `examples/sample-api-routes.md` — Markdown table of all routes for documentation
- `examples/sample-test-data.json` — The three test data objects in JSON format
- `resources/file-structure-template.md` — Copy-pasteable tree view of the project
- `resources/e2e-test-steps-template.md` — Formatted checklist version of the E2E steps
