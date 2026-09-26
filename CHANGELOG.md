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
