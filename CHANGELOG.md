## 2.8.18 - 2026-10-10
- Pictures: profile photo, team logo, company logo and the main logo accept files up to 2 MB. They are resized in the browser before saving. Previously any picture over about 24 KB was refused by a hidden request limit.
- Tables wrap their text and fit the window, so every column of the Users table is visible at 100% zoom.
- Help and FAQ is now a centered card like the profile page.
- New PaveLedger Srbija logo.

## 2.8.17 - 2026-10-10
- Roles: Team lead is retired, and Head Analyst has all of its permissions. Reviewer is retired, and Auditor has all of its permissions (verify and close repairs, reopen, hold and resume) while still reading every record.
- Existing users, role settings, custom roles, escalation chains and escalated tickets are migrated automatically. The default escalation is Head Analyst, then Director.
- Analysts can be added to more teams (up to three) while they have open tickets. Removing a team that still holds their open tickets, suspending them or changing their role still requires reassigning those tickets first.

## 2.8.16 - 2026-10-10
- New ticket is now a full page with Location (full address, GPS coordinates as in Google Maps, find on map, current position, map preview), Details (issue, priority, observed time, source, team, description) and Photos (up to 10, uploaded as evidence).
- Tickets show their address and Google Maps coordinates with Open in Google Maps and Copy; authorised staff can edit them (recorded in the activity log).
- GPS input accepts decimals, degrees/minutes/seconds, N/S/E/W letters and Google Maps links.
- FAQ updated.

## 2.8.15 - 2026-10-09
- Fix: tickets can be reopened from the Archive. The stage dropdown there now works, and reopening takes the ticket out of the archive.
- Roles: an Admin can delete a custom role that people still hold by moving them to a role with the same base. Built-in roles are unchanged.
- Dark mode now applies to the sidebar and menus.
- User Profile and Users and Roles pages: centered cards, aligned fields and buttons, spaced tabs.

## 2.8.14 - 2026-10-08
- Contractor notice emails (off by default): an Admin can turn on automatic emails sent when a case reaches Notice prepared; staff can email a prepared notice from the case. Needs RESEND_API_KEY and MAIL_FROM.
- At-most-once delivery with up to 3 attempts, an Admin retry button, a record on each case, and a daily retry.
- Admin settings show recent notice emails and failures. Two new FAQ entries.

## 2.8.13 - 2026-10-08
- Help form: sends the message to support from inside the app when RESEND_API_KEY is set (limited to 3 messages per 10 minutes per person). Without the key it opens the email app as before.
- Fix: when someone changes their sign-in email on the User Profile page, their membership email now follows automatically.
- DEPLOYMENT.md documents CRON_SECRET, RESEND_API_KEY, MAIL_FROM and SUPPORT_EMAIL.

## 2.8.12 - 2026-10-07
- New User Profile page (open it from your name at the top right): profile details, status, phone, photo, password, email, notifications, theme, log out. Admin-only Platform settings with Edit branding.
- New Help and FAQ page in the sidebar with search and the support form at the bottom. The Help, FAQ, Settings and Notification popups are gone.
- The user menu now has a single action, User Profile. A user's status is shown in bold.
- FAQ answers updated for the new locations; two new entries.

## 2.8.11 - 2026-10-07
- Users: when adding a user an Admin can create the sign-in with a temporary password (shown once), send an email invitation, or link an existing sign-in.
- Users: Admin can reset another member's password (not their own, not the owner's). Delete now also removes the sign-in account.
- Sign-in screen: invited users and users with a temporary password choose their own password at first sign-in; added a Forgot your password link.
- FAQ: three new entries about adding users, forgotten passwords and removing access.

## 2.8.10 - 2026-10-06
- Escalation chain is now configurable by an Admin (Users and Roles, Roles tab). The default is still Head Analyst, then Team lead, then Director.
- The Escalate button on a ticket follows the chain and respects the role's Escalate tickets permission.
- Escalation notices go to the target role; team-scoped roles are notified only within the ticket's team.

