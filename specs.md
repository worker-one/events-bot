# Event Registration Bot — Development Specification

## Goal

Adapt the existing codebase to create a bot that assists users with event registration.

---

## Data Models

- **users**:  
  _No changes required._

- **events**:  
  Stores events available for user sign-up.  
  Fields:
  - `id`
  - `name`
  - `description`
  - `qtickets_link`

- **users_events**:  
  Association table to track user attendance history.

---

## Bot Functionality

### Main Menu (`/menu` command)

Presents two options:
- **Events list**
- **Contact**

---

### Events List

- When "Events list" is selected, display a button for each event from the `events` table.
- When a user clicks an event button, reply with the corresponding `qtickets_link` for that event.

---

### Contact

- When "Contact" is selected, prompt the user to enter a message.
- The entered message should be sent to all users with the `admin` role, using the template:  
  `"Feedback text from {username}: {text}"`

---

## Implementation Rules

- **Respect existing patterns:**  
  Review `README.md` to understand the project structure and conventions.
- **New files:**  
  You may create new files if necessary.
- **Unit tests:**  
  Unit tests are optional and may be skipped.
- **Localization:**  
  All user-facing strings must be placed in a config file, supporting both Russian and English.

---