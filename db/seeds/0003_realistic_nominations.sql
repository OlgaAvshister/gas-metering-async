-- Bring planned volumes into proportion with the sample flow rates: a node
-- running at roughly 1250 units per hour delivers about 30000 over a gas day.
UPDATE nomination SET planned_volume = 30000.000
WHERE delivery_point_id = 'aaaaaaaa-0000-0000-0000-000000000001';

UPDATE nomination SET planned_volume = 22000.000
WHERE delivery_point_id = 'aaaaaaaa-0000-0000-0000-000000000002';