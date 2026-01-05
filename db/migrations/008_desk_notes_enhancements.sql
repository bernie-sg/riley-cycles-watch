-- Migration 006: Desk Notes Enhancements
-- Adds analysis field for long-form journal entries
-- Adds bullets_formatted field for rich text (HTML/Markdown)

-- Add analysis field for long-form trading journal
ALTER TABLE desk_notes ADD COLUMN analysis TEXT;

-- Add formatted bullets field for rich text editing
-- This allows Notion-style formatting while maintaining backwards compatibility with bullets_json
ALTER TABLE desk_notes ADD COLUMN bullets_formatted TEXT;
