-- add_archetype_to_experts.sql

ALTER TABLE experts
ADD COLUMN archetype TEXT DEFAULT 'balanced';