## 2.8.9 - 2026-10-06
- Branding editor moved from the sidebar to the account menu (Platform settings: branding), shown to Admin only. The logo and slogan still display for everyone.

## 2.8.8 - 2026-10-06
- Fix: the contract scope line and the contract import screen showed raw "\u00b7" and "\u2014" text instead of a dot and a dash.

## 2.8.7 - 2026-10-05
- Roles tab: Admin can add, edit and delete custom roles (base role, visibility, allowed actions).
- User form: custom roles appear in the Role dropdown; the Users table shows the custom role name.
- Users: Admin can delete a user. Blocked for yourself, the owner identity, the last active Admin, and anyone who appears in ticket records (suspend them instead).

## 2.8.6 - 2026-10-05
- Street and address lookups are now spaced at least 1.1 seconds apart per server instance, to follow the OpenStreetMap Nominatim usage policy.

## 2.8.5 - 2026-10-05
- Custom roles (backend): Admin can create, edit and delete roles with a base role, a visibility setting (base, own, team, all) and capability checkboxes.
- Memberships can be assigned a custom role; the member keeps the base role for workflow rules.
- Capability checks (create, comment, assign, escalate, archive, contracts) now use the custom role when a member has one.

## 2.8.4 - 2026-10-05
- Fix: map tiles were blocked by OpenStreetMap because no Referer header was sent. Referrer-Policy is now strict-origin-when-cross-origin (only the site origin is sent to other sites).
- Map attribution now links to the OpenStreetMap copyright page, as the tile policy requires.

## 2.8.3 - 2026-10-05
- Account menu now has Settings, Notifications, Theme, Help, FAQ and Logout.
- New FAQ dialog with 22 entries.
- Logout clears stored session state and returns to the start page.
- Tickets with no tagged contractor now read "No contractor" instead of "Unassigned".

## 2.8.2 - 2026-10-05
- Security: only an Admin can modify an existing Vehicle account (previously a Team lead or Director could change or deactivate one by submitting a different role).
- Audit: role-permission and branding changes are now written to the event log.
- Safety: branding and profile-photo updates now respect the 8 MB workspace size limit.

## 2.8.1 - 2026-10-04
- Added "Import contracts" (Admin): upload XLSX/XLS/CSV or XML, map columns to contract fields (auto-guessed), review and select rows, then import. PDF shows a message suggesting conversion to CSV first, since reliable automatic PDF table extraction isn't realistic across arbitrary government formats.

## 2.8.0 - 2026-10-04
- Added bulkImportContracts action: validates each row with the same rules as a single contract, skips invalid rows rather than failing the whole batch, capped at 200 per import

## 2.7.1 - 2026-10-04
- Contract create/edit forms now have a company logo upload and an "additional streets covered" field
- Contract cards display the logo and any additional streets

## 2.7.0 - 2026-10-04
- Contracts can now have a company logo (inline, under 500 KB) and additional streets covered beyond the primary road
- contractCovers now matches a ticket's road against any additional street listed, not just the primary one

## 2.6.3 - 2026-10-04
- Team cards now show the team logo and contact email/phone when set, and the Edit team form lets Admin set all three

## 2.6.2 - 2026-10-04
- Teams can now have a logo, contact email, and phone number, set via Edit team; carried over correctly if the team is renamed, cleaned up if deleted

## 2.6.1 - 2026-10-02
- The topbar now shows the signed-in user's name/photo/status with a dropdown (Edit profile, Sign out) instead of a bare Sign out button
- My profile now includes a status message (with presets: In office, Work from home, On vacation, Out sick, Do not disturb), phone number, profile photo, and self-service email change (sends a confirmation link)

## 2.6.0 - 2026-10-02
- Added self-service status message, phone number, and profile photo (stored inline, under 500 KB) to the self-profile action

## 2.5.2 - 2026-10-02
- Added a light/dark theme toggle in the topbar, persisted per browser
- Admin can edit the sidebar logo and slogan from a new "Edit branding" link

