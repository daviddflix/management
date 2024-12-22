# Data Models and Relationships

## Project Structure

The models are organized in two main folders:

### 1. `models/` (Current Directory)
Contains the business logic layer with Pydantic models and high-level implementations:
- Handles data validation
- Implements business rules
- Manages model relationships
- Provides API interfaces

### 2. `models/database/`
Contains SQLAlchemy ORM definitions that map to database tables:
- Defines database schema
- Handles database relationships
- Manages persistence layer
- Supports database migrations

## Core Models Overview

### User Model (`user.py`)
The central entity representing team members with different roles:
- Links to: Team (member_ids), Tasks (assigned_tasks, completed_tasks), Channels (member_of)
- Tracked by: Metrics (performance, productivity)
- Properties: roles, skills, status, integrations (Monday, Slack)
- Messages: sent_messages, reactions, read_messages

### Team Model (`team.py`)
Represents development teams and their composition:
- Contains: Users (member_ids, tech_lead_id, etc.)
- Manages: Sprints (current_sprint_id), Channels (team_channels)
- Tracked by: Metrics (team_health, performance)
- Properties: type, status, capacity, working hours

### Channel Model (`channel.py`)
Represents communication spaces for teams and direct messaging:
- Types: Public, Private, Direct Messages
- Belongs to: Team (team_id)
- Contains: Messages, Members (with admin roles)
- Properties: visibility, archival status, Slack integration
- Features: Member management, message threading, read tracking

### Message Model (`message.py`)
Represents all forms of communication within channels:
- Belongs to: Channel (channel_id)
- Created by: User (sender_id)
- Features: Threading (parent/replies), Reactions, Attachments
- Tracks: Read status, Edit history
- Integration: Slack message sync

### Task Model (`task.py`)
Represents work items with various types and priorities:
- Belongs to: Team (team_id), Sprint (sprint_id), Board (board_id)
- Assigned to: User (assignee_id)
- Created by: User (creator_id)
- Related to: Other Tasks (dependencies, blocked_by, blocks)
- Tracked by: Metrics (time_spent, quality)

### Sprint Model (`sprint.py`)
Represents time-boxed work periods:
- Belongs to: Team (team_id)
- Contains: Tasks (planned_tasks, completed_tasks)
- Includes: Team Members (team_members)
- Tracked by: Metrics (velocity, completion_rate)
- Properties: goals, retrospective, daily standups

### Metrics Model (`metrics.py`)
Comprehensive tracking of various performance indicators:
- Quality Metrics: code coverage, bug density, etc.
- Performance Metrics: completion rates, cycle times
- Productivity Metrics: velocity, story points
- Team Health Metrics: happiness, stress, collaboration

## Data Flow and Relationships

### Team Management Flow
1. Team Creation:
   - Team is created with type and settings
   - Tech Lead, PO, and Scrum Master are assigned
   - Team members are added
   - Integration IDs (Monday, Slack) are configured
   - Default channels are created

2. Communication Setup:
   - Team channels are created
   - Members are assigned to channels
   - Integration with Slack is configured
   - Channel permissions are set

3. Sprint Planning:
   - New Sprint is created for Team
   - Tasks are created and assigned to Sprint
   - Story points and capacity are calculated
   - Team members are associated with Sprint

4. Task Management:
   - Tasks are created and assigned to Team members
   - Dependencies are established
   - Progress is tracked through status changes
   - Metrics are collected on task completion

5. Metrics Collection:
   - Regular snapshots of team performance
   - Quality metrics from code analysis
   - Productivity metrics from task completion
   - Team health metrics from various sources
   - Communication metrics from channels

## Key Relationships

### User Relationships
```
User
├── Team (belongs_to)
├── Tasks (has_many)
├── Channels (has_many)
├── Messages (has_many)
└── Metrics (tracked_by)
```

### Team Relationships
```
Team
├── Users (has_many)
├── Channels (has_many)
├── Sprints (has_many)
├── Tasks (has_many)
└── Metrics (tracked_by)
```

### Channel Relationships
```
Channel
├── Team (belongs_to)
├── Members (has_many: users)
├── Messages (has_many)
└── Admins (has_many: users)
```

### Message Relationships
```
Message
├── Channel (belongs_to)
├── Sender (belongs_to: user)
├── Parent (belongs_to: message)
├── Replies (has_many: messages)
├── Reactions (has_many)
└── ReadBy (has_many: users)
```

### Sprint Relationships
```
Sprint
├── Team (belongs_to)
├── Tasks (has_many)
└── Metrics (has_one)
```

### Task Relationships
```
Task
├── Team (belongs_to)
├── Sprint (belongs_to)
├── Board (belongs_to)
├── User (belongs_to)
├── Tasks (has_many: dependencies)
└── Metrics (has_one)
```

### Metrics Relationships
```
Metrics
├── Team (belongs_to)
├── Sprint (belongs_to)
├── User (belongs_to)
└── Task (belongs_to)
```

## Data Flow Examples

1. **Task Assignment Flow**:
   ```
   User -> Task -> Sprint -> Team -> Metrics
   ```

2. **Sprint Completion Flow**:
   ```
   Sprint -> Tasks -> Metrics -> Team -> Users
   ```

3. **Performance Tracking Flow**:
   ```
   Tasks -> Metrics -> Team -> Notifications
   ```

4. **Communication Flow**:
   ```
   User -> Message -> Channel -> Team -> Notifications
   ```

5. **Message Threading Flow**:
   ```
   Message -> Replies -> Reactions -> Notifications
   ```

## Integration Points

1. **Monday.com Integration**:
   - Team synchronization
   - Task tracking
   - Sprint management

2. **Slack Integration**:
   - Channel synchronization
   - Message mirroring
   - Notifications
   - Daily updates
   - Team communication

3. **Prometheus Integration**:
   - Performance metrics
   - System monitoring
   - Alert management

## Best Practices

1. **Data Consistency**:
   - Always update related models in transactions
   - Maintain referential integrity
   - Use cascading updates/deletes where appropriate
   - Handle message threading carefully

2. **Performance**:
   - Use efficient queries with proper joins
   - Implement caching for frequently accessed data
   - Batch metrics collection
   - Optimize message queries

3. **Security**:
   - Implement proper access control
   - Validate all relationships
   - Sanitize integration data
   - Protect sensitive messages
   - Manage channel permissions

4. **Communication**:
   - Handle message delivery reliably
   - Maintain read status accurately
   - Process reactions atomically
   - Manage file attachments securely
