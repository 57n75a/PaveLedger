## 2.1.0 - 2026-09-27
- Added a global search bar in the top header covering investigations, contracts, and evidence
- Added a "My profile" dialog: edit display name and change password (email locked)
- Added a 24-hour session timeout for all roles except Vehicle, which never expires
- Added a Notification preferences dialog under Notifications
- Team lead and Director can now see and edit any member's access from the Teams & access page (except granting/modifying Administrator access)

## 2.0.9 - 2026-09-27
- Added self-service profile name updates (email still locked)
- Added configurable notification preferences: assignment and status-change on by default, manual-edit notifications off by default
- Team lead now gets notified when they personally assign a ticket
- Team lead and Director can now edit any member's access and see all members org-wide, but cannot grant or modify Administrator access

## 2.0.8 - 2026-09-26
- Contractor is now shown as a column on the dashboard and assignable directly from the ticket page (Admin, Team lead)
- Archive/unarchive/request-archive controls moved to the bottom of each investigation
- Priority now shown in the Overview Attention queue
- Fixed the stretched logo image; reporter photos and the logo fallback are now sized correctly
- All four Overview metric cards are now clickable and jump to the matching filtered view
- Added a visible Teams list to the Teams & access page

## 2.0.6 - 2026-09-26
- Added a personal "My tickets" summary to the Overview page, showing status counts for cases you are personally assigned to, reported, or have completed/closed

## 2.0.5 - 2026-09-26
- Archived tickets are now hidden from Overview, Investigations, and Analytics
- Added a dedicated Archive section in the sidebar, visible only to Admin, Team lead, and Director

## 2.0.4 - 2026-09-26
- Added archive as a flag (not a status): tickets are never deleted, only archived
- Admin, Team lead, and Director can archive/unarchive directly from the ticket page
- Analyst and Head Analyst can request archival, which notifies Team lead/Director/Admin
- Note: archived tickets still appear in the main dashboard for now -- hiding them and adding a dedicated Archive view is next

## 2.0.3 - 2026-09-26
- Fixed: creating a non-Vehicle member (e.g. Admin) incorrectly required a vehicleTag field

## 2.0.2 - 2026-09-26
- Added Head Analyst and Director roles
- Added escalation workflow: Head Analyst -> Team lead -> Director, with notifications
- Director has organization-wide read access but does not perform ticket transitions directly

# Changelog

## 2.0.1 - 2026-09-26
- Added dashboard "Updated" timestamp row, editable priority dropdown, and a visible "Reopened xN" flag
- Ticket detail page now shows the reporter's actual first photo, falling back to the PaveLedger logo when none is uploaded yet
- Added automated dashcam detection: Vehicle role, radius-based dedupe, automatic contractor/warranty tagging, automatic least-loaded-analyst assignment
- Footer now shows the app version and a Contact form
