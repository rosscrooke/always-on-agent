# Meetings Mock Data

This directory contains synthetic calendar data that mirrors the realism and structure style used in issues, deploys, and contracts.

## Files

- people.json: Person records for meeting participants.
- calendar.json: Meeting records with purpose-aligned titles and participant references.
- preview.json: Smaller review sample used during initial design.

## Schema

### Person

Required fields:
- person_id: unique stable identifier.
- name: display name.
- title: job title.
- bio: short role-relevant biography.

Optional fields used in this dataset:
- team
- timezone

### Meeting

Required fields:
- meeting_id: unique stable identifier.
- start_time: ISO 8601 timestamp.
- end_time: ISO 8601 timestamp.
- title: purpose-specific meeting title.
- purpose: one of the approved purpose categories.
- participants: array of person_id values.
- organizer: person_id value.

Optional fields used in this dataset:
- meeting_link
- location
- related_context

## Purpose Categories

- Incident response
- Root cause analysis
- Release planning
- Customer escalation
- Cross-team dependency alignment
- Contract/compliance review

## Title Rule

Meeting titles should describe the intended outcome of the session and include operational context. Avoid generic titles such as "sync" or "catch-up".