## 2.5.1 - 2026-10-02
- Added editable branding: Admin can replace the sidebar logo (stored inline, under 500 KB) and change the workspace slogan

## 2.5.0 - 2026-10-01
- Added PDF export alongside CSV export on the Tickets dashboard (client-side, no server cost)
- Fixed the CSV export filename (was still PaveLedger_Investigations.csv)

## 2.4.3 - 2026-09-30
- Fixed: edit dialogs (users, contracts) could overflow the screen on desktop with the Save button unreachable; every dialog now scrolls internally instead
- Contract create/edit forms no longer require the scope description; it's now a free-form optional field (e.g. cross-street description) alongside the map radius
- Contract cards now show the contractor's name as the heading, with the road as a subheading
- "Rename team" is now "Edit team"
- The main Tickets dashboard now has a stage-change dropdown per row for straightforward transitions; stages needing extra details (Notice prepared, Duplicate, Verified closed) open the full ticket instead

## 2.4.2 - 2026-09-30
- Fixed: contract scope field was requiring 10+ characters even when a map radius already defined coverage; it's now optional
- Only an Admin can create or modify a Vehicle account (Team lead/Director can still manage other roles)

## 2.4.1 - 2026-09-30
- "Users and Roles" is now two tabs: Users (the member list, renamed from "members" throughout) and Roles (the new live capability matrix)
- Admin can toggle role capabilities directly in the Roles tab; changes save immediately per checkbox

## 2.4.0 - 2026-09-30
- Added a configurable role-capability system: Admin can now toggle, per role, whether it can create tickets, comment, assign, escalate, archive directly, and manage contracts
- A fixed safety floor is not configurable: granting or modifying Administrator access, closing/verifying tickets, and team create/rename/delete remain hard-coded regardless of the capability matrix
- Defaults exactly match prior hard-coded behavior, so nothing changes until an Admin customizes something

## 2.3.2 - 2026-09-29
- Stand-alone comments on a ticket's activity are now restricted to team members and Admin (Contractor can still comment when moving a stage they're permitted to, since that comment is part of the transition itself)
- Renamed the "Roles" section to "Users and Roles"

## 2.3.1 - 2026-09-29
- Every ticket's hero is now a live map centered on its coordinates (Overview and the individual ticket page); reported photos appear as thumbnails below instead
- Evidence photos now show as real clickable thumbnails linking to the full image, instead of a filename-only button
- Manually creating a ticket now looks up latitude/longitude automatically once you finish typing the road
- Contract address country list is now USA, Canada, Serbia, EU

## 2.3.0 - 2026-09-29
- Vehicle re-check: when the original vehicle finds the location clear at least 12 hours later, the ticket moves to pending closure, the assigned team is notified, and it auto-closes and archives after 7 days (daily sweep; any manual stage change or a new detection cancels it)
- New vehicle tickets resolve the street name from the GPS fix; the vehicle no longer has to send it
- Vehicle detections inside an open ticket's 20 m radius are matched by location only
- Contract coverage now uses the scope area when a contract has one, otherwise road name (abbreviation tolerant)
- Address lookup allows Admin, Team lead and Analyst, is country-optional, and biases toward the workspace area
- Added a batch thumbnail-URL endpoint for ticket images
- Added Serbia and EU region codes for address lookup

## 2.2.2 - 2026-09-28
- Contracts can now define a scope area: locate the address on a map, drag the pin, and set a coverage radius (Leaflet + OpenStreetMap, no API key)
- Added a server-side address lookup limited to the selected region (USA, Canada, Europe), Admin only
- Contract cards now show phone, address, and scope area with an Open in Google Maps link

## 2.2.1 - 2026-09-28
- Renamed "Investigations" to "Tickets" everywhere users see it: sidebar, page titles, buttons, dialogs, filters, search, exports, and messages
- Internal code names (types, variables, API fields) are unchanged

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
