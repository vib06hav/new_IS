# WorkOS AuthKit Migration Scope

This migration replaces local email/password authentication with WorkOS AuthKit.

## In scope

- Backend authentication and session bootstrap
- Local invite and access lifecycle for interviewers
- Founder admin bootstrap via WorkOS identity
- Frontend admin and interviewer login entry flows
- Frontend interviewer access-management UI
- Removal of local password and local profile-image management

## Out of scope

- Application upload and processing
- Report synthesis and export
- Assignment semantics and assignment business rules
- Interviewer workspace behavior
- Admin application management outside interviewer access management

## Authorization boundary

- WorkOS is the source of truth for identity, password, MFA, verified email, and provider profile image.
- The application remains the source of truth for local role and access state.
- Existing admin/interviewer authorization checks must continue to run against the local `User` record.
