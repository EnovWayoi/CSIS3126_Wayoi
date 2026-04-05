# Weekly Progress Log
## Interactive Quiz Show Platform

**Student:** Enov Wayoi 
**Course:** CSIS3126 - Design Project I  
**Instructor:** Professor Jeffrey Tagen

---

## Week 1

### Work Completed
- ✅ Project proposal created and submitted
- ✅ GitHub repository created and shared with professor (username: jtagen)
- ✅ Initial README.md created
- ✅ Technology stack selected (Python/Flask/MySQL)
- ✅ Project idea finalized: Interactive Quiz Show Platform

### Progress Summary
Created initial project structure and decided on Interactive Quiz Show Platform as the project topic. Selected technology stack after comparing Python/Flask vs PHP options. Set up GitHub repository for version control and collaboration.

### Impediments/Challenges
- Initially considered file sharing app but switched to quiz platform for better demonstration value
- Needed to compare XAMPP vs standalone MySQL
- Learning Git basics for version control

### Changes to Plan
- Switched project idea from file sharing to Interactive Quiz Show Platform
- Decided to focus on web-only platform instead of native mobile apps

### Next Week Goals
- Complete Software Requirements Specification (SRS)
- Create Entity Relationship Diagram (ERD)
- Begin database design documentation
- Set up development environment

---

## Week 2

### Work Completed
- ✅ Software Requirements Specification document completed
- ✅ All functional requirements documented
- ✅ Non-functional requirements specified
- ✅ Use cases and user stories documented
- ✅ System requirements defined

### Progress Summary
Documented comprehensive software requirements including all features, user roles, system constraints, and success criteria. SRS now serves as blueprint for entire project development.

### Impediments/Challenges
- Understanding IEEE SRS format and standards
- Defining clear acceptance criteria for each requirement
- Estimating realistic scope for 16-week timeline
- Balancing feature richness with achievability

### Changes to Plan
- Removed social features based on professor recommendation to keep scope manageable

### Next Week Goals
- Design complete database schema
- Create Entity Relationship Diagram
- Normalize database to 3NF
- Document all table relationships

---

## Week 3

### Work Completed
- ✅ Entity Relationship Diagram (ERD) created
- ✅ Database schema designed with 6 tables
- ✅ All table relationships documented
- ✅ Foreign key constraints defined
- ✅ Database normalized to Third Normal Form (3NF)
- ✅ SQL schema file created (database_schema.sql)
- ✅ MySQL installed and configured
- ✅ Database implemented - all tables created successfully
- ✅ Sample data inserted for testing

### Progress Summary
Completed full database design and implementation. All tables created with proper relationships, constraints, and indexes. Database successfully tested with sample data.

### Impediments/Challenges
- MySQL installation issues - XAMPP had port conflicts
- Learning SQL foreign key syntax and CASCADE delete behavior
- Understanding proper database normalization rules
- Deciding on ENUM vs separate lookup tables for status fields

### Changes to Plan
- Used standalone MySQL instead of XAMPP due to technical issues

### Next Week Goals
- Set up Flask application structure
- Create basic routing and templates
- Establish database connection from Flask
- Test database connectivity

---

## Week 4

### Work Completed
- ✅ Flask application scaffold created
- ✅ Project structure organized (app.py, templates/, static/, docs/)
- ✅ Database connection established using mysql-connector-python
- ✅ Configuration file created (config.py)
- ✅ Basic routing implemented
- ✅ Database connectivity tested successfully
- ✅ All Flask dependencies installed
- ✅ All documentation uploaded to GitHub
- ✅ Software Design Document created
- ✅ Test Plan documented

### Progress Summary
Set up complete Flask application foundation with verified database connectivity. Created organized project structure following best practices. All core documentation completed.

### Impediments/Challenges
- Learning Flask application structure and routing
- Configuring database connection with proper error handling
- Understanding PyCharm workflow
- Managing configuration files (keeping passwords out of Git)

### Changes to Plan
- Added comprehensive documentation after professor feedback

