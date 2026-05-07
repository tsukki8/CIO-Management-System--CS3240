[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/F1hjDb63)

# CIO Management System

## CS 3240: Software Engineering S26 Group-05
**Spring 2026 | University of Virginia**

---

## Project Theme

**Supporting UVA Student Organizations (CIOs)**

At UVA, many student organizations operate as **Contracted Independent Organizations (CIOs)**. While CIO status provides useful institutional benefits, these organizations are fully student‑run, placing significant operational responsibility on student officers.

This project implements a **CIO Management System** designed to help CIOs manage their **members, communication, events, and engagement** more effectively through a centralized web application.

Our site targets CIO leadership and members by providing robust internal tools for:

- Member management through the roster feature
- Messaging among CIO members
- Document and file storage (S3)
- Event and organizational continuity (event creation, promotion, and rsvp features)
- Centralized calendar for rsvp'd events
- Notifications center for upcoming events and received messages
- User role dashboard swap feature for CIO creators only

---

## Authentication & Roles
- Google Login integration (login method)
- Multiple meaningful user levels:
  - **Member** – standard CIO participants with no additional permissions
  - **CIO creator** – elevated permissions for managing the organization (creating events etc.)
  - **User Administrator** – role management only (super user)

---

## Approved Tech Stack (Course Constraint)

This project strictly follows the required CS 3240 technology stack:

- **Language:** Python 3
- **Framework:** Django
- **Database:** PostgreSQL (production), SQLite (local development)
- **Authentication:** Google OAuth
- **Storage:** Amazon S3 (files and images)
- **Hosting:** Heroku
- **CI/CD:** GitHub Actions
- **Source Control:** GitHub
- **Frontend:** Django Templates

---

## User Manual

1. Tell us anything we need to know about running/using your app (e.g., accounts, tricky feature, etc.):

How to test:
1. Go to this site: https://uva-cio-fe058471845c.herokuapp.com/home/ 
2. Log in as exec_test and create a CIO.
3. In a separate browser (use one regular window and one incognito window), log in as member_test and apply to that CIO.
4. Switch back to exec_test and approve the membership request.
5. Use both accounts in separate sessions to test other features.

Notes: 
Using separate browser sessions is important to properly test interactions between user types.
We recommend testing event creation, event promotion (after setting CIO status to public), messaging, calendar viewing, and checking notifications.
* We highly recommend using the Google Chrome browser to bypass the dangerous site warning popups and for a smoother user experience.

---
