-- Reference data for the tests and for local runs. Replaces the earlier
-- nomination seeds, which were per gas day.

INSERT INTO contract_parameter (
    id, delivery_point_id, valid_from, valid_to,
    daily_nomination, deviation_threshold, accumulated_deviation_threshold
) VALUES
    ('cccccccc-0000-0000-0000-000000000001', 'aaaaaaaa-0000-0000-0000-000000000001',
     '2026-01-01T00:00:00+00', NULL, 30000.000, 5.00, 2.00),
    ('cccccccc-0000-0000-0000-000000000002', 'aaaaaaaa-0000-0000-0000-000000000002',
     '2026-01-01T00:00:00+00', NULL, 22000.000, 3.00, 2.00)
ON CONFLICT DO NOTHING;