### Next Week Goals
- Implement user registration functionality
- Implement user login functionality
- Create registration and login HTML templates
- Implement password hashing
- Set up Flask-Login for session management

---

## Week 5

### Work Completed
- ✅ User authentication module fully implemented
- ✅ Registration page with form validation
- ✅ Login page with authentication
- ✅ Password hashing using Werkzeug
- ✅ Flask-Login integration for session management
- ✅ User class created with UserMixin
- ✅ Dashboard page created
- ✅ Base template created with Bootstrap 5 navigation
- ✅ Landing page designed
- ✅ Logout functionality implemented
- ✅ Protected routes using @login_required decorator
- ✅ Flash messages for user feedback
- ✅ Custom CSS styling added
- ✅ Database schema refactored and documented (`docs/database_schema.md`)
- ✅ Entity Relationship Diagram (ERD) generated and consolidated (`docs/Database_Design.md`)

### Progress Summary
Successfully implemented complete user authentication system. Users can register new accounts, log in securely with hashed passwords, access personalized dashboard, and log out. All templates use Bootstrap 5 for responsive design. Additionally, formalized database documentation with a comprehensive design document and updated schema.

### Impediments/Challenges
- Learning Flask-Login library and UserMixin class
- Understanding Jinja2 templating syntax
- Implementing proper password hashing and verification
- Managing user sessions across requests
- Bootstrap CSS framework learning curve

### Changes to Plan
None

### Next Week Goals
- Implement quiz creation functionality
- Build quiz creation form with question management
- Support multiple question types
- Create quiz editing functionality
- Implement quiz deletion

---

## Week 6

### Work Completed
- ✅ Quiz creation module implemented
- ✅ Quiz creation form with title, description, and public/private toggle
- ✅ Question management interface (add, edit, delete questions)
- ✅ Multiple choice question support (4 options A–D)
- ✅ True/false question support
- ✅ Fill-in-the-blank question support
- ✅ Quiz editing functionality (update title, description, visibility)
- ✅ Quiz deletion with confirmation modal
- ✅ Question addition with auto-incrementing order
- ✅ Question editing with pre-populated form
- ✅ Question deletion with confirmation modal
- ✅ Dashboard updated to display quiz list with working links
- ✅ Quiz view page (read-only display of quiz and questions)
- ✅ Ownership verification on all quiz/question routes
- ✅ Dynamic form JavaScript for question type toggling

### Progress Summary
Implemented complete quiz creation and management system. Users can create quizzes, add questions of three different types (multiple choice, true/false, fill-in-the-blank), edit and delete both quizzes and individual questions. All routes are protected with login requirement and quiz ownership verification. Dashboard now shows quiz cards with question counts, public/private badges, and functional Edit/View/Delete buttons with Bootstrap confirmation modals.

### Impediments/Challenges
- JavaScript toggling for different question types required careful handling of form field names to ensure correct data submission
- Managing multiple correct answer input fields (select vs text input) across question types
- Bootstrap modal integration for delete confirmations on dynamically generated content

### Changes to Plan
None

### Next Week Goals
- Checkpoint 1: Demonstration of requirements
- Comprehensive testing of authentication system
- Comprehensive testing of quiz creation/management
- Bug fixes and UI/UX improvements
- Create demo quizzes for presentation


---

## Week 7

### Work Completed
- ✅ Checkpoint 1: Demonstration of requirements
- ✅ Comprehensive testing of authentication system
- ✅ Comprehensive testing of quiz creation/management
- ✅ Bug fixes
- ✅ Created demo quizzes for presentation
- ✅ UI/UX improvements
- ✅ Error handling improvements
- ✅ Documentation updates

### Progress Summary
Successfully demonstrated project requirements for Checkpoint 1. Conducted comprehensive testing across the authentication and quiz management systems to ensure stability. Addressed identified bugs and implemented UI/UX and error handling improvements for a smoother user experience. Created demo quizzes to effectively showcase the platform's features during the presentation, and updated all relevant documentation.

