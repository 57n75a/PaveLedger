## 2.2.0 - 2026-09-27
- Add member form now shows team checkboxes (up to 3) instead of a single team dropdown
- Team management, assignment pickers, and Teams page member counts all updated for multi-team membership

## 2.1.9 - 2026-09-27
- Members can now belong to up to 3 teams instead of just one
- Existing single-team members are automatically migrated to the new teams array on next load

## 2.1.8 - 2026-09-27
- Added phone number field to the member form, and phone/address/country fields to contract create and edit forms
- New tickets now default to a live Google Maps embed of the reported location (free, no API key) instead of the logo, until a photo is uploaded

## 2.1.7 - 2026-09-27
- Added phone number field for members and contracts
- Added address and country/region fields for contracts
- Schema prepared for a future interactive scope-radius picker (Leaflet, free/no API key)

## 2.1.6 - 2026-09-27
- Admin can now delete a team directly from the Teams page (blocked if it still has active members or open investigations)
- Admin can now add or remove members from a team directly from the Teams page, without going through Roles

## 2.1.5 - 2026-09-27
- Teams page now reuses the same card styling as Contracts, for visual consistency across the app
- Admin can now rename a team; the rename cascades to every member and ticket assigned to that team

## 2.1.4 - 2026-09-27
- Reformatted the Teams page into a clean card grid (previously plain unstyled text)

## 2.1.3 - 2026-09-27
- Split "Teams & access" into two separate sidebar sections: Teams (team list, create team) and Roles (member table, edit access)

## 2.1.2 - 2026-09-27
- Overview now features a live "top priority case" hero with the real reported photo, instead of a static illustration
- Contractor assignment on a ticket now explains clearly when no matching contract exists for that road
- Contracts can now be edited: update details, add notes, upload documents, and link existing incidents on the same road

## 2.1.1 - 2026-09-27
- Added contractUpdate action: Admin can edit an existing contract's details and notes
- Added contract document storage (reuses the private evidence bucket under a contracts/ path) with a new /api/contract-document endpoint
- Editing a contract can now link existing incidents on the same road directly to it

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