### Impediments/Challenges
- Thoroughly testing all edge cases for authentication and quiz management
- Standardizing the UI/UX design across different views
- Ensuring clear and user-friendly error messages

### Changes to Plan
- Added advanced features (Flashcards and AI-Assisted Quiz Generation) to the project roadmap for Weeks 13 and 14 to enhance the interactive experience.

### Next Week Goals
- Implement game session module (session code generation, session creation)
- Build host game control screen and player lobby
- Implement basic game state management
- Track session participants

---

## Week 8

### Work Completed
- ✅ Link Sharing & Access: Generate shareable links for public quizzes
- ✅ Allow anonymous users to view public quizzes via link
- ✅ Solo Mode: Allow creators to test their own quizzes before hosting a live game
- ✅ Enhanced Solo Mode end screen with cumulative score and performance feedback
- ✅ Game session module basic setup
- ✅ Session code generation logic
- ✅ Game session creation database schema and logic
- ✅ Session validation
- ✅ Join game form for players (Quick join, no account required)
- ✅ UI Overhaul: Applied a vibrant 'Neo-Brutalism' aesthetic across the entire platform using Tailwind CSS

### Progress Summary
Successfully implemented “Link Sharing” allowing anonymous access to public quizzes. Developed a fully functional JavaScript-based "Solo Mode" so users can practice quizzes independently. Completely redesigned the website interface by transitioning from standard Bootstrap to a highly stylized and vibrant Neo-Brutalism aesthetic using Tailwind CSS. Finally, established the foundational backend routes and database schema updates (`game_sessions`, `game_participants`) required for the upcoming live game sessions, including lobby stubs and a session code generator.

### Impediments/Challenges
- Synchronizing the frontend timer and proportional scoring logic in Javascript for Solo Mode.
- Redesigning the database to correctly utilize a `game_participants` table that accommodates anonymous joins via nicknames, replacing the old `session_participants` table which required account logins.

### Changes to Plan
- Replaced the `session_participants` table with `game_participants` to ensure users do not need an account to join a hosted live game.

### Next Week Goals
- Install and configure Flask-SocketIO.
- Establish WebSocket connections for real-time game state management.
- Complete the Host Game Control Screen and Player Lobby interfaces.
- Plan and begin implementing in-app context help and documentation (Course Requirement).

---

## Week 9

### Work Completed
- ✅ Flask-SocketIO installed and configured
- ✅ WebSocket connection established and error handling added
- ✅ Host game control screen interface (Implement WebSockets)
- ✅ Player lobby (Implement WebSockets)
- ✅ Session participants tracking and real-time player list updates
- ✅ In-app context help and documentation added (Course Requirement)
- ✅ Prevented hosting/playing quizzes with 0 questions (Bug Fix)
- ✅ Implemented real-time redirection for players when host cancels session
- ✅ Optimized Solo Mode for perfectly centered, scroll-free mobile layout
- ✅ Fixed layout overflow for long titles and answer options
- ✅ Implemented responsive mobile Navigation menu (Hamburger Toggle) to resolve layout breaks on small screens (Bug Fix)

### Progress Summary
Successfully integrated Flask-SocketIO to enable real-time WebSocket communication for live game staging. The Host Game Control Screen and Player Lobby now dynamically update as participants join, utilizing a `join_room_event` to seamlessly group users by session code. Additionally, a comprehensive in-app context help modal was integrated into the main navigation bar to meet the course's user documentation requirement, offering quick guides on creating, hosting, and joining quizzes. Finally, resolved critical mobile responsiveness issues on the master layout template by implementing a Tailwind-powered hamburger navigation menu.

### Impediments/Challenges
- Restructuring the participant fetching logic to effectively capture anonymous nicknames across various events.
- Ensuring robust room management via SocketIO so that events are broadcast exclusively to the correct game session.
- Debugging flexbox layout inconsistencies across different mobile viewports to ensure standard navigation links correctly collapse into a functional hamburger menu toggled by JavaScript.

### Changes to Plan
None.

### Next Week Goals
- Implement question display for players with a time countdown.
- Build answer submission functionality and response validation logic.
- Develop a time-based proportional scoring system.
- Provide host controls to advance all players to the next question synchronously.

---

## Week 10

### Work Completed
- ✅ Question display for players with time countdown
- ✅ Answer submission functionality and validation logic
- ✅ Auto-end round early if all players submit answers
- ✅ Time-based proportional scoring system implementation
- ✅ Points calculation: `⌊(1 - (({response time} / {question timer}) / 2)) * {points possible}⌉`
- ✅ Host toggle for optional streak bonus
- ✅ Answer streak tracking and reset on incorrect
- ✅ Streak bonus points calculation (+100 pts per streak level, caps at +500 pts)
- ✅ Player scores and streaks updated in database
- ✅ Host controls to advance all players to the next question

### Progress Summary
Implemented the complete live game play flow. The host lobby now features a "Streak Bonus" toggle and a wired "Start Game" button that transitions the session to active via WebSocket. Two new templates were created: `host_game.html` (host control screen with question display, answer count tracking, timer, and Next Question button) and `player_game.html` (player game screen with interactive answer cards, countdown timer, real-time scoring feedback, streak display, and game over summary). All scoring uses a server-side time-based proportional formula with optional streak bonuses. When all players answer, the round auto-ends early. The `game_participants` table was updated with a `streak` column to persist answer streaks across questions.

### Impediments/Challenges
- Coordinating server-side timestamps with client-side countdown timers for accurate proportional scoring required careful design to prevent cheating via client manipulation.
- Managing in-memory game state (`active_games` dictionary) alongside database persistence needed attention to avoid race conditions when multiple players submit answers simultaneously.
- Ensuring smooth view transitions on the player game screen (waiting → question → feedback → between rounds → game over) required careful state management in JavaScript.

### Changes to Plan
- Added `streak` column to `game_participants` table to support answer streak tracking.
- Created an in-memory `active_games` dictionary for tracking question start times and answer counts, since these are transient values that don't need database persistence.

### Next Week Goals
- Build real-time leaderboard view
- Implement answer distribution bar chart for host
- Add player feedback with current rank and gap comparison messages
- Create final results podium/screen
- Implement game end notification broadcast

---

## Week 11

### Work Completed
- ✅ Real-time leaderboard view created
- ✅ Host screen: Answer distribution bar chart reveal
- ✅ Leaderboard updates triggered by answer submissions
- ✅ Player feedback: Current rank and gap comparison messages
- ✅ Final results podium/screen

### Progress Summary
Successfully implemented real-time leaderboard and answer distribution features. The host screen now displays a dynamic bar chart showing the distribution of player answers when the round ends, followed by a dedicated leaderboard scoreboard between rounds. The player screen was enhanced to provide personalized feedback during the game, calculating and displaying the player's current rank and point gap to the person ahead of them. A final results podium was added to both the host and player screens to highlight the top 3 players at the end of the game alongside the final scores.

### Impediments/Challenges
- Synchronizing leaderboard UI transitions efficiently and avoiding overlapping SocketIO events required adding specific transition states (like `roundOver`) and managing `setTimeout` delays between the answer reveal and the leaderboard view.
- Ensuring the answer distribution chart updates dynamically using reliable percentage calculations while matching the Neo-Brutalism CSS framework.

### Changes to Plan
- Integrated the Leaderboard view directly into the Host screen as an intermediate step between questions to mirror an authentic quiz show flow.

### Next Week Goals
- Implement independent study Flashcards view
- AI-Assisted quiz generation from topic/notes
- Add tutorial for first-time users
- Improve modularity and responsive designs

---

## Week 12

### Work Completed
- ✅ Advanced Feature: Independent study Flashcards view
- ✅ Advanced Feature: AI-Assisted quiz generation from topic/notes
- ✅ Advanced Feature: AI-Assisted quiz generation from uploaded documents (PDF, TXT)
- ✅ Tutorial for first-time users
- ✅ Mobile responsiveness improved
- ✅ Accessibility improvements

### Progress Summary
Successfully implemented the final set of advanced features and polish for the platform. Added a dedicated "Flashcards" study mode that allows users to independently review quizzes with interactive, 3D-flipping cards and keyboard navigation. Enhanced the AI generation tool to natively support document uploads (PDF, TXT) via the Gemini Files API, allowing instantaneous quiz creation directly from course materials without manual formatting. Implemented a first-time user tutorial by dynamically displaying the global Help modal upon a user's first visit to the dashboard, smartly tracked via local storage to avoid redundant pop-ups. Conducted a sweep of mobile responsiveness, ensuring all navigation and action buttons nicely wrap and scale on small screens. Improved accessibility by adding ARIA labels, focus states, and keyboard event listeners for all interactive components.

### Impediments/Challenges
- Handling the 3D CSS transform for the flashcards across different browsers and ensuring the content behind the card remained hidden until flipped.
- securely processing multi-part form data uploads for documents and integrating them seamlessly with the Google GenAI Files API without introducing server storage leaks.
- Deciding on a non-intrusive way to present the first-time tutorial without modifying the user database schema, successfully resolving it through browser local storage.

### Changes to Plan
- Avoided duplicating tutorial content by leveraging the existing Help Modal as the first-time user tutorial, automatically populating it with the latest feature guides (Flashcards and AI Generation) and showing it for new users.

### Next Week Goals
- Checkpoint 2: Demonstration of testing
- Conduct extensive unit testing for game session logic
- Perform manual integration testing with concurrent players

---

## Week 13

### Work Completed
- ✅ Write unit tests for game session logic
- ✅ Perform integration testing for WebSockets and live functionality
- ✅ Conduct manual testing with concurrent players across browsers
- ✅ Test AI quiz generation edge cases
- ✅ Checkpoint 2: Demonstration of testing

### Progress Summary
Successfully implemented comprehensive automated test coverage for the platform using Python's `unittest` framework. Created isolated testing modules to independently verify the core functionalities: `test_game_sessions.py` guarantees the validity of REST API routes managing game lobbies and participant connections, `test_websockets.py` verifies the real-time bidirectional Socket.IO events (like answering, tracking streaks, and synchronization), and `test_ai_generation.py` ensures the application safely handles Gemini API faults and invalid file uploads. Additionally, all components were confirmed stable through manual concurrent browsers testing, passing the Checkpoint 2 milestone successfully.

### Impediments/Challenges
- Simulating a multi-user WebSocket environment within an isolated testing framework required managing the `socketio.test_client` concurrently within `setUp` to persist connections across requests.
- Writing robust AI tests required accurately mocking the `google.genai` SDK objects to safely simulate generation success and failure conditions without making live API calls.

### Changes to Plan
None.

### Next Week Goals
- Polish visual design (animations, button states, loading spinners)
- Add missing code comments and docstrings for presentation defense
- Clean up dead code and organize project files

---

## Week 14

### Work Completed
- [ ] Polish visual design (animations, button states, loading spinners)
- [ ] Add missing code comments and docstrings for presentation defense
- [ ] Resolve any remaining bugs identified during Checkpoint 2
- [ ] Clean up dead code and organize project files

### Progress Summary
[To be filled in]

### Impediments/Challenges
[To be filled in]

### Changes to Plan
[To be filled in]

### Next Week Goals
[To be filled in]

---

## Week 15

### Work Completed
- [ ] Finalize `README.md` and installation instructions
- [ ] Ensure all Weekly Progress Logs are up-to-date
- [ ] Clean up and organize GitHub repository
- [ ] Create presentation slides for final defense
- [ ] Rehearse live demo and record backup video

### Progress Summary
[To be filled in]

### Impediments/Challenges
[To be filled in]

### Changes to Plan
[To be filled in]

### Next Week Goals
- Week 16: Final Presentation

---

